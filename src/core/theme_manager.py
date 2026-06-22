"""UI 主题管理器 - 支持白天/黑夜模式切换"""

from PySide6.QtWidgets import QPushButton, QMessageBox


class Theme:
    """主题配置类"""
    
    def __init__(self, name: str, is_dark: bool, colors: dict):
        self.name = name
        self.is_dark = is_dark
        self.colors = colors


# 黑夜主题
DARK_THEME = Theme(
    name="dark",
    is_dark=True,
    colors={
        "bg_primary": "#1e1e1e",
        "bg_secondary": "#252526",
        "bg_tertiary": "#2d2d2d",
        "bg_hover": "#2a2d2e",
        "border": "#3a3a3a",
        "border_hover": "#4a4a4a",
        "header_bg": "#333333",
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "text_tertiary": "#888888",
        "accent": "#505050",
        "accent_hover": "#606060",
        "accent_pressed": "#404040",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "tree_alt_row": "#252526",
    }
)

# 白天主题
LIGHT_THEME = Theme(
    name="light",
    is_dark=False,
    colors={
        "bg_primary": "#ffffff",
        "bg_secondary": "#f5f5f5",
        "bg_tertiary": "#ffffff",
        "bg_hover": "#e8e8e8",
        "border": "#d0d0d0",
        "border_hover": "#b0b0b0",
        "header_bg": "#e8e8e8",
        "text_primary": "#1e1e1e",
        "text_secondary": "#4a4a4a",
        "text_tertiary": "#888888",
        "accent": "#b0b0b0",
        "accent_hover": "#a0a0a0",
        "accent_pressed": "#c0c0c0",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "tree_alt_row": "#f9f9f9",
    }
)


