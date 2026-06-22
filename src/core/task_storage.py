"""对比任务配置持久化模块"""
import json
import os
from pathlib import Path
from typing import Optional


class TaskStorage:
    """对比任务配置存储管理器"""
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_dir = Path.home() / ".db_diff_tool"
            config_dir.mkdir(exist_ok=True)
            config_file = str(config_dir / "tasks.json")
        
        self.config_file = config_file
        self.tasks = []
        self._load()
    
    def _load(self):
        """从文件加载任务配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.tasks = []
        else:
            self.tasks = []
    
    def _save(self):
        """保存任务配置到文件"""
        config_dir = os.path.dirname(self.config_file)
        os.makedirs(config_dir, exist_ok=True)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)
    
    def add_task(self, name: str, source_conn_id: str, target_conn_id: str, 
                 filters: dict = None) -> dict:
        """添加新任务
        
        Args:
            name: 任务名称
            source_conn_id: 源数据库连接ID
            target_conn_id: 目标数据库连接ID
            filters: 过滤配置(可选)
            
        Returns:
            新任务字典
        """
        task = {
            "id": f"task_{len(self.tasks) + 1}",
            "name": name,
            "source_conn_id": source_conn_id,
            "target_conn_id": target_conn_id,
            "filters": filters or {},
            "created_at": self._get_timestamp(),
        }
        
        self.tasks.append(task)
        self._save()
        return task
    
    def update_task(self, task_id: str, name: str = None, source_conn_id: str = None,
                    target_conn_id: str = None, filters: dict = None) -> Optional[dict]:
        """更新任务配置"""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                if name is not None:
                    self.tasks[i]["name"] = name
                if source_conn_id is not None:
                    self.tasks[i]["source_conn_id"] = source_conn_id
                if target_conn_id is not None:
                    self.tasks[i]["target_conn_id"] = target_conn_id
                if filters is not None:
                    self.tasks[i]["filters"] = filters
                
                self._save()
                return self.tasks[i]
        return None
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        original_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if len(self.tasks) < original_len:
            self._save()
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """获取指定任务"""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> list[dict]:
        """获取所有任务列表"""
        return self.tasks
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 全局实例
task_storage = TaskStorage()
