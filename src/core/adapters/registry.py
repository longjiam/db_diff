from typing import Dict, Type
from .base import BaseDBAdapter

_registry: Dict[str, Type[BaseDBAdapter]] = {}


def register_adapter(db_type: str, adapter_class: Type[BaseDBAdapter]) -> None:
    """注册数据库适配器"""
    _registry[db_type] = adapter_class


def get_adapter(db_type: str) -> BaseDBAdapter:
    """获取指定类型的数据库适配器实例"""
    if db_type not in _registry:
        supported = list(_registry.keys())
        raise ValueError(f"不支持的数据库类型: {db_type}，支持的类型: {supported}")
    return _registry[db_type]()


def get_supported_types() -> list[str]:
    """获取所有已注册的数据库类型"""
    return list(_registry.keys())


# 自动注册内置适配器
from .mysql import MySQLAdapter
from .postgresql import PostgreSQLAdapter

register_adapter("mysql", MySQLAdapter)
register_adapter("postgresql", PostgreSQLAdapter)