class ThemeManager:
    """主题管理器"""
    
    def __init__(self):
        self._current_theme = DARK_THEME
        self._callbacks = []
    
    @property
    def current_theme(self) -> Theme:
        return self._current_theme
    
    @property
    def is_dark(self) -> bool:
        return self._current_theme.is_dark
    
    def set_theme(self, theme: Theme):
        """切换主题"""
        self._current_theme = theme
        self._notify_callbacks()
    
    def toggle(self):
        """切换白天/黑夜"""
        if self._current_theme.is_dark:
            self._current_theme = LIGHT_THEME
        else:
            self._current_theme = DARK_THEME
        self._notify_callbacks()
    
    def register_callback(self, callback):
        """注册主题变化回调"""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self):
        """通知所有回调"""
        for callback in self._callbacks:
            callback(self._current_theme)
    
    def generate_stylesheet(self) -> str:
        """生成当前主题的样式表"""
        c = self._current_theme.colors
        return f"""
        QMainWindow, QWidget {{
            background-color: {c['bg_primary']};
        }}
        QLabel {{
            font-size: 13px;
            color: {c['text_secondary']};
            background-color: transparent;
        }}
        QLineEdit {{
            padding: 8px;
            border: 1px solid transparent;
            border-radius: 4px;
            background-color: {c['bg_tertiary']};
            color: {c['text_primary']};
            font-size: 13px;
        }}
        QLineEdit:hover {{
            border: 1px solid {c['border_hover']};
            background-color: {c['bg_hover']};
        }}
        QLineEdit:focus {{
            border: 1px solid {c['accent']};
            background-color: {c['bg_hover']};
        }}
        QComboBox {{
            padding: 8px;
            border: 1px solid transparent;
            border-radius: 4px;
            background-color: {c['bg_tertiary']};
            color: {c['text_primary']};
            font-size: 13px;
        }}
        QComboBox:hover {{
            border: 1px solid {c['border_hover']};
            background-color: {c['bg_hover']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c['bg_secondary']};
            color: {c['text_primary']};
            selection-background-color: {c['accent']};
            border: none;
            outline: none;
            padding: 4px;
        }}
        QComboBox QAbstractItemView::item {{
            border: none;
            padding: 6px 8px;
            border-radius: 3px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {c['bg_hover']};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {c['accent']};
        }}
        QSpinBox {{
            padding: 8px;
            border: 1px solid transparent;
            border-radius: 4px;
            background-color: {c['bg_tertiary']};
            color: {c['text_primary']};
            font-size: 13px;
        }}
        QSpinBox:hover {{
            border: 1px solid {c['border_hover']};
            background-color: {c['bg_hover']};
        }}
        QSpinBox:focus {{
            border: 1px solid {c['accent']};
            background-color: {c['bg_hover']};
        }}
        QCheckBox {{
            spacing: 8px;
            color: {c['text_primary']};
            font-size: 13px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: none;
            border-radius: 3px;
            background-color: {c['bg_tertiary']};
            color: transparent;
            font-size: 14px;
            font-weight: bold;
        }}
        QCheckBox::indicator:hover {{
            background-color: {c['bg_hover']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c['accent']};
            color: white;
        }}
        QPushButton {{
            background-color: {c['bg_tertiary']};
            color: {c['text_primary']};
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {c['bg_hover']};
            border: 1px solid {c['accent']};
        }}
        QPushButton:pressed {{
            background-color: {c['accent']};
            border: 1px solid {c['accent']};
        }}
        QPushButton#secondaryBtn {{
            background-color: {c['bg_tertiary']};
            color: {c['text_primary']};
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 13px;
        }}
        QPushButton#secondaryBtn:hover {{
            background-color: {c['bg_hover']};
            border: 1px solid {c['accent']};
        }}
        QPushButton#secondaryBtn:pressed {{
            background-color: {c['accent']};
            border: 1px solid {c['accent']};
        }}
        QProgressBar {{
            border: none;
            border-radius: 4px;
            background-color: {c['bg_tertiary']};
            text-align: center;
            color: {c['text_primary']};
        }}
        QProgressBar::chunk {{
            background-color: {c['accent']};
            border-radius: 3px;
        }}
        QStatusBar {{
            background-color: {c['bg_secondary']};
            color: {c['text_secondary']};
        }}
        QMenuBar {{
            background-color: {c['bg_secondary']};
            color: {c['text_primary']};
        }}
        QMenuBar::item:selected {{
            background-color: {c['border']};
        }}
        QMenu {{
            background-color: {c['bg_secondary']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
        }}
        QMenu::item:selected {{
            background-color: {c['border']};
        }}
        QToolBar {{
            background-color: {c['bg_secondary']};
            border-bottom: 1px solid {c['border']};
            padding: 5px;
        }}
        QSplitter::handle {{
            background-color: {c['border']};
        }}
        QTreeWidget {{
            background-color: {c['bg_secondary']};
            border: none;
            border-radius: 4px;
            color: {c['text_primary']};
            font-size: 13px;
            alternate-background-color: {c['tree_alt_row']};
            outline: 0;
        }}
        QTreeWidget::item {{
            padding: 4px 8px;
            border: none;
        }}
        QTreeWidget::item:hover {{
            background-color: {c['bg_hover']};
            border: none;
        }}
        QTreeWidget::item:selected {{
            background-color: {c['accent']};
            color: {c['text_primary']};
            border: none;
            outline: none;
        }}
        QListWidget {{
            background-color: {c['bg_secondary']};
            border: none;
            border-radius: 4px;
            color: {c['text_primary']};
            font-size: 13px;
            outline: 0;
        }}
        QListWidget::item {{
            padding: 6px 8px;
            color: {c['text_primary']};
            border: none;
        }}
        QListWidget::item:hover {{
            background-color: {c['bg_hover']};
            border: none;
        }}
        QListWidget::item:selected {{
            background-color: {c['accent']};
            color: {c['text_primary']};
            border: none;
            outline: none;
        }}
        QHeaderView::section {{
            background-color: {c['header_bg']};
            color: {c['text_primary']};
            padding: 6px;
            border: none;
            font-weight: bold;
        }}
        QTextEdit {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            color: {c['text_primary']};
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            padding: 10px;
        }}
        QGroupBox {{
            background-color: transparent;
            border: 1px solid {c['border']};
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 15px;
            font-weight: bold;
            color: {c['text_primary']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: {c['text_primary']};
        }}
        QDialog {{
            background-color: {c['bg_primary']};
        }}
        QDialog QLabel {{
            background-color: transparent;
        }}
        QLabel#tipLabel {{
            color: {c['text_tertiary']};
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            background-color: {c['bg_secondary']};
            width: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {c['border']};
            border-radius: 5px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c['border_hover']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background-color: {c['bg_secondary']};
            height: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {c['border']};
            border-radius: 5px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['border_hover']};
        }}
        """


# 全局主题实例
theme_manager = ThemeManager()


def style_dialog_buttons(dialog):
    """为对话框应用主题样式
    
    Args:
        dialog: QDialog 或 QMessageBox 实例
    """
    if dialog:
        dialog.setStyleSheet(theme_manager.generate_stylesheet())


def show_message(parent, title, message, icon=QMessageBox.Information, buttons=QMessageBox.Ok):
    """显示消息框并应用主题样式
    
    Args:
        parent: 父窗口
        title: 标题
        message: 消息内容
        icon: 图标类型 (QMessageBox.Information, Warning, Critical, Question)
        buttons: 按钮组合
    
    Returns:
        用户点击的按钮 ID
    """
    msg_box = QMessageBox(icon, title, message, buttons, parent)
    msg_box.setStyleSheet(theme_manager.generate_stylesheet())
    return msg_box.exec()
