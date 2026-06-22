from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from ..core.theme_manager import theme_manager


class LogPanel(QWidget):
    """运行日志面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # 标题栏
        header = QHBoxLayout()
        header.addWidget(QLabel("运行日志:"))
        header.addStretch()
        
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.clicked.connect(self.clear)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # 日志文本框 - 不设置固定样式，由主题样式表控制
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
    
    def log(self, message: str, level: str = "INFO"):
        """添加日志
        
        Args:
            message: 日志内容
            level: 日志级别 (INFO, WARNING, ERROR, SUCCESS)
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据级别设置颜色
        color_map = {
            "INFO": "#d4d4d4",
            "WARNING": "#ffcc00",
            "ERROR": "#f44747",
            "SUCCESS": "#4CAF50",
        }
        color = color_map.get(level, "#d4d4d4")
        
        self.log_text.append(f'<span style="color:#888888">[{timestamp}]</span> <span style="color:{color}">[{level}]</span> {message}')
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear(self):
        """清空日志"""
        self.log_text.clear()
