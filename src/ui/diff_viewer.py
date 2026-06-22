from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QHeaderView,
    QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor
from ..core.diff_engine import DiffResult, DiffType
from ..core.theme_manager import theme_manager


# 差异类型对应的颜色（根据主题动态调整）
def get_diff_colors():
    """获取当前主题下的差异颜色"""
    if theme_manager.is_dark:
        # 黑夜主题 - 使用亮色
        return {
            DiffType.NEW_TABLE: "#4CAF50",
            DiffType.NEW_COLUMN: "#4CAF50",
            DiffType.NEW_INDEX: "#4CAF50",
            DiffType.NEW_FOREIGN_KEY: "#4CAF50",
            DiffType.NEW_VIEW: "#4CAF50",
            DiffType.NEW_PROCEDURE: "#4CAF50",
            DiffType.NEW_TRIGGER: "#4CAF50",
            DiffType.DROP_TABLE: "#F44336",
            DiffType.DROP_COLUMN: "#F44336",
            DiffType.DROP_INDEX: "#F44336",
            DiffType.DROP_FOREIGN_KEY: "#F44336",
            DiffType.DROP_VIEW: "#F44336",
            DiffType.DROP_PROCEDURE: "#F44336",
            DiffType.DROP_TRIGGER: "#F44336",
            DiffType.MODIFY_COLUMN: "#FF9800",
            DiffType.MODIFY_INDEX: "#FF9800",
            DiffType.MODIFY_FOREIGN_KEY: "#FF9800",
            DiffType.MODIFY_VIEW: "#FF9800",
            DiffType.MODIFY_PROCEDURE: "#FF9800",
            DiffType.MODIFY_TRIGGER: "#FF9800",
        }
    else:
        # 白天主题 - 使用稍暗的颜色以便在白色背景上可读
        return {
            DiffType.NEW_TABLE: "#2E7D32",
            DiffType.NEW_COLUMN: "#2E7D32",
            DiffType.NEW_INDEX: "#2E7D32",
            DiffType.NEW_FOREIGN_KEY: "#2E7D32",
            DiffType.NEW_VIEW: "#2E7D32",
            DiffType.NEW_PROCEDURE: "#2E7D32",
            DiffType.NEW_TRIGGER: "#2E7D32",
            DiffType.DROP_TABLE: "#C62828",
            DiffType.DROP_COLUMN: "#C62828",
            DiffType.DROP_INDEX: "#C62828",
            DiffType.DROP_FOREIGN_KEY: "#C62828",
            DiffType.DROP_VIEW: "#C62828",
            DiffType.DROP_PROCEDURE: "#C62828",
            DiffType.DROP_TRIGGER: "#C62828",
            DiffType.MODIFY_COLUMN: "#E65100",
            DiffType.MODIFY_INDEX: "#E65100",
            DiffType.MODIFY_FOREIGN_KEY: "#E65100",
            DiffType.MODIFY_VIEW: "#E65100",
            DiffType.MODIFY_PROCEDURE: "#E65100",
            DiffType.MODIFY_TRIGGER: "#E65100",
        }


DIFF_COLORS = get_diff_colors()


