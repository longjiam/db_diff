from typing import Any
from sqlalchemy import text
from .base import BaseDBAdapter


class PostgreSQLAdapter(BaseDBAdapter):
    """PostgreSQL 数据库适配器"""
    
    @property
    def db_type(self) -> str:
        return "postgresql"
    
    def build_connection_string(self, config: dict) -> str:
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        user = config.get("user", "postgres")
        password = config.get("password", "")
        database = config.get("database", "postgres")
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    
    def get_tables(self, conn: Any) -> list[str]:
        result = conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        return [row[0] for row in result.fetchall()]
    
    def get_table_comment(self, conn: Any, table: str) -> str:
        """获取表注释"""
        result = conn.execute(text("""
            SELECT obj_description(c.oid, 'pg_class')
            FROM pg_class c
            WHERE c.relname = :table_name
              AND c.relkind = 'r'
        """), {"table_name": table})
        row = result.fetchone()
        return row[0] if row and row[0] else ""
    
    def get_columns(self, conn: Any, table: str) -> list[dict]:
        result = conn.execute(text("""
            SELECT 
                c.column_name,
                c.data_type,
                c.character_maximum_length,
                c.is_nullable,
                c.column_default,
                c.numeric_precision,
                c.numeric_scale,
                col_description(
                    (SELECT oid FROM pg_class WHERE relname = :table_name),
                    c.ordinal_position
                ) AS column_comment
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
              AND c.table_name = :table_name
            ORDER BY c.ordinal_position
        """), {"table_name": table})
        
        columns = []
        for row in result.fetchall():
            col_type = row[1]  # data_type
            
            # 处理字符类型长度
            if row[2] is not None:
                col_type = f"{row[1]}({row[2]})"
            # PostgreSQL 不需要 numeric 精度（BIGINT, INTEGER 等是固定宽度）
            # 只有 NUMERIC 和 DECIMAL 类型才需要精度参数
            elif row[5] is not None and row[6] is not None:
                if row[1].upper() in ('NUMERIC', 'DECIMAL', 'DEC'):
                    col_type = f"{row[1]}({row[5]},{row[6]})"
                # 其他类型（BIGINT, INTEGER, SMALLINT 等）不需要精度
            
            columns.append({
                "name": row[0],
                "type": col_type.upper(),
                "nullable": row[3] == "YES",
                "default": row[4],
                "is_primary": False,
                "auto_increment": "nextval" in (row[4] or ""),
                "comment": row[7] if len(row) > 7 and row[7] else "",  # 字段注释
            })
        return columns
    
    def get_indexes(self, conn: Any, table: str) -> list[dict]:
        result = conn.execute(text("""
            SELECT 
                i.relname AS index_name,
                ix.indisunique AS is_unique,
                array_to_string(array_agg(a.attname), ',') AS columns
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE t.relname = :table_name
            GROUP BY i.relname, ix.indisunique
        """), {"table_name": table})
        
        indexes = []
        for row in result.fetchall():
            indexes.append({
                "name": row[0],
                "unique": row[1],
                "columns": row[2].split(","),
                "type": "BTREE",
            })
        return indexes
    
    def get_foreign_keys(self, conn: Any, table: str) -> list[dict]:
        result = conn.execute(text("""
            SELECT
                con.conname AS fk_name,
                array_to_string(array_agg(DISTINCT fk_col.attname), ',') AS columns,
                pk_t.relname AS ref_table,
                array_to_string(array_agg(DISTINCT pk_col.attname), ',') AS ref_columns,
                CASE con.confupdtype
                    WHEN 'c' THEN 'CASCADE'
                    WHEN 'n' THEN 'SET NULL'
                    WHEN 'd' THEN 'SET DEFAULT'
                    ELSE 'NO ACTION'
                END AS on_update,
                CASE con.confdeltype
                    WHEN 'c' THEN 'CASCADE'
                    WHEN 'n' THEN 'SET NULL'
                    WHEN 'd' THEN 'SET DEFAULT'
                    ELSE 'NO ACTION'
                END AS on_delete
            FROM pg_constraint con
            JOIN pg_class fk_t ON fk_t.oid = con.conrelid
            JOIN pg_class pk_t ON pk_t.oid = con.confrelid
            JOIN pg_attribute fk_col ON fk_col.attrelid = con.conrelid AND fk_col.attnum = ANY(con.conkey)
            JOIN pg_attribute pk_col ON pk_col.attrelid = con.confrelid AND pk_col.attnum = ANY(con.confkey)
            WHERE con.contype = 'f'
              AND fk_t.relname = :table_name
            GROUP BY con.conname, pk_t.relname, con.confupdtype, con.confdeltype
        """), {"table_name": table})
        
        fks = []
        for row in result.fetchall():
            fks.append({
                "name": row[0],
                "columns": row[1].split(","),
                "ref_table": row[2],
                "ref_columns": row[3].split(","),
                "on_update": row[4],
                "on_delete": row[5],
            })
        return fks
    
    # ========== SQL 生成 ==========
    
    def generate_create_table_sql(self, table: str, columns: list[dict],
                                   indexes: list[dict] = None,
                                   foreign_keys: list[dict] = None,
                                   table_comment: str = "") -> str:
        parts = []
        for col in columns:
            col_def = f"  \"{col['name']}\" {col['type']}"
            if col.get("is_primary"):
                col_def += " PRIMARY KEY"
            elif not col.get("nullable", True):
                col_def += " NOT NULL"
            if col.get("default") is not None and "nextval" not in (col.get("default") or ""):
                default_val = col['default']
                # 处理字符串默认值
                if not default_val.startswith("'") and not default_val.upper() in ('NULL', 'TRUE', 'FALSE', 'CURRENT_TIMESTAMP', 'NOW()'):
                    # 转义单引号，防止 SQL 注入和语法错误
                    escaped_default = default_val.replace("'", "''")
                    default_val = f"'{escaped_default}'"
                col_def += f" DEFAULT {default_val}"
            if col.get("auto_increment"):
                col_def = f"  \"{col['name']}\" SERIAL"
            # PostgreSQL CREATE TABLE 中不能有列内注释（-- comment）
            # 注释必须用 COMMENT ON COLUMN 语句单独添加
            parts.append(col_def)
        
        # 主键
        pk_cols = [c["name"] for c in columns if c.get("is_primary")]
        if pk_cols and not any(c.get("auto_increment") for c in columns):
            parts.append(f"  PRIMARY KEY ({', '.join(f'\"{c}\"' for c in pk_cols)})")
        
        sql = f"CREATE TABLE \"{table}\" (\n{',\n'.join(parts)}\n)"
        if table_comment:
            # 转义单引号，防止 SQL 注入和语法错误
            escaped_table_comment = table_comment.replace("'", "''")
            sql += f";\nCOMMENT ON TABLE \"{table}\" IS '{escaped_table_comment}'"
        
        # 添加字段注释
        for col in columns:
            if col.get("comment"):
                # 转义单引号，防止 SQL 注入和语法错误
                escaped_comment = col['comment'].replace("'", "''")
                sql += f";\nCOMMENT ON COLUMN \"{table}\".\"{col['name']}\" IS '{escaped_comment}'"
        
        return sql + ";"
    
    def generate_add_column_sql(self, table: str, column: dict) -> str:
        col_def = f"\"{column['name']}\" {column['type']}"
        if not column.get("nullable", True):
            col_def += " NOT NULL"
        if column.get("default") is not None:
            default_val = column['default']
            if not default_val.startswith("'") and not default_val.upper() in ('NULL', 'TRUE', 'FALSE', 'CURRENT_TIMESTAMP', 'NOW()'):
                # 转义单引号，防止 SQL 注入和语法错误
                escaped_default = default_val.replace("'", "''")
                default_val = f"'{escaped_default}'"
            col_def += f" DEFAULT {default_val}"
        sql = f"ALTER TABLE \"{table}\" ADD COLUMN {col_def};"
        if column.get("comment"):
            # 转义单引号，防止 SQL 注入和语法错误
            escaped_comment = column['comment'].replace("'", "''")
            sql += f"\nCOMMENT ON COLUMN \"{table}\".\"{column['name']}\" IS '{escaped_comment}';"
        return sql
    
    def generate_modify_column_sql(self, table: str, old_column: dict, new_column: dict) -> str:
        col_def = f"\"{new_column['name']}\" {new_column['type']}"
        if not new_column.get("nullable", True):
            col_def += " NOT NULL"
        if new_column.get("default") is not None:
            default_val = new_column['default']
            if not default_val.startswith("'") and not default_val.upper() in ('NULL', 'TRUE', 'FALSE', 'CURRENT_TIMESTAMP', 'NOW()'):
                # 转义单引号，防止 SQL 注入和语法错误
                escaped_default = default_val.replace("'", "''")
                default_val = f"'{escaped_default}'"
            col_def += f" DEFAULT {default_val}"
        sql = f"ALTER TABLE \"{table}\" ALTER COLUMN \"{new_column['name']}\" TYPE {new_column['type']} USING \"{new_column['name']}\"::{new_column['type'].split('(')[0]};"
        if new_column.get("comment"):
            # 转义单引号，防止 SQL 注入和语法错误
            escaped_comment = new_column['comment'].replace("'", "''")
            sql += f"\nCOMMENT ON COLUMN \"{table}\".\"{new_column['name']}\" IS '{escaped_comment}';"
        return sql
    
    def generate_drop_column_sql(self, table: str, column_name: str) -> str:
        return f"ALTER TABLE \"{table}\" DROP COLUMN \"{column_name}\";"
    
    def generate_add_index_sql(self, table: str, index: dict) -> str:
        cols = ", ".join(f"\"{c}\"" for c in index["columns"])
        unique = "UNIQUE " if index.get("unique") else ""
        return f"CREATE {unique}INDEX \"{index['name']}\" ON \"{table}\" ({cols});"
    
    def generate_drop_index_sql(self, table: str, index_name: str) -> str:
        return f"DROP INDEX \"{index_name}\";"
    
    def generate_add_foreign_key_sql(self, table: str, fk: dict) -> str:
        cols = ", ".join(f"\"{c}\"" for c in fk["columns"])
        ref_cols = ", ".join(f"\"{c}\"" for c in fk["ref_columns"])
        sql = f"ALTER TABLE \"{table}\" ADD CONSTRAINT \"{fk['name']}\" FOREIGN KEY ({cols}) REFERENCES \"{fk['ref_table']}\" ({ref_cols})"
        if fk.get("on_delete"):
            sql += f" ON DELETE {fk['on_delete']}"
        if fk.get("on_update"):
            sql += f" ON UPDATE {fk['on_update']}"
        return sql + ";"
    
    def generate_drop_foreign_key_sql(self, table: str, fk_name: str) -> str:
        return f"ALTER TABLE \"{table}\" DROP CONSTRAINT \"{fk_name}\";"
