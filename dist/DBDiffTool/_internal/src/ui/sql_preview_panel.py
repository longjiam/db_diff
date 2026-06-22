from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QClipboard
from ..core.theme_manager import theme_manager, style_dialog_buttons, show_message
from .sql_highlighter import SQLHighlighter


class SQLPreviewPanel(QWidget):
    """SQL 实时预览面板"""
    
    execute_requested = Signal(str)  # 请求执行SQL
    
    def __init__(self, parent=None, db_type=None):
        super().__init__(parent)
        self.current_sql = ""
        self.db_type = db_type
        self.highlighter = None
        self.init_ui()
        # 初始化语法高亮
        self.highlighter = SQLHighlighter(self.sql_text.document(), db_type=db_type)
    
    def set_db_type(self, db_type: str):
        """设置数据库类型并更新高亮规则"""
        self.db_type = db_type
        if self.highlighter:
            self.highlighter.db_type = db_type
            self.highlighter.rehighlight()  # 重新应用高亮
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        header = QHBoxLayout()
        self.count_label = QLabel("SQL 预览 (0 项)")
        header.addWidget(self.count_label)
        header.addStretch()
        
        copy_btn = QPushButton("复制")
        copy_btn.setObjectName("secondaryBtn")
        copy_btn.clicked.connect(self.copy_sql)
        header.addWidget(copy_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setObjectName("secondaryBtn")
        save_btn.clicked.connect(self.save_sql)
        header.addWidget(save_btn)
        
        execute_btn = QPushButton("执行")
        execute_btn.setObjectName("secondaryBtn")
        execute_btn.clicked.connect(self.execute_sql)
        header.addWidget(execute_btn)
        
        layout.addLayout(header)
        
        # SQL 文本框 - 不设置固定样式，由主题样式表控制
        self.sql_text = QTextEdit()
        self.sql_text.setReadOnly(True)
        self.sql_text.setPlaceholderText("勾选差异项后，SQL 将在这里显示...")
        layout.addWidget(self.sql_text)
    
    def update_sql(self, sql: str, count: int = 0):
        """更新 SQL 预览"""
        self.current_sql = sql
        self.sql_text.setText(sql)  # setText 会自动触发语法高亮
        self.count_label.setText(f"SQL 预览 ({count} 项)")
    
    def copy_sql(self):
        """复制 SQL 到剪贴板"""
        if not self.current_sql:
            show_message(self, "提示", "没有可复制的 SQL")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_sql)
        show_message(self, "已复制", "SQL 已复制到剪贴板")
    
    def save_sql(self):
        """保存 SQL 到文件"""
        if not self.current_sql:
            show_message(self, "提示", "没有可保存的 SQL")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存 SQL 文件", "sync.sql", "SQL Files (*.sql);;All Files (*)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.current_sql)
            show_message(self, "保存成功", f"SQL 已保存到:\n{file_path}")
    
    def execute_sql(self):
        """请求执行 SQL"""
        if not self.current_sql:
            show_message(self, "提示", "没有可执行的 SQL")
            return
        
        # 确认对话框
        from PySide6.QtWidgets import QMessageBox
        reply = show_message(
            self,
            "确认执行",
            "确定要执行这些 SQL 语句吗？\n\n警告：此操作将修改目标数据库，请确保已备份数据！",
            QMessageBox.Question,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.execute_requested.emit(self.current_sql)


# 需要导入 QApplication
from PySide6.QtWidgets import QApplication
