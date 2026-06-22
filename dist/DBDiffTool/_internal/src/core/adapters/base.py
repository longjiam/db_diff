from abc import ABC, abstractmethod
from typing import Any


class BaseDBAdapter(ABC):
    """数据库适配器抽象基类
    
    新增数据库只需继承此类并实现所有抽象方法，
    然后在 registry.py 中注册即可。
    """
    
    @property
    @abstractmethod
    def db_type(self) -> str:
        """返回数据库类型名称，如 'mysql', 'postgresql'"""
        pass
    
    @abstractmethod
    def build_connection_string(self, config: dict) -> str:
        """根据配置字典构建 SQLAlchemy 连接字符串
        
        Args:
            config: 包含 host, port, user, password, database 的字典
            
        Returns:
            SQLAlchemy 连接字符串，如 'mysql+pymysql://user:pass@host:3306/db'
        """
        pass
    
    @abstractmethod
    def get_tables(self, conn: Any) -> list[str]:
        """获取数据库中所有表名列表"""
        pass
    
    def get_table_comment(self, conn: Any, table: str) -> str:
        """获取表注释（可选实现，默认返回空字符串）"""
        return ""
    
    @abstractmethod
    def get_columns(self, conn: Any, table: str) -> list[dict]:
        """获取指定表的所有字段信息
        
        Returns:
            字段信息列表，每个字段为字典：
            {
                'name': str,          # 字段名
                'type': str,          # 数据类型（如 VARCHAR(255)）
                'nullable': bool,     # 是否允许 NULL
                'default': str|None,  # 默认值
                'is_primary': bool,   # 是否主键
                'auto_increment': bool # 是否自增
            }
        """
        pass
    
    @abstractmethod
    def get_indexes(self, conn: Any, table: str) -> list[dict]:
        """获取指定表的所有索引信息
        
        Returns:
            索引信息列表，每个索引为字典：
            {
                'name': str,          # 索引名
                'columns': list[str], # 索引包含的字段列表
                'unique': bool,       # 是否唯一索引
                'type': str           # 索引类型（BTREE, HASH 等）
            }
        """
        pass
    
    @abstractmethod
    def get_foreign_keys(self, conn: Any, table: str) -> list[dict]:
        """获取指定表的所有外键信息
        
        Returns:
            外键信息列表，每个外键为字典：
            {
                'name': str,          # 外键约束名
                'columns': list[str], # 当前表字段
                'ref_table': str,     # 引用表
                'ref_columns': list[str], # 引用字段
                'on_delete': str,     # ON DELETE 动作
                'on_update': str      # ON UPDATE 动作
            }
        """
        pass
    
    # ========== SQL 生成方法 ==========
    
    @abstractmethod
    def generate_create_table_sql(self, table: str, columns: list[dict], 
                                   indexes: list[dict] = None, 
                                   foreign_keys: list[dict] = None,
                                   table_comment: str = "") -> str:
        """生成 CREATE TABLE 语句"""
        pass
    
    @abstractmethod
    def generate_add_column_sql(self, table: str, column: dict) -> str:
        """生成 ALTER TABLE ADD COLUMN 语句"""
        pass
    
    @abstractmethod
    def generate_modify_column_sql(self, table: str, old_column: dict, new_column: dict) -> str:
        """生成 ALTER TABLE MODIFY/ALTER COLUMN 语句"""
        pass
    
    @abstractmethod
    def generate_drop_column_sql(self, table: str, column_name: str) -> str:
        """生成 ALTER TABLE DROP COLUMN 语句"""
        pass
    
    @abstractmethod
    def generate_add_index_sql(self, table: str, index: dict) -> str:
        """生成 CREATE INDEX 语句"""
        pass
    
    @abstractmethod
    def generate_drop_index_sql(self, table: str, index_name: str) -> str:
        """生成 DROP INDEX 语句"""
        pass
    
    @abstractmethod
    def generate_add_foreign_key_sql(self, table: str, fk: dict) -> str:
        """生成 ALTER TABLE ADD FOREIGN KEY 语句"""
        pass
    
    @abstractmethod
    def generate_drop_foreign_key_sql(self, table: str, fk_name: str) -> str:
        """生成 ALTER TABLE DROP FOREIGN KEY 语句"""
        pass
