"""数据库连接配置持久化模块"""
import json
import os
from pathlib import Path
from typing import Optional


class ConnectionStorage:
    """连接配置存储管理器"""
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_dir = Path.home() / ".db_diff_tool"
            config_dir.mkdir(exist_ok=True)
            config_file = str(config_dir / "connections.json")
        
        self.config_file = config_file
        self.connections = []
        self._load()
    
    def _load(self):
        """从文件加载连接配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.connections = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.connections = []
        else:
            self.connections = []
    
    def _save(self):
        """保存连接配置到文件"""
        config_dir = os.path.dirname(self.config_file)
        os.makedirs(config_dir, exist_ok=True)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.connections, f, indent=2, ensure_ascii=False)
    
    def add_connection(self, name: str, config: dict, save_password: bool = True) -> dict:
        """添加新连接
        
        Args:
            name: 连接名称（自定义）
            config: 连接配置字典
            save_password: 是否保存密码
            
        Returns:
            新连接字典
        """
        connection = {
            "id": f"conn_{len(self.connections) + 1}",
            "name": name,
            "db_type": config.get("db_type", "mysql"),
            "host": config.get("host", "localhost"),
            "port": config.get("port", 3306),
            "user": config.get("user", ""),
            "database": config.get("database", ""),
            "save_password": save_password,
        }
        
        if save_password:
            connection["password"] = config.get("password", "")
        else:
            connection["password"] = ""
        
        self.connections.append(connection)
        self._save()
        return connection
    
    def update_connection(self, conn_id: str, config: dict, save_password: bool = True) -> Optional[dict]:
        """更新连接配置"""
        for i, conn in enumerate(self.connections):
            if conn["id"] == conn_id:
                self.connections[i].update({
                    "name": config.get("name", conn["name"]),
                    "db_type": config.get("db_type", conn["db_type"]),
                    "host": config.get("host", conn["host"]),
                    "port": config.get("port", conn["port"]),
                    "user": config.get("user", conn["user"]),
                    "database": config.get("database", conn["database"]),
                    "save_password": save_password,
                })
                
                if save_password:
                    self.connections[i]["password"] = config.get("password", conn.get("password", ""))
                else:
                    self.connections[i]["password"] = ""
                
                self._save()
                return self.connections[i]
        return None
    
    def delete_connection(self, conn_id: str) -> bool:
        """删除连接"""
        original_len = len(self.connections)
        self.connections = [c for c in self.connections if c["id"] != conn_id]
        if len(self.connections) < original_len:
            self._save()
            return True
        return False
    
    def get_connection(self, conn_id: str) -> Optional[dict]:
        """获取指定连接"""
        for conn in self.connections:
            if conn["id"] == conn_id:
                return conn
        return None
    
    def get_all_connections(self) -> list[dict]:
        """获取所有连接列表"""
        return self.connections
    
    def get_connection_config(self, conn_id: str) -> Optional[dict]:
        """获取可用于连接的配置字典"""
        conn = self.get_connection(conn_id)
        if conn:
            return {
                "db_type": conn["db_type"],
                "host": conn["host"],
                "port": conn["port"],
                "user": conn["user"],
                "password": conn["password"],
                "database": conn["database"],
            }
        return None


# 全局实例
storage = ConnectionStorage()
