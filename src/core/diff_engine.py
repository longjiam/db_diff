from dataclasses import dataclass
from enum import Enum
from typing import Optional
from .schema_extractor import TableSchema


class DiffType(str, Enum):
    """差异类型枚举"""
    NEW_TABLE = "新增表"
    DROP_TABLE = "删除表"
    NEW_COLUMN = "新增字段"
    MODIFY_COLUMN = "修改字段"
    DROP_COLUMN = "删除字段"
    NEW_INDEX = "新增索引"
    DROP_INDEX = "删除索引"
    MODIFY_INDEX = "修改索引"
    NEW_FOREIGN_KEY = "新增外键"
    DROP_FOREIGN_KEY = "删除外键"
    MODIFY_FOREIGN_KEY = "修改外键"
    NEW_VIEW = "新增视图"
    DROP_VIEW = "删除视图"
    MODIFY_VIEW = "修改视图"
    NEW_PROCEDURE = "新增存储过程"
    DROP_PROCEDURE = "删除存储过程"
    MODIFY_PROCEDURE = "修改存储过程"
    NEW_TRIGGER = "新增触发器"
    DROP_TRIGGER = "删除触发器"
    MODIFY_TRIGGER = "修改触发器"


@dataclass
class DiffResult:
    """差异结果"""
    diff_type: DiffType
    table_name: str
    object_name: str  # 字段名/索引名/外键名
    source_value: Optional[str] = None  # 源库值
    target_value: Optional[str] = None  # 目标库值
    description: str = ""
    selected: bool = True  # 是否勾选同步
    source_schema: Optional['TableSchema'] = None  # 源表完整结构（用于 NEW_TABLE）
    target_schema: Optional['TableSchema'] = None  # 目标表完整结构（用于 DROP_TABLE）
    source_column: Optional[dict] = None  # 源字段完整信息（用于 NEW_COLUMN/MODIFY_COLUMN）
    target_column: Optional[dict] = None  # 目标字段完整信息（用于 DROP_COLUMN/MODIFY_COLUMN）
    source_definition: Optional[str] = None  # 源对象定义（用于视图/存储过程/触发器）
    target_definition: Optional[str] = None  # 目标对象定义（用于视图/存储过程/触发器）


