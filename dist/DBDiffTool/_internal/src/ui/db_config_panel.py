from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QMessageBox,
    QDialogButtonBox, QCheckBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Signal
from ..core.adapters.registry import get_supported_types
from ..core.connection_storage import storage
from ..core.theme_manager import theme_manager, style_dialog_buttons, show_message


class ConnectionDialog(QDialog):
    """数据库连接配置对话框"""
    
    def __init__(self, parent=None, edit_conn=None):
        super().__init__(parent)
        self.edit_conn = edit_conn
        self.setWindowTitle("编辑连接" if edit_conn else "新建连接")
        self.resize(450, 380)
        self.result_config = None
        self.init_ui()
        self.setStyleSheet(theme_manager.generate_stylesheet())
        
        if edit_conn:
            self._load_connection(edit_conn)
    
    def _load_connection(self, conn: dict):
        """加载已有连接信息"""
        self.name_input.setText(conn["name"])
        self.type_combo.setCurrentText(conn["db_type"])
        self.host_input.setText(conn["host"])
        self.port_input.setValue(conn["port"])
        self.user_input.setText(conn["user"])
        self.password_input.setText(conn.get("password", ""))
        self.database_input.setText(conn["database"])
        self.save_password.setChecked(conn.get("save_password", True))
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)
        
        # 连接名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入连接名称（自定义）")
        form.addRow("连接名称:", self.name_input)
        
        # 数据库类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(get_supported_types())
        form.addRow("数据库类型:", self.type_combo)
        
        # 主机
        self.host_input = QLineEdit("localhost")
        form.addRow("主机:", self.host_input)
        
        # 端口
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(3306)
        form.addRow("端口:", self.port_input)
        
        # 用户名
        self.user_input = QLineEdit("root")
        form.addRow("用户名:", self.user_input)
        
        # 密码
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form.addRow("密码:", self.password_input)
        
        # 数据库名
        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("输入数据库名称")
        form.addRow("数据库:", self.database_input)
        
        # 保存密码选项
        self.save_password = QCheckBox("保存密码到本地（加密存储）")
        self.save_password.setChecked(True)
        form.addRow("", self.save_password)
        
        layout.addLayout(form)
        
        # 提示文字
        tip_label = QLabel("💡 连接信息将保存在本地，下次启动可继续使用")
        tip_label.setObjectName("tipLabel")
        tip_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(tip_label)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        # 为按钮设置 objectName 以应用主题样式
        buttons.button(QDialogButtonBox.Ok).setObjectName("secondaryBtn")
        buttons.button(QDialogButtonBox.Cancel).setObjectName("secondaryBtn")
        
        layout.addWidget(buttons)
        
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self._on_type_changed(self.type_combo.currentText())
    
    def _on_type_changed(self, db_type: str):
        if db_type == "mysql":
            self.port_input.setValue(3306)
        elif db_type == "postgresql":
            self.port_input.setValue(5432)
    
    def accept(self):
        if not self.name_input.text():
            show_message(self, "警告", "请输入连接名称", QMessageBox.Warning)
            return
        
        if not self.database_input.text():
            show_message(self, "警告", "请输入数据库名称", QMessageBox.Warning)
            return
        
        self.result_config = {
            "name": self.name_input.text(),
            "db_type": self.type_combo.currentText(),
            "host": self.host_input.text(),
            "port": self.port_input.value(),
            "user": self.user_input.text(),
            "password": self.password_input.text(),
            "database": self.database_input.text(),
            "save_password": self.save_password.isChecked(),
        }
        super().accept()
    
    def get_config(self) -> dict:
        return self.result_config


