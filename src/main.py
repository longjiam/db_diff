import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLabel, QSplitter, QFileDialog,
    QMessageBox, QProgressBar, QToolBar, QStatusBar, QMenuBar, QSizePolicy, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QAction
from sqlalchemy import text

from .ui.db_config_panel import DBConnectionSelector
from .ui.diff_viewer import DiffViewer
from .ui.sql_preview_panel import SQLPreviewPanel
from .ui.log_panel import LogPanel
from .ui.task_manager_panel import TaskManagerDialog
from .core.db_connector import DBConnection
from .core.schema_extractor import SchemaExtractor
from .core.diff_engine import DiffEngine
from .core.sql_generator import SQLGenerator
from .core.adapters.registry import get_adapter
from .core.theme_manager import theme_manager, DARK_THEME, LIGHT_THEME, style_dialog_buttons, show_message


class TestConnectionWorker(QThread):
    """异步测试连接工作线程"""
    finished = Signal(bool, str)  # (成功/失败, 消息)
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
    
    def run(self):
        try:
            conn = DBConnection(self.config["db_type"], self.config)
            success, msg = conn.test_connection()
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))


class ExecuteSQLWorker(QThread):
    """异步执行SQL工作线程"""
    progress = Signal(int, str)
    finished = Signal(bool, str)
    error = Signal(str)
    
    def __init__(self, config: dict, sql: str):
        super().__init__()
        self.config = config
        self.sql = sql
    
    def run(self):
        try:
            self.progress.emit(10, "连接数据库...")
            conn = DBConnection(self.config["db_type"], self.config)
            conn.connect()
            
            self.progress.emit(30, "开始执行 SQL...")
            
            # 分割SQL语句（按分号分割）
            statements = [s.strip() for s in self.sql.split(';') if s.strip() and not s.strip().startswith('--')]
            
            total = len(statements)
            for i, stmt in enumerate(statements, 1):
                try:
                    progress = 30 + int((i / total) * 60)
                    self.progress.emit(progress, f"执行 {i}/{total}...")
                    conn.connection.execute(text(stmt))
                    conn.connection.commit()
                except Exception as e:
                    self.error.emit(f"执行第 {i} 条SQL失败: {str(e)}\nSQL: {stmt}")
                    conn.disconnect()
                    return
            
            self.progress.emit(100, "执行完成")
            conn.disconnect()
            self.finished.emit(True, f"成功执行 {total} 条SQL语句")
            
        except Exception as e:
            self.error.emit(f"执行SQL时发生错误: {str(e)}")