class DiffEngine:
    """差异对比引擎"""
    
    def compare(self, source_schema: list[TableSchema], 
                target_schema: list[TableSchema],
                source_views: list[dict] = None,
                target_views: list[dict] = None,
                source_procedures: list[dict] = None,
                target_procedures: list[dict] = None,
                source_triggers: list[dict] = None,
                target_triggers: list[dict] = None) -> list[DiffResult]:
        """对比两个数据库的结构差异
        
        Args:
            source_schema: 源库表结构列表
            target_schema: 目标库表结构列表
            source_views: 源库视图列表
            target_views: 目标库视图列表
            source_procedures: 源库存储过程列表
            target_procedures: 目标库存储过程列表
            source_triggers: 源库触发器列表
            target_triggers: 目标库触发器列表
            
        Returns:
            差异结果列表
        """
        source_tables = {t.name: t for t in source_schema}
        target_tables = {t.name: t for t in target_schema}
        
        results = []
        
        # 新增表（源库有，目标库没有）—— 同时列出所有字段/索引/外键
        for table_name in source_tables:
            if table_name not in target_tables:
                source_table = source_tables[table_name]
                results.append(DiffResult(
                    diff_type=DiffType.NEW_TABLE,
                    table_name=table_name,
                    object_name=table_name,
                    description=f"目标库中不存在表: {table_name}",
                    source_schema=source_table,  # 传递完整表结构
                ))
                # 列出新增表的所有字段
                for col in source_table.columns:
                    results.append(DiffResult(
                        diff_type=DiffType.NEW_COLUMN,
                        table_name=table_name,
                        object_name=col['name'],
                        source_value=self._format_column(col),
                        description=f"新增表字段: {col['name']}",
                        source_column=col,
                    ))
                # 列出新增表的所有索引
                for idx in source_table.indexes:
                    results.append(DiffResult(
                        diff_type=DiffType.NEW_INDEX,
                        table_name=table_name,
                        object_name=idx['name'],
                        source_value=str(idx['columns']),
                        description=f"新增表索引: {idx['name']}",
                        source_schema=source_table,
                    ))
                # 列出新增表的所有外键
                for fk in source_table.foreign_keys:
                    results.append(DiffResult(
                        diff_type=DiffType.NEW_FOREIGN_KEY,
                        table_name=table_name,
                        object_name=fk['name'],
                        source_value=f"{fk['columns']} -> {fk['ref_table']}.{fk['ref_columns']}",
                        description=f"新增表外键: {fk['name']}",
                        source_schema=source_table,
                    ))
        
        # 删除表（目标库有，源库没有）—— 同时列出所有字段/索引/外键
        for table_name in target_tables:
            if table_name not in source_tables:
                target_table = target_tables[table_name]
                results.append(DiffResult(
                    diff_type=DiffType.DROP_TABLE,
                    table_name=table_name,
                    object_name=table_name,
                    description=f"源库中不存在表: {table_name}",
                    target_schema=target_table,  # 传递完整表结构
                ))
                # 列出被删除表的所有字段
                for col in target_table.columns:
                    results.append(DiffResult(
                        diff_type=DiffType.DROP_COLUMN,
                        table_name=table_name,
                        object_name=col['name'],
                        target_value=self._format_column(col),
                        description=f"删除表字段: {col['name']}",
                        target_column=col,
                    ))
                # 列出被删除表的所有索引
                for idx in target_table.indexes:
                    results.append(DiffResult(
                        diff_type=DiffType.DROP_INDEX,
                        table_name=table_name,
                        object_name=idx['name'],
                        target_value=str(idx['columns']),
                        description=f"删除表索引: {idx['name']}",
                        target_schema=target_table,
                    ))
                # 列出被删除表的所有外键
                for fk in target_table.foreign_keys:
                    results.append(DiffResult(
                        diff_type=DiffType.DROP_FOREIGN_KEY,
                        table_name=table_name,
                        object_name=fk['name'],
                        target_value=f"{fk['columns']} -> {fk['ref_table']}.{fk['ref_columns']}",
                        description=f"删除表外键: {fk['name']}",
                        target_schema=target_table,
                    ))
        
        # 对比共同存在的表
        for table_name in source_tables:
            if table_name in target_tables:
                source_table = source_tables[table_name]
                target_table = target_tables[table_name]
                
                # 对比字段
                results.extend(self._compare_columns(table_name, source_table, target_table))
                
                # 对比索引
                results.extend(self._compare_indexes(table_name, source_table, target_table))
                
                # 对比外键
                results.extend(self._compare_foreign_keys(table_name, source_table, target_table))
        
        # 对比视图
        if source_views is not None and target_views is not None:
            results.extend(self._compare_objects(
                DiffType.NEW_VIEW, DiffType.DROP_VIEW, DiffType.MODIFY_VIEW,
                "视图", source_views, target_views
            ))
        
        # 对比存储过程
        if source_procedures is not None and target_procedures is not None:
            results.extend(self._compare_objects(
                DiffType.NEW_PROCEDURE, DiffType.DROP_PROCEDURE, DiffType.MODIFY_PROCEDURE,
                "存储过程", source_procedures, target_procedures
            ))
        
        # 对比触发器
        if source_triggers is not None and target_triggers is not None:
            results.extend(self._compare_objects(
                DiffType.NEW_TRIGGER, DiffType.DROP_TRIGGER, DiffType.MODIFY_TRIGGER,
                "触发器", source_triggers, target_triggers
            ))
        
        return results
    
    def _compare_columns(self, table_name: str, 
                         source: TableSchema, 
                         target: TableSchema) -> list[DiffResult]:
        source_cols = {c["name"]: c for c in source.columns}
        target_cols = {c["name"]: c for c in target.columns}
        
        results = []
        
        # 新增字段
        for col_name in source_cols:
            if col_name not in target_cols:
                results.append(DiffResult(
                    diff_type=DiffType.NEW_COLUMN,
                    table_name=table_name,
                    object_name=col_name,
                    source_value=self._format_column(source_cols[col_name]),
                    description=f"新增字段: {col_name}",
                    source_column=source_cols[col_name],  # 传递完整字段信息
                ))
        
        # 删除字段
        for col_name in target_cols:
            if col_name not in source_cols:
                results.append(DiffResult(
                    diff_type=DiffType.DROP_COLUMN,
                    table_name=table_name,
                    object_name=col_name,
                    target_value=self._format_column(target_cols[col_name]),
                    description=f"删除字段: {col_name}",
                    target_column=target_cols[col_name],  # 传递完整字段信息
                ))
        
        # 修改字段
        for col_name in source_cols:
            if col_name in target_cols:
                src_col = source_cols[col_name]
                tgt_col = target_cols[col_name]
                
                if self._column_differs(src_col, tgt_col):
                    results.append(DiffResult(
                        diff_type=DiffType.MODIFY_COLUMN,
                        table_name=table_name,
                        object_name=col_name,
                        source_value=self._format_column(src_col),
                        target_value=self._format_column(tgt_col),
                        description=f"修改字段: {col_name}",
                        source_column=src_col,  # 传递完整字段信息
                        target_column=tgt_col,  # 传递完整字段信息
                    ))
        
        return results
    
    def _compare_indexes(self, table_name: str,
                         source: TableSchema,
                         target: TableSchema) -> list[DiffResult]:
        source_idx = {i["name"]: i for i in source.indexes}
        target_idx = {i["name"]: i for i in target.indexes}
        
        results = []
        
        # 新增索引
        for idx_name in source_idx:
            if idx_name not in target_idx:
                results.append(DiffResult(
                    diff_type=DiffType.NEW_INDEX,
                    table_name=table_name,
                    object_name=idx_name,
                    source_value=str(source_idx[idx_name]["columns"]),
                    description=f"新增索引: {idx_name}",
                    source_schema=source,  # 传递完整表结构以获取索引信息
                ))
        
        # 删除索引
        for idx_name in target_idx:
            if idx_name not in source_idx:
                results.append(DiffResult(
                    diff_type=DiffType.DROP_INDEX,
                    table_name=table_name,
                    object_name=idx_name,
                    target_value=str(target_idx[idx_name]["columns"]),
                    description=f"删除索引: {idx_name}",
                    target_schema=target,  # 传递完整表结构以获取索引信息
                ))
        
        # 修改索引(对比字段或唯一性是否变化)
        for idx_name in source_idx:
            if idx_name in target_idx:
                src_idx = source_idx[idx_name]
                tgt_idx = target_idx[idx_name]
                
                # 对比索引的字段和唯一性
                if (src_idx.get('columns') != tgt_idx.get('columns') or
                    src_idx.get('unique') != tgt_idx.get('unique')):
                    
                    results.append(DiffResult(
                        diff_type=DiffType.MODIFY_INDEX,
                        table_name=table_name,
                        object_name=idx_name,
                        source_value=str(src_idx['columns']),
                        target_value=str(tgt_idx['columns']),
                        description=f"修改索引: {idx_name}",
                        source_schema=source,  # 传递完整表结构
                        target_schema=target,  # 传递完整表结构
                    ))
        
        return results
    
    def _compare_foreign_keys(self, table_name: str,
                              source: TableSchema,
                              target: TableSchema) -> list[DiffResult]:
        source_fks = {f["name"]: f for f in source.foreign_keys}
        target_fks = {f["name"]: f for f in target.foreign_keys}
        
        results = []
        
        # 新增外键
        for fk_name in source_fks:
            if fk_name not in target_fks:
                results.append(DiffResult(
                    diff_type=DiffType.NEW_FOREIGN_KEY,
                    table_name=table_name,
                    object_name=fk_name,
                    source_value=f"{source_fks[fk_name]['columns']} -> {source_fks[fk_name]['ref_table']}.{source_fks[fk_name]['ref_columns']}",
                    description=f"新增外键: {fk_name}",
                    source_schema=source,  # 传递完整表结构以获取外键信息
                ))
        
        # 删除外键
        for fk_name in target_fks:
            if fk_name not in source_fks:
                results.append(DiffResult(
                    diff_type=DiffType.DROP_FOREIGN_KEY,
                    table_name=table_name,
                    object_name=fk_name,
                    target_value=f"{target_fks[fk_name]['columns']} -> {target_fks[fk_name]['ref_table']}.{target_fks[fk_name]['ref_columns']}",
                    description=f"删除外键: {fk_name}",
                    target_schema=target,  # 传递完整表结构以获取外键信息
                ))
        
        # 修改外键(对比引用关系是否变化)
        for fk_name in source_fks:
            if fk_name in target_fks:
                src_fk = source_fks[fk_name]
                tgt_fk = target_fks[fk_name]
                
                # 对比外键的各个属性
                if (src_fk.get('columns') != tgt_fk.get('columns') or
                    src_fk.get('ref_table') != tgt_fk.get('ref_table') or
                    src_fk.get('ref_columns') != tgt_fk.get('ref_columns') or
                    src_fk.get('on_delete') != tgt_fk.get('on_delete') or
                    src_fk.get('on_update') != tgt_fk.get('on_update')):
                    
                    results.append(DiffResult(
                        diff_type=DiffType.MODIFY_FOREIGN_KEY,
                        table_name=table_name,
                        object_name=fk_name,
                        source_value=f"{src_fk['columns']} -> {src_fk['ref_table']}.{src_fk['ref_columns']}",
                        target_value=f"{tgt_fk['columns']} -> {tgt_fk['ref_table']}.{tgt_fk['ref_columns']}",
                        description=f"修改外键: {fk_name}",
                        source_schema=source,  # 传递完整表结构
                        target_schema=target,  # 传递完整表结构
                    ))
        
        return results
    
    def _column_differs(self, src: dict, tgt: dict) -> bool:
        """判断两个字段是否有差异"""
        return (
            src.get("type") != tgt.get("type") or
            src.get("nullable") != tgt.get("nullable") or
            str(src.get("default")) != str(tgt.get("default")) or
            src.get("comment") != tgt.get("comment")  # 对比注释
        )
    
    def _format_column(self, col: dict) -> str:
        """格式化字段信息为字符串"""
        parts = [col["type"]]
        if not col.get("nullable", True):
            parts.append("NOT NULL")
        if col.get("default") is not None:
            parts.append(f"DEFAULT {col['default']}")
        return " ".join(parts)
    
    def _compare_objects(self, new_type: DiffType, drop_type: DiffType, modify_type: DiffType,
                        object_type_name: str, source_objects: list[dict], 
                        target_objects: list[dict]) -> list[DiffResult]:
        """通用对象对比方法（用于视图、存储过程、触发器）"""
        source_objs = {o["name"]: o for o in source_objects}
        target_objs = {o["name"]: o for o in target_objects}
        
        results = []
        
        # 新增对象
        for obj_name in source_objs:
            if obj_name not in target_objs:
                results.append(DiffResult(
                    diff_type=new_type,
                    table_name="",
                    object_name=obj_name,
                    source_value=object_type_name,
                    source_definition=source_objs[obj_name].get("definition", ""),
                    description=f"新增{object_type_name}: {obj_name}",
                ))
        
        # 删除对象
        for obj_name in target_objs:
            if obj_name not in source_objs:
                results.append(DiffResult(
                    diff_type=drop_type,
                    table_name="",
                    object_name=obj_name,
                    target_value=object_type_name,
                    target_definition=target_objs[obj_name].get("definition", ""),
                    description=f"删除{object_type_name}: {obj_name}",
                ))
        
        # 修改对象
        for obj_name in source_objs:
            if obj_name in target_objs:
                src_def = source_objs[obj_name].get("definition", "").strip()
                tgt_def = target_objs[obj_name].get("definition", "").strip()
                
                if src_def != tgt_def:
                    results.append(DiffResult(
                        diff_type=modify_type,
                        table_name="",
                        object_name=obj_name,
                        source_value=object_type_name,
                        target_value=object_type_name,
                        source_definition=src_def,
                        target_definition=tgt_def,
                        description=f"修改{object_type_name}: {obj_name}",
                    ))
        
        return results
