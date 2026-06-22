"""独立入口文件 - 用于 PyInstaller 打包"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.main import MainWindow

if __name__ == '__main__':
    # 获取临时目录（PyInstaller onefile 解压位置）
    if getattr(sys, 'frozen', False):
        # 打包后运行
        application_path = os.path.dirname(sys.executable)
    else:
        # 开发环境运行
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # 添加资源路径
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(application_path, 'src')
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