class DiffWorker(QThread):
    """异步对比工作线程 - 并行提取两个数据库"""
    progress = Signal(int, str)
    finished = Signal(list)
    error = Signal(str)
    
    def __init__(self, config_a: dict, config_b: dict):
        super().__init__()
        self.config_a = config_a
        self.config_b = config_b
    
    def run(self):
        try:
            import threading
            
            result_a = {"schema": None, "views": None, "procedures": None, "triggers": None, "error": None}
            result_b = {"schema": None, "views": None, "procedures": None, "triggers": None, "error": None}
            
            def extract_database(config, result, label):
                """提取单个数据库的结构"""
                try:
                    conn = DBConnection(config["db_type"], config)
                    conn.connect()
                    
                    extractor = SchemaExtractor(conn.adapter, conn.connection)
                    result["schema"] = extractor.extract_all_tables()
                    result["views"] = extractor.extract_views()
                    result["procedures"] = extractor.extract_procedures()
                    result["triggers"] = extractor.extract_triggers()
                    
                    conn.disconnect()
                except Exception as e:
                    result["error"] = f"数据库 {label} 提取失败: {str(e)}"
            
            # 并行提取两个数据库
            self.progress.emit(10, "正在提取数据库结构...")
            
            thread_a = threading.Thread(target=extract_database, args=(self.config_a, result_a, "A"))
            thread_b = threading.Thread(target=extract_database, args=(self.config_b, result_b, "B"))
            
            thread_a.start()
            thread_b.start()
            
            # 等待完成（带进度更新）
            import time
            last_progress = 10
            while thread_a.is_alive() or thread_b.is_alive():
                if last_progress < 70:
                    last_progress += 5
                    self.progress.emit(last_progress, f"提取中... {last_progress}%")
                time.sleep(0.3)
            
            # 提取完成
            self.progress.emit(75, "提取完成")
            
            # 检查错误
            if result_a["error"]:
                raise Exception(result_a["error"])
            if result_b["error"]:
                raise Exception(result_b["error"])
            
            self.progress.emit(80, "对比差异...")
            engine = DiffEngine()
            diffs = engine.compare(
                result_a["schema"], result_b["schema"],
                result_a["views"], result_b["views"],
                result_a["procedures"], result_b["procedures"],
                result_a["triggers"], result_b["triggers"]
            )
            
            self.progress.emit(100, f"对比完成，共 {len(diffs)} 处差异")
            self.finished.emit(diffs)
            
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据库结构对比同步工具")
        self.resize(1400, 900)
        self.test_worker = None
        self.diff_worker = None
        self.execute_worker = None
        self.init_ui()
    
    def closeEvent(self, event):
        """窗口关闭时停止所有工作线程"""
        if self.diff_worker and self.diff_worker.isRunning():
            self.diff_worker.terminate()
            self.diff_worker.wait()
        if self.test_worker and self.test_worker.isRunning():
            self.test_worker.terminate()
            self.test_worker.wait()
        if self.execute_worker and self.execute_worker.isRunning():
            self.execute_worker.terminate()
            self.execute_worker.wait()
        event.accept()
    
    def init_ui(self):
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()
        self.init_central_widget()
        self.apply_style()
    
    def init_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("文件")
        
        export_action = QAction("导出 SQL", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_sql)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        tools_menu = menubar.addMenu("工具")
        
        compare_action = QAction("开始对比", self)
        compare_action.setShortcut("Ctrl+D")
        compare_action.triggered.connect(self.start_compare)
        tools_menu.addAction(compare_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        theme_action = QAction("切换主题", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
    
    def init_toolbar(self):
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        
        compare_btn = QPushButton("▶ 开始对比")
        compare_btn.setObjectName("secondaryBtn")
        compare_btn.setMinimumWidth(120)
        compare_btn.clicked.connect(self.start_compare)
        toolbar.addWidget(compare_btn)
        
        toolbar.addSeparator()
        
        # 任务管理按钮
        task_btn = QPushButton("📋 任务管理")
        task_btn.setObjectName("secondaryBtn")
        task_btn.clicked.connect(self.open_task_manager)
        toolbar.addWidget(task_btn)
        
        toolbar.addSeparator()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(250)
        self.progress_bar.setVisible(False)
        toolbar.addWidget(self.progress_bar)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
    
    def init_statusbar(self):
        statusbar = self.statusBar()
        self.status_label = QLabel("就绪")
        statusbar.addWidget(self.status_label)
        
        self.selected_label = QLabel("已选: 0/0 项")
        statusbar.addPermanentWidget(self.selected_label)
    
    def init_central_widget(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 数据库连接选择
        conn_layout = QHBoxLayout()
        conn_layout.setSpacing(20)
        
        self.panel_a = DBConnectionSelector("源数据库")
        self.panel_a.test_connection.connect(self.test_source_connection)
        conn_layout.addWidget(self.panel_a)
        
        self.panel_b = DBConnectionSelector("目标数据库")
        self.panel_b.test_connection.connect(self.test_target_connection)
        conn_layout.addWidget(self.panel_b)
        
        main_layout.addLayout(conn_layout)
        
        # 工作区(三个面板同时显示)
        splitter = QSplitter(Qt.Vertical)
        
        # 差异查看器(最大空间)
        self.diff_viewer = DiffViewer()
        self.diff_viewer.selection_changed.connect(self.update_sql_preview)
        splitter.addWidget(self.diff_viewer)
        
        # SQL 预览(中等空间)
        self.sql_panel = SQLPreviewPanel()
        self.sql_panel.execute_requested.connect(self.execute_sql)
        splitter.addWidget(self.sql_panel)
        
        # 日志面板(最小空间)
        self.log_panel = LogPanel()
        splitter.addWidget(self.log_panel)
        
        # 设置比例 4:2:1
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
    
    def test_source_connection(self, config: dict):
        """异步测试源连接"""
        self.log_panel.log(f"测试源连接: {config['host']}:{config['port']}/{config['database']}")
        self.status_label.setText("正在测试连接...")
        
        self.test_worker = TestConnectionWorker(config)
        self.test_worker.finished.connect(self.on_test_finished)
        self.test_worker.start()
    
    def test_target_connection(self, config: dict):
        """异步测试目标连接"""
        self.log_panel.log(f"测试目标连接: {config['host']}:{config['port']}/{config['database']}")
        self.status_label.setText("正在测试连接...")
        
        self.test_worker = TestConnectionWorker(config)
        self.test_worker.finished.connect(self.on_test_finished)
        self.test_worker.start()
    
    def on_test_finished(self, success: bool, msg: str):
        """测试连接完成"""
        if success:
            self.log_panel.log(f"连接测试成功", "SUCCESS")
            show_message(self, "连接成功", "数据库连接测试成功！")
        else:
            self.log_panel.log(f"连接失败: {msg}", "ERROR")
            show_message(self, "连接失败", f"数据库连接测试失败：\n{msg}", QMessageBox.Warning)
        self.status_label.setText("就绪")
    
    def load_task(self, source_conn_id: str, target_conn_id: str):
        """加载任务配置"""
        from .core.connection_storage import storage
        
        # 设置源数据库连接
        for i in range(self.panel_a.connection_combo.count()):
            if self.panel_a.connection_combo.itemData(i) == source_conn_id:
                self.panel_a.connection_combo.setCurrentIndex(i)
                break
        
        # 设置目标数据库连接
        for i in range(self.panel_b.connection_combo.count()):
            if self.panel_b.connection_combo.itemData(i) == target_conn_id:
                self.panel_b.connection_combo.setCurrentIndex(i)
                break
        
        self.log_panel.log(f"已加载任务配置", "SUCCESS")
    
    def open_task_manager(self):
        """打开任务管理对话框"""
        dialog = TaskManagerDialog(self)
        dialog.task_loaded.connect(self.load_task)
        dialog.exec()
    
    def start_compare(self):
        """开始对比"""
        config_a = self.panel_a.get_config()
        config_b = self.panel_b.get_config()
        
        if not config_a:
            show_message(self, "警告", "请先配置源数据库连接", QMessageBox.Warning)
            return
        
        if not config_b:
            show_message(self, "警告", "请先配置目标数据库连接", QMessageBox.Warning)
            return
        
        self.log_panel.log(f"开始对比: {config_a['database']} -> {config_b['database']}", "INFO")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.diff_worker = DiffWorker(config_a, config_b)
        self.diff_worker.progress.connect(self.update_progress)
        self.diff_worker.finished.connect(self.on_compare_finished)
        self.diff_worker.error.connect(self.on_compare_error)
        self.diff_worker.start()
    
    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        # 只在关键节点记录日志
        if value in [10, 80, 100]:
            self.log_panel.log(message)
    
    def on_compare_finished(self, diffs: list):
        """对比完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"对比完成，发现 {len(diffs)} 处差异")
        self.log_panel.log(f"对比完成，共发现 {len(diffs)} 处差异", "SUCCESS")
        
        # 更新 SQL 预览的数据库类型（用于语法高亮）
        if hasattr(self, 'config_a') and self.config_a:
            db_type = self.config_a.get("db_type")
            self.sql_panel.set_db_type(db_type)
        
        if len(diffs) == 0:
            show_message(self, "提示", "两个数据库结构完全一致！")
        else:
            self.diff_viewer.load_diffs(diffs)
            self.update_sql_preview()
    
    def on_compare_error(self, error_msg: str):
        """对比出错"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("对比出错")
        self.log_panel.log(f"对比失败: {error_msg}", "ERROR")
        show_message(self, "错误", f"对比过程中发生错误：\n{error_msg}", QMessageBox.Critical)
    
    def execute_sql(self, sql: str):
        """执行 SQL"""
        config_b = self.panel_b.get_config()
        
        if not config_b["database"]:
            show_message(self, "警告", "请先选择目标数据库", QMessageBox.Warning)
            return
        
        self.log_panel.log(f"开始执行 SQL 同步...", "INFO")
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 启动执行工作线程
        self.execute_worker = ExecuteSQLWorker(config_b, sql)
        self.execute_worker.progress.connect(self.update_progress)
        self.execute_worker.finished.connect(self.on_execute_finished)
        self.execute_worker.error.connect(self.on_execute_error)
        self.execute_worker.start()
    
    def on_execute_finished(self, success: bool, msg: str):
        """执行完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(msg)
        self.log_panel.log(msg, "SUCCESS" if success else "ERROR")
        
        if success:
            show_message(self, "执行成功", msg)
        else:
            show_message(self, "执行失败", msg, QMessageBox.Warning)
    
    def on_execute_error(self, error_msg: str):
        """执行出错"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("执行出错")
        self.log_panel.log(error_msg, "ERROR")
        show_message(self, "错误", error_msg, QMessageBox.Critical)
    
    def update_sql_preview(self):
        """更新 SQL 预览"""
        diffs = self.diff_viewer.get_selected_diffs()
        if not diffs:
            self.sql_panel.update_sql("-- 没有选中的差异项", 0)
            self.selected_label.setText("已选: 0/0 项")
            return
        
        # 使用目标库类型生成 SQL
        config = self.panel_b.get_config()
        if config:
            adapter = get_adapter(config["db_type"])
            generator = SQLGenerator(adapter)
            sql = generator.generate_sync_sql(diffs)
            self.sql_panel.update_sql(sql, len(diffs))
            self.selected_label.setText(f"已选: {len(diffs)} 项")
    
    def export_sql(self):
        """导出 SQL"""
        sql = self.sql_panel.current_sql
        if not sql:
            show_message(self, "提示", "没有可导出的 SQL")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存 SQL 文件", "sync.sql", "SQL Files (*.sql);;All Files (*)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sql)
            self.log_panel.log(f"SQL 已导出到: {file_path}", "SUCCESS")
            show_message(self, "导出成功", f"SQL 文件已保存到:\n{file_path}")
    
    def apply_style(self):
        """应用主题样式"""
        theme_manager.register_callback(self.update_theme)
        self.update_theme(theme_manager.current_theme)
    
    def update_theme(self, theme):
        """主题变化时更新"""
        self.setStyleSheet(theme_manager.generate_stylesheet())
        self.status_label.setText(f"🌙 黑夜主题" if theme.is_dark else "☀️ 白天主题")
    
    def toggle_theme(self):
        """切换主题"""
        theme_manager.toggle()
        # 重新应用主题样式表到整个窗口和所有子控件
        self.setStyleSheet(theme_manager.generate_stylesheet())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