class DiffViewer(QWidget):
    """Navicat 风格差异结果查看器"""
    
    # 信号
    selection_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.diffs: list[DiffResult] = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 筛选工具栏
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("筛选:"))
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全部类型", "仅表", "仅索引", "仅外键"])
        self.type_filter.setMaximumWidth(150)
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        filter_bar.addWidget(self.type_filter)
        
        self.action_filter = QComboBox()
        self.action_filter.addItems(["全部操作", "仅新增", "仅修改", "仅删除"])
        self.action_filter.setMaximumWidth(150)
        self.action_filter.currentTextChanged.connect(self.apply_filters)
        filter_bar.addWidget(self.action_filter)
        
        filter_bar.addSpacing(20)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索对象名...")
        self.search_input.setMaximumWidth(250)
        self.search_input.textChanged.connect(self.apply_filters)
        filter_bar.addWidget(self.search_input)
        
        filter_bar.addStretch()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.setObjectName("secondaryBtn")
        select_all_btn.clicked.connect(self.select_all)
        filter_bar.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.setObjectName("secondaryBtn")
        deselect_all_btn.clicked.connect(self.deselect_all)
        filter_bar.addWidget(deselect_all_btn)
        
        layout.addLayout(filter_bar)
        
        # 树形表格
        self.tree = QTreeWidget()
        self.tree.setColumnCount(7)
        self.tree.setHeaderLabels(["", "对象类型", "对象名称", "操作", "源库", "目标库", "注释"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tree.setAlternatingRowColors(True)
        self.tree.setIconSize(QSize(16, 16))
        self.tree.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.tree)
    
    def load_diffs(self, diffs: list[DiffResult]):
        """加载差异结果到树形表格"""
        self.diffs = diffs
        self.tree.clear()
        
        # 按表名分组
        table_groups = {}
        for diff in diffs:
            if diff.table_name not in table_groups:
                table_groups[diff.table_name] = []
            table_groups[diff.table_name].append(diff)
        
        # 构建树
        for table_name, table_diffs in sorted(table_groups.items()):
            table_item = self._create_table_node(table_name, table_diffs)
            self.tree.addTopLevelItem(table_item)
            
            for diff in table_diffs:
                child = self._create_diff_node(diff)
                table_item.addChild(child)
            
            table_item.setExpanded(False)
        
        self.apply_filters()
    
    def _create_table_node(self, table_name: str, diffs: list[DiffResult]) -> QTreeWidgetItem:
        """创建表节点"""
        item = QTreeWidgetItem()
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Checked)
        
        item.setText(1, "表")
        item.setText(2, table_name)
        
        new_count = sum(1 for d in diffs if "NEW" in d.diff_type.name)
        mod_count = sum(1 for d in diffs if "MODIFY" in d.diff_type.name)
        del_count = sum(1 for d in diffs if "DROP" in d.diff_type.name)
        
        summary = []
        if new_count: summary.append(f"+{new_count}")
        if mod_count: summary.append(f"~{mod_count}")
        if del_count: summary.append(f"-{del_count}")
        
        # 根据差异类型决定操作列显示
        if not summary:
            action_text = "相同"
        elif new_count and not mod_count and not del_count:
            action_text = "+ 新增"
        elif del_count and not new_count and not mod_count:
            action_text = "- 删除"
        elif mod_count and not new_count and not del_count:
            action_text = "修改"
        else:
            action_text = "修改"
        
        item.setText(3, action_text)
        item.setText(4, f"{len(diffs)}处差异")
        item.setText(5, ", ".join(summary) if summary else "结构一致")
        
        item.setData(0, Qt.UserRole, {"type": "table", "diffs": diffs})
        return item
    
    def _create_diff_node(self, diff: DiffResult) -> QTreeWidgetItem:
        """创建差异子节点"""
        item = QTreeWidgetItem()
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Checked if diff.selected else Qt.Unchecked)
        
        type_map = {
            DiffType.NEW_TABLE: "表",
            DiffType.DROP_TABLE: "表",
            DiffType.NEW_COLUMN: "字段",
            DiffType.MODIFY_COLUMN: "字段",
            DiffType.DROP_COLUMN: "字段",
            DiffType.NEW_INDEX: "索引",
            DiffType.DROP_INDEX: "索引",
            DiffType.MODIFY_INDEX: "索引",
            DiffType.NEW_FOREIGN_KEY: "外键",
            DiffType.DROP_FOREIGN_KEY: "外键",
            DiffType.MODIFY_FOREIGN_KEY: "外键",
            DiffType.NEW_VIEW: "视图",
            DiffType.DROP_VIEW: "视图",
            DiffType.MODIFY_VIEW: "视图",
            DiffType.NEW_PROCEDURE: "存储过程",
            DiffType.DROP_PROCEDURE: "存储过程",
            DiffType.MODIFY_PROCEDURE: "存储过程",
            DiffType.NEW_TRIGGER: "触发器",
            DiffType.DROP_TRIGGER: "触发器",
            DiffType.MODIFY_TRIGGER: "触发器",
        }
        
        item.setText(1, type_map.get(diff.diff_type, diff.diff_type.value))
        item.setText(2, diff.object_name)
        
        action_map = {"NEW": "+ 新增", "MODIFY": "修改", "DROP": "- 删除"}
        action_key = diff.diff_type.name.split("_")[0]
        item.setText(3, action_map.get(action_key, diff.diff_type.value))
        
        color = DIFF_COLORS.get(diff.diff_type, "#FFFFFF")
        for col in range(7):
            item.setForeground(col, QColor(color))
        
        item.setText(4, diff.source_value or "-")
        item.setText(5, diff.target_value or "-")
        
        # 显示注释差异
        src_comment = diff.source_column.get("comment", "") if diff.source_column else ""
        tgt_comment = diff.target_column.get("comment", "") if diff.target_column else ""
        if src_comment or tgt_comment:
            item.setText(6, src_comment or tgt_comment)
        
        item.setData(0, Qt.UserRole, {"type": "diff", "diff": diff})
        
        return item
    
    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        """复选框变化"""
        if column != 0:
            return
        
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        
        is_checked = item.checkState(0) == Qt.Checked
        
        if data.get("type") == "table":
            # 表节点变化：同步所有子节点
            self.tree.blockSignals(True)
            try:
                for i in range(item.childCount()):
                    child = item.child(i)
                    child.setCheckState(0, Qt.Checked if is_checked else Qt.Unchecked)
                    child_data = child.data(0, Qt.UserRole)
                    if child_data and child_data.get("type") == "diff":
                        child_data["diff"].selected = is_checked
            finally:
                self.tree.blockSignals(False)
        elif data.get("type") == "diff":
            # 子节点变化：更新数据
            data["diff"].selected = is_checked
            
            # 更新父节点（表节点）的状态
            parent = item.parent()
            if parent:
                self.tree.blockSignals(True)
                try:
                    # 统计子节点选中情况
                    checked_count = 0
                    total_count = 0
                    for i in range(parent.childCount()):
                        child = parent.child(i)
                        total_count += 1
                        if child.checkState(0) == Qt.Checked:
                            checked_count += 1
                    
                    # 设置父节点状态
                    if checked_count == 0:
                        parent.setCheckState(0, Qt.Unchecked)
                    elif checked_count == total_count:
                        parent.setCheckState(0, Qt.Checked)
                    else:
                        parent.setCheckState(0, Qt.PartiallyChecked)
                finally:
                    self.tree.blockSignals(False)
        
        self.selection_changed.emit()
    
    def select_all(self):
        """全选"""
        self.tree.blockSignals(True)
        try:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                item.setCheckState(0, Qt.Checked)
                data = item.data(0, Qt.UserRole)
                if data and data.get("type") == "table":
                    for j in range(item.childCount()):
                        child = item.child(j)
                        child.setCheckState(0, Qt.Checked)
                        child_data = child.data(0, Qt.UserRole)
                        if child_data and child_data.get("type") == "diff":
                            child_data["diff"].selected = True
        finally:
            self.tree.blockSignals(False)
        self.selection_changed.emit()
    
    def deselect_all(self):
        """取消全选"""
        self.tree.blockSignals(True)
        try:
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                item.setCheckState(0, Qt.Unchecked)
                data = item.data(0, Qt.UserRole)
                if data and data.get("type") == "table":
                    for j in range(item.childCount()):
                        child = item.child(j)
                        child.setCheckState(0, Qt.Unchecked)
                        child_data = child.data(0, Qt.UserRole)
                        if child_data and child_data.get("type") == "diff":
                            child_data["diff"].selected = False
        finally:
            self.tree.blockSignals(False)
        self.selection_changed.emit()
    
    def get_selected_diffs(self) -> list[DiffResult]:
        """获取选中的差异"""
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            table_item = self.tree.topLevelItem(i)
            for j in range(table_item.childCount()):
                child = table_item.child(j)
                data = child.data(0, Qt.UserRole)
                if data and data.get("type") == "diff" and child.checkState(0) == Qt.Checked:
                    selected.append(data["diff"])
        return selected
    
    def apply_filters(self):
        """应用筛选"""
        type_filter = self.type_filter.currentText()
        action_filter = self.action_filter.currentText()
        search_text = self.search_input.text().lower()
        
        for i in range(self.tree.topLevelItemCount()):
            table_item = self.tree.topLevelItem(i)
            visible = 0
            
            for j in range(table_item.childCount()):
                child = table_item.child(j)
                data = child.data(0, Qt.UserRole)
                if not data or data.get("type") != "diff":
                    continue
                
                diff = data["diff"]
                show = True
                
                # 类型筛选
                if type_filter == "仅表" and "TABLE" in diff.diff_type.name:
                    show = True
                elif type_filter != "全部类型":
                    if type_filter == "仅表" or \
                       (type_filter == "仅索引" and "INDEX" not in diff.diff_type.name) or \
                       (type_filter == "仅外键" and "FOREIGN_KEY" not in diff.diff_type.name):
                        show = False
                
                # 操作筛选
                if action_filter != "全部操作":
                    action = diff.diff_type.name.split("_")[0]
                    if (action_filter == "仅新增" and action != "NEW") or \
                       (action_filter == "仅修改" and action != "MODIFY") or \
                       (action_filter == "仅删除" and action != "DROP"):
                        show = False
                
                # 搜索
                if search_text and search_text not in diff.table_name.lower() and search_text not in diff.object_name.lower():
                    show = False
                
                child.setHidden(not show)
                if show:
                    visible += 1
            
            table_item.setHidden(visible == 0)
