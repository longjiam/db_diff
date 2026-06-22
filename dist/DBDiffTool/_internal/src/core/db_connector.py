from typing import Optional, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from .adapters.registry import get_adapter


class DBConnection:
    """数据库连接管理器"""
    
    def __init__(self, db_type: str, config: dict):
        """
        Args:
            db_type: 数据库类型（如 'mysql', 'postgresql'）
            config: 连接配置字典，包含 host, port, user, password, database
        """
        self.db_type = db_type
        self.config = config
        self.adapter = get_adapter(db_type)
        self.engine = None
        self.connection = None
    
    def connect(self) -> bool:
        """建立数据库连接
        
        Returns:
            是否连接成功
        """
        try:
            conn_str = self.adapter.build_connection_string(self.config)
            self.engine = create_engine(conn_str)
            self.connection = self.engine.connect()
            # 测试连接
            self.connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            raise ConnectionError(f"数据库连接失败: {str(e)}")
    
    def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.engine:
            self.engine.dispose()
            self.engine = None
    
    @contextmanager
    def get_session(self):
        """获取数据库连接的上下文管理器"""
        if not self.connection:
            self.connect()
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            if self.connection:
                self.connection.rollback()
            raise
    
    def test_connection(self) -> tuple[bool, str]:
        """测试数据库连接
        
        Returns:
            (是否成功, 错误信息)
        """
        try:
            self.connect()
            self.disconnect()
            return True, "连接成功"
        except ConnectionError as e:
            return False, str(e)
