from typing import Any
from dataclasses import dataclass, field


@dataclass
class TableSchema:
    """表结构信息"""
    name: str
    comment: str = ""  # 表注释
    columns: list[dict] = field(default_factory=list)
    indexes: list[dict] = field(default_factory=list)
    foreign_keys: list[dict] = field(default_factory=list)


class SchemaExtractor:
    """数据库结构提取器"""
    
    def __init__(self, adapter, conn: Any):
        """
        Args:
            adapter: 数据库适配器实例（BaseDBAdapter）
            conn: 数据库连接对象
        """
        self.adapter = adapter
        self.conn = conn
    
    def extract_all_tables(self) -> list[TableSchema]:
        """提取数据库中所有表的完整结构信息"""
        table_names = self.adapter.get_tables(self.conn)
        schemas = []
        
        for table_name in table_names:
            schema = TableSchema(name=table_name)
            schema.comment = self.adapter.get_table_comment(self.conn, table_name) if hasattr(self.adapter, 'get_table_comment') else ""
            schema.columns = self.adapter.get_columns(self.conn, table_name)
            schema.indexes = self.adapter.get_indexes(self.conn, table_name)
            schema.foreign_keys = self.adapter.get_foreign_keys(self.conn, table_name)
            schemas.append(schema)
        
        return schemas
    
    def extract_table(self, table_name: str) -> TableSchema:
        """提取指定表的完整结构信息"""
        schema = TableSchema(name=table_name)
        schema.comment = self.adapter.get_table_comment(self.conn, table_name) if hasattr(self.adapter, 'get_table_comment') else ""
        schema.columns = self.adapter.get_columns(self.conn, table_name)
        schema.indexes = self.adapter.get_indexes(self.conn, table_name)
        schema.foreign_keys = self.adapter.get_foreign_keys(self.conn, table_name)
        return schema
    
    def extract_views(self) -> list[dict]:
        """提取所有视图定义"""
        if hasattr(self.adapter, 'get_views'):
            return self.adapter.get_views(self.conn)
        return []
    
    def extract_procedures(self) -> list[dict]:
        """提取所有存储过程/函数定义"""
        if hasattr(self.adapter, 'get_procedures'):
            return self.adapter.get_procedures(self.conn)
        return []
    
    def extract_triggers(self) -> list[dict]:
        """提取所有触发器定义"""
        if hasattr(self.adapter, 'get_triggers'):
            return self.adapter.get_triggers(self.conn)
        return []
