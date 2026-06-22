"""对比任务管理面板"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QComboBox,
    QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from ..core.task_storage import task_storage
from ..core.connection_storage import storage
from ..core.theme_manager import show_message


class TaskDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task
        self.result = None
        self.init_ui()
        
        if task:
            self.name_input.setText(task["name"])
            # 找到并设置源连接
            for i in range(self.source_combo.count()):
                if self.source_combo.itemData(i) == task["source_conn_id"]:
                    self.source_combo.setCurrentIndex(i)
                    break
            # 找到并设置目标连接
            for i in range(self.target_combo.count()):
                if self.target_combo.itemData(i) == task["target_conn_id"]:
                    self.target_combo.setCurrentIndex(i)
                    break
    
    def init_ui(self):
        self.setWindowTitle("新建对比任务" if not self.task else "编辑对比任务")
        self.setMinimumWidth(400)
        self.setStyleSheet("QDialog { background-color: #252526; }")
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        # 任务名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: 开发环境 -> 生产环境")
        form.addRow("任务名称:", self.name_input)
        
        # 源数据库连接
        self.source_combo = QComboBox()
        self.source_combo.addItem("-- 请选择源连接 --")
        connections = storage.get_all_connections()
        for conn in connections:
            self.source_combo.addItem(f"{conn['name']} ({conn['host']}:{conn['port']}/{conn['database']})", conn["id"])
        form.addRow("源数据库:", self.source_combo)
        
        # 目标数据库连接
        self.target_combo = QComboBox()
        self.target_combo.addItem("-- 请选择目标连接 --")
        for conn in connections:
            self.target_combo.addItem(f"{conn['name']} ({conn['host']}:{conn['port']}/{conn['database']})", conn["id"])
        form.addRow("目标数据库:", self.target_combo)
        
        layout.addLayout(form)
        
        # 按钮
        buttons = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("secondaryBtn")
        save_btn.clicked.connect(self.save)
        buttons.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
    
    def save(self):
        name = self.name_input.text().strip()
        source_id = self.source_combo.currentData()
        target_id = self.target_combo.currentData()
        
        if not name:
            show_message(self, "警告", "请输入任务名称")
            return
        
        if not source_id:
            show_message(self, "警告", "请选择源数据库连接")
            return
        
        if not target_id:
            show_message(self, "警告", "请选择目标数据库连接")
            return
        
        self.result = {
            "name": name,
            "source_conn_id": source_id,
            "target_conn_id": target_id,
        }
        self.accept()


class TaskManagerDialog(QDialog):
    """对比任务管理对话框"""
    
    # 信号: 加载任务(源连接ID, 目标连接ID)
    task_loaded = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 对比任务管理")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("QDialog { background-color: #252526; }")
        self.init_ui()
        self.load_tasks()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel("对比任务管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        # 任务列表
        self.task_list = QListWidget()
        self.task_list.itemDoubleClicked.connect(self.load_task)
        layout.addWidget(self.task_list)
        
        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        new_btn = QPushButton("新建")
        new_btn.setObjectName("secondaryBtn")
        new_btn.clicked.connect(self.new_task)
        btn_layout.addWidget(new_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.setObjectName("secondaryBtn")
        edit_btn.clicked.connect(self.edit_task)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("secondaryBtn")
        delete_btn.clicked.connect(self.delete_task)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        load_btn = QPushButton("加载并关闭")
        load_btn.setObjectName("secondaryBtn")
        load_btn.clicked.connect(self.load_and_close)
        btn_layout.addWidget(load_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("secondaryBtn")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def load_tasks(self):
        """加载任务列表"""
        self.task_list.clear()
        tasks = task_storage.get_all_tasks()
        
        if not tasks:
            item = QListWidgetItem("暂无任务,点击\"新建\"添加...")
            item.setTextAlignment(Qt.AlignCenter)
            self.task_list.addItem(item)
            return
        
        for task in tasks:
            source_conn = storage.get_connection(task["source_conn_id"])
            target_conn = storage.get_connection(task["target_conn_id"])
            
            source_name = source_conn["name"] if source_conn else "未知"
            target_name = target_conn["name"] if target_conn else "未知"
            
            text = f"{task['name']}\n{source_name} → {target_name}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, task["id"])
            self.task_list.addItem(item)
    
    def new_task(self):
        """新建任务"""
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.result:
            result = dialog.result
            task_storage.add_task(
                result["name"],
                result["source_conn_id"],
                result["target_conn_id"]
            )
            self.load_tasks()
            show_message(self, "提示", "任务已保存")
    
    def edit_task(self):
        """编辑任务"""
        current = self.task_list.currentItem()
        if not current:
            show_message(self, "提示", "请选择一个任务")
            return
        
        task_id = current.data(Qt.UserRole)
        task = task_storage.get_task(task_id)
        if not task:
            return
        
        dialog = TaskDialog(self, task=task)
        if dialog.exec() == QDialog.Accepted and dialog.result:
            result = dialog.result
            task_storage.update_task(
                task_id,
                name=result["name"],
                source_conn_id=result["source_conn_id"],
                target_conn_id=result["target_conn_id"]
            )
            self.load_tasks()
            show_message(self, "提示", "任务已更新")
    
    def delete_task(self):
        """删除任务"""
        current = self.task_list.currentItem()
        if not current:
            show_message(self, "提示", "请选择一个任务")
            return
        
        task_id = current.data(Qt.UserRole)
        reply = show_message(
            self, "确认删除",
            "确定要删除此任务吗?",
            QMessageBox.Question,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            task_storage.delete_task(task_id)
            self.load_tasks()
    
    def load_task(self, item=None):
        """加载任务配置并关闭对话框"""
        # 如果没有传入 item，使用当前选中的项
        if item is None:
            item = self.task_list.currentItem()
        if not item:
            return
        
        task_id = item.data(Qt.UserRole)
        task = task_storage.get_task(task_id)
        if not task:
            return
        
        # 发射信号,通知主窗口加载任务
        self.task_loaded.emit(task["source_conn_id"], task["target_conn_id"])
        # 关闭对话框
        self.accept()
    
    def load_and_close(self):
        """加载任务并关闭对话框"""
        self.load_task()
        self.close()