class ConnectionManagerDialog(QDialog):
    """连接管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理连接")
        self.resize(600, 400)
        self.init_ui()
        self.setStyleSheet(theme_manager.generate_stylesheet())
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 连接列表
        self.conn_list = QListWidget()
        # 强制去除选中项的 outline 和边框
        self.conn_list.setStyleSheet("""
            QListWidget {
                outline: 0;
            }
            QListWidget::item:selected {
                outline: none;
                border: none;
            }
        """)
        self._load_connections()
        layout.addWidget(self.conn_list)
        
        # 按钮栏
        btn_layout = QHBoxLayout()
        
        new_btn = QPushButton("新建")
        new_btn.setObjectName("secondaryBtn")
        new_btn.clicked.connect(self._on_new)
        btn_layout.addWidget(new_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.setObjectName("secondaryBtn")
        edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("secondaryBtn")
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("secondaryBtn")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_connections(self):
        """加载连接列表"""
        self.conn_list.clear()
        for conn in storage.get_all_connections():
            display = f"{conn['name']} - {conn['db_type']}@{conn['host']}:{conn['port']}/{conn['database']}"
            item = QListWidgetItem(display)
            item.setData(100, conn["id"])
            self.conn_list.addItem(item)
    
    def _on_new(self):
        """新建连接"""
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            config = dialog.get_config()
            if config:
                storage.add_connection(
                    name=config["name"],
                    config=config,
                    save_password=config.get("save_password", True)
                )
                self._load_connections()
    
    def _on_edit(self):
        """编辑连接"""
        current = self.conn_list.currentItem()
        if not current:
            show_message(self, "提示", "请选择一个连接")
            return
        
        conn_id = current.data(100)
        conn = storage.get_connection(conn_id)
        if not conn:
            return
        
        dialog = ConnectionDialog(self, edit_conn=conn)
        if dialog.exec() == QDialog.Accepted:
            config = dialog.get_config()
            if config:
                storage.update_connection(conn_id, config, config.get("save_password", True))
                self._load_connections()
    
    def _on_delete(self):
        """删除连接"""
        current = self.conn_list.currentItem()
        if not current:
            show_message(self, "提示", "请选择一个连接")
            return
        
        conn_id = current.data(100)
        from PySide6.QtWidgets import QMessageBox
        reply = show_message(
            self, "确认删除",
            "确定要删除此连接吗？",
            QMessageBox.Question,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            storage.delete_connection(conn_id)
            self._load_connections()


class DBConnectionSelector(QWidget):
    """Navicat 风格数据库连接选择器"""
    
    test_connection = Signal(dict)
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.current_config = None
        self.init_ui()
        self._load_saved_connections()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel(f"{self.title}:"))
        
        self.connection_combo = QComboBox()
        self.connection_combo.setMinimumWidth(250)
        self.connection_combo.addItem("-- 选择连接 --")
        self.connection_combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.connection_combo)
        
        manage_btn = QPushButton("管理连接")
        manage_btn.setObjectName("secondaryBtn")
        manage_btn.clicked.connect(self._on_manage)
        layout.addWidget(manage_btn)
        
        test_btn = QPushButton("测试")
        test_btn.setObjectName("secondaryBtn")
        test_btn.clicked.connect(self._on_test)
        layout.addWidget(test_btn)
    
    def _load_saved_connections(self):
        """加载已保存的连接"""
        self.connection_combo.clear()
        self.connection_combo.addItem("-- 选择连接 --")
        
        for conn in storage.get_all_connections():
            display = f"{conn['name']} - {conn['db_type']}@{conn['host']}:{conn['port']}/{conn['database']}"
            self.connection_combo.addItem(display, userData=conn["id"])
    
    def _on_selection_changed(self, index: int):
        """选择变化时更新当前配置"""
        if index <= 0:
            self.current_config = None
            return
        
        conn_id = self.connection_combo.itemData(index)
        config = storage.get_connection_config(conn_id)
        self.current_config = config
    
    def _on_manage(self):
        """打开连接管理"""
        dialog = ConnectionManagerDialog(self)
        dialog.exec()
        self._load_saved_connections()
    
    def _on_test(self):
        """测试连接"""
        if not self.current_config:
            QMessageBox.information(self, "提示", "请先选择或配置连接")
            return
        self.test_connection.emit(self.current_config)
    
    def get_config(self) -> dict:
        """获取当前配置"""
        return self.current_config
