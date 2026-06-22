from typing import Any
from sqlalchemy import text
from .base import BaseDBAdapter


class MySQLAdapter(BaseDBAdapter):
    """MySQL 数据库适配器"""
    
    @property
    def db_type(self) -> str:
        return "mysql"
    
    def build_connection_string(self, config: dict) -> str:
        host = config.get("host", "localhost")
        port = config.get("port", 3306)
        user = config.get("user", "root")
        password = config.get("password", "")
        database = config.get("database", "")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    
    def get_tables(self, conn: Any) -> list[str]:
        result = conn.execute(text("SHOW TABLES"))
        return [row[0] for row in result.fetchall()]
    
    def get_table_comment(self, conn: Any, table: str) -> str:
        """获取表注释"""
        result = conn.execute(text("""
            SELECT TABLE_COMMENT 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = :table_name
        """), {"table_name": table})
        row = result.fetchone()
        return row[0] if row and row[0] else ""
    
    def get_columns(self, conn: Any, table: str) -> list[dict]:
        result = conn.execute(text(f"SHOW FULL COLUMNS FROM `{table}`"))
        columns = []
        for row in result.fetchall():
            columns.append({
                "name": row[0],
                "type": row[1],  # 完整类型，如 'longtext', 'varchar(255)', 'int' 等
                "nullable": row[3] == "YES",
                "default": row[5],
                "is_primary": row[4] == "PRI",
                "auto_increment": "auto_increment" in (row[6] or ""),
                "comment": row[8] if len(row) > 8 and row[8] else "",  # 字段注释
            })
        return columns
    
    def get_indexes(self, conn: Any, table: str) -> list[dict]:
        result = conn.execute(text(f"SHOW INDEX FROM `{table}`"))
        indexes = {}
        for row in result.fetchall():
            idx_name = row[2]
            if idx_name not in indexes:
                indexes[idx_name] = {
                    "name": idx_name,
                    "columns": [],
                    "unique": row[1] == 0,
                    "type": None,
                }
            indexes[idx_name]["columns"].append(row[4])
        return list(indexes.values())
    
    def get_foreign_keys(self, conn: Any, table: str) -> list[dict]:
        query = text("""
            SELECT 
                kcu.CONSTRAINT_NAME,
                kcu.COLUMN_NAME,
                kcu.REFERENCED_TABLE_NAME,
                kcu.REFERENCED_COLUMN_NAME,
                rc.DELETE_RULE,
                rc.UPDATE_RULE
            FROM information_schema.KEY_COLUMN_USAGE kcu
            JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
              ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
             AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
            WHERE kcu.TABLE_SCHEMA = DATABASE()
              AND kcu.TABLE_NAME = :table_name
              AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY kcu.CONSTRAINT_NAME, kcu.ORDINAL_POSITION
        """)
        result = conn.execute(query, {"table_name": table})
        fks = {}
        for row in result.fetchall():
            fk_name = row[0]
            if fk_name not in fks:
                fks[fk_name] = {
                    "name": fk_name,
                    "columns": [],
                    "ref_table": row[2],
                    "ref_columns": [],
                    "on_delete": row[4],
                    "on_update": row[5],
                }
            fks[fk_name]["columns"].append(row[1])
            fks[fk_name]["ref_columns"].append(row[3])
        return list(fks.values())
    
    def get_views(self, conn: Any) -> list[dict]:
        """获取所有视图定义"""
        result = conn.execute(text("""
            SELECT TABLE_NAME, VIEW_DEFINITION
            FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = DATABASE()
        """))
        views = []
        for row in result.fetchall():
            views.append({
                "name": row[0],
                "definition": row[1],
            })
        return views
    
    def get_procedures(self, conn: Any) -> list[dict]:
        """获取所有存储过程和函数定义"""
        result = conn.execute(text("""
            SELECT ROUTINE_NAME, ROUTINE_DEFINITION, ROUTINE_TYPE
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = DATABASE()
        """))
        procedures = []
        for row in result.fetchall():
            procedures.append({
                "name": row[0],
                "definition": row[1],
                "type": row[2],  # PROCEDURE 或 FUNCTION
            })
        return procedures
    
    def get_triggers(self, conn: Any) -> list[dict]:
        """获取所有触发器定义"""
        result = conn.execute(text("""
            SELECT TRIGGER_NAME, ACTION_STATEMENT, EVENT_OBJECT_TABLE, EVENT_MANIPULATION
            FROM information_schema.TRIGGERS
            WHERE TRIGGER_SCHEMA = DATABASE()
        """))
        triggers = []
        for row in result.fetchall():
            triggers.append({
                "name": row[0],
                "definition": row[1],
                "table": row[2],
                "event": row[3],  # INSERT/UPDATE/DELETE
            })
        return triggers
    
    # ========== SQL 生成 ==========
    
    def generate_create_table_sql(self, table: str, columns: list[dict],
                                   indexes: list[dict] = None,
                                   foreign_keys: list[dict] = None,
                                   table_comment: str = "") -> str:
        parts = []
        for col in columns:
            col_def = f"  `{col['name']}` {col['type']}"
            if not col.get("nullable", True):
                col_def += " NOT NULL"
            if col.get("default") is not None:
                default_val = col['default']
                # 处理特殊默认值
                if default_val.upper() in ('CURRENT_TIMESTAMP', 'NULL'):
                    col_def += f" DEFAULT {default_val}"
                else:
                    col_def += f" DEFAULT '{default_val}'"
            if col.get("auto_increment"):
                col_def += " AUTO_INCREMENT"
            if col.get("comment"):
                col_def += f" COMMENT '{col['comment']}'"
            parts.append(col_def)
        
        pk_cols = [c["name"] for c in columns if c.get("is_primary")]
        if pk_cols:
            cols_str = ", ".join(f"`{c}`" for c in pk_cols)
            parts.append(f"  PRIMARY KEY ({cols_str})")
        
        if indexes:
            for idx in indexes:
                if idx["name"] == "PRIMARY":
                    continue
                cols_str = ", ".join(f"`{c}`" for c in idx["columns"])
                unique = "UNIQUE " if idx.get("unique") else ""
                parts.append(f"  {unique}KEY `{idx['name']}` ({cols_str})")
        
        if foreign_keys:
            for fk in foreign_keys:
                cols_str = ", ".join(f"`{c}`" for c in fk["columns"])
                ref_cols_str = ", ".join(f"`{c}`" for c in fk["ref_columns"])
                fk_sql = f"  CONSTRAINT `{fk['name']}` FOREIGN KEY ({cols_str}) REFERENCES `{fk['ref_table']}` ({ref_cols_str})"
                if fk.get("on_delete"):
                    fk_sql += f" ON DELETE {fk['on_delete']}"
                if fk.get("on_update"):
                    fk_sql += f" ON UPDATE {fk['on_update']}"
                parts.append(fk_sql)
        
        cols = ",\n".join(parts)
        sql = f"CREATE TABLE `{table}` (\n{cols}\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        if table_comment:
            sql += f" COMMENT='{table_comment}'"
        sql += ";"
        return sql
    
    def generate_add_column_sql(self, table: str, column: dict) -> str:
        col_def = f"`{column['name']}` {column['type']}"
        if not column.get("nullable", True):
            col_def += " NOT NULL"
        if column.get("default") is not None:
            default_val = column['default']
            if default_val.upper() in ('CURRENT_TIMESTAMP', 'NULL'):
                col_def += f" DEFAULT {default_val}"
            else:
                col_def += f" DEFAULT '{default_val}'"
        if column.get("comment"):
            col_def += f" COMMENT '{column['comment']}'"
        return f"ALTER TABLE `{table}` ADD COLUMN {col_def};"
    
    def generate_modify_column_sql(self, table: str, old_column: dict, new_column: dict) -> str:
        col_def = f"`{new_column['name']}` {new_column['type']}"
        if not new_column.get("nullable", True):
            col_def += " NOT NULL"
        if new_column.get("default") is not None:
            default_val = new_column['default']
            if default_val.upper() in ('CURRENT_TIMESTAMP', 'NULL'):
                col_def += f" DEFAULT {default_val}"
            else:
                col_def += f" DEFAULT '{default_val}'"
        if new_column.get("comment"):
            col_def += f" COMMENT '{new_column['comment']}'"
        return f"ALTER TABLE `{table}` MODIFY COLUMN {col_def};"
    
    def generate_drop_column_sql(self, table: str, column_name: str) -> str:
        return f"ALTER TABLE `{table}` DROP COLUMN `{column_name}`;"
    
    def generate_add_index_sql(self, table: str, index: dict) -> str:
        cols = ", ".join(f"`{c}`" for c in index["columns"])
        unique = "UNIQUE " if index.get("unique") else ""
        return f"CREATE {unique}INDEX `{index['name']}` ON `{table}` ({cols});"
    
    def generate_drop_index_sql(self, table: str, index_name: str) -> str:
        return f"DROP INDEX `{index_name}` ON `{table}`;"
    
    def generate_add_foreign_key_sql(self, table: str, fk: dict) -> str:
        cols = ", ".join(f"`{c}`" for c in fk["columns"])
        ref_cols = ", ".join(f"`{c}`" for c in fk["ref_columns"])
        sql = f"ALTER TABLE `{table}` ADD CONSTRAINT `{fk['name']}` FOREIGN KEY ({cols}) REFERENCES `{fk['ref_table']}` ({ref_cols})"
        if fk.get("on_delete"):
            sql += f" ON DELETE {fk['on_delete']}"
        if fk.get("on_update"):
            sql += f" ON UPDATE {fk['on_update']}"
        return sql + ";"
    
    def generate_drop_foreign_key_sql(self, table: str, fk_name: str) -> str:
        return f"ALTER TABLE `{table}` DROP FOREIGN KEY `{fk_name}`;"
    
    # ========== 视图、存储过程、触发器 SQL 生成 ==========
    
    def generate_create_view_sql(self, view: dict) -> str:
        """生成 CREATE VIEW 语句"""
        return f"CREATE OR REPLACE VIEW `{view['name']}` AS {view['definition']};"
    
    def generate_drop_view_sql(self, view_name: str) -> str:
        """生成 DROP VIEW 语句"""
        return f"DROP VIEW IF EXISTS `{view_name}`;"
    
    def generate_create_procedure_sql(self, procedure: dict) -> str:
        """生成 CREATE PROCEDURE/FUNCTION 语句"""
        proc_type = procedure.get('type', 'PROCEDURE')
        return f"DROP {proc_type} IF EXISTS `{procedure['name']}`;\n{procedure['definition']};"
    
    def generate_drop_procedure_sql(self, procedure_name: str, proc_type: str = "PROCEDURE") -> str:
        """生成 DROP PROCEDURE/FUNCTION 语句"""
        return f"DROP {proc_type} IF EXISTS `{procedure_name}`;"
    
    def generate_create_trigger_sql(self, trigger: dict) -> str:
        """生成 CREATE TRIGGER 语句"""
        return f"DROP TRIGGER IF EXISTS `{trigger['name']}`;\n{trigger['definition']};"
    
    def generate_drop_trigger_sql(self, trigger_name: str) -> str:
        """生成 DROP TRIGGER 语句"""
        return f"DROP TRIGGER IF EXISTS `{trigger_name}`;"
