# 完善 SQL 生成、视图对比和 UI 折叠功能

## Context

用户需要 SQL 预览能生成可直接执行的完整 SQL(包括表、索引、视图等所有对象),并且树形对比默认折叠以提升浏览体验。

### 当前问题
1. **SQL 生成不完整**: NEW_TABLE/NEW_INDEX/NEW_FOREIGN_KEY 只输出注释,无可执行 SQL
2. **索引修改未实现**: MODIFY_INDEX 未被创建,相同名称索引的属性差异被忽略
3. **缺少视图对比**: 无视图提取、对比和 SQL 生成
4. **树默认展开**: 差异多时不易浏览

### 设计决策
- **索引修改策略**: DROP + CREATE (MySQL/PostgreSQL 均不支持 ALTER INDEX)
- **视图范围**: 普通视图 + 物化视图 (PostgreSQL 支持 MATERIALIZED VIEW)
- **表结构**: 传递完整 TableSchema,生成完整 CREATE TABLE

## 实施方案

### 一、扩展 DiffResult 传递完整结构

**文件**: `src/core/diff_engine.py`

修改 DiffResult 数据类:
```python
@dataclass
class DiffResult:
    diff_type: DiffType
    table_name: str
    object_name: str
    source_value: Optional[str] = None
    target_value: Optional[str] = None
    description: str = ""
    selected: bool = True
    source_schema: Optional[TableSchema] = None  # 源表完整结构
    target_schema: Optional[TableSchema] = None  # 目标表完整结构
```

在 `_compare_tables()` 和 `_compare_indexes()` 中传递完整 schema 引用。

### 二、添加视图支持

#### 2.1 扩展 TableSchema

**文件**: `src/core/schema_extractor.py`

```python
@dataclass
class TableSchema:
    name: str
    columns: list[dict]
    indexes: list[dict]
    foreign_keys: list[dict]
    views: list[dict] = field(default_factory=list)  # 新增
```

#### 2.2 适配器添加视图方法

**文件**: `src/core/adapters/base.py`, `mysql.py`, `postgresql.py`

添加抽象方法:
```python
@abstractmethod
def get_views(self, conn) -> list[dict]:
    """获取所有视图列表,包含 name, definition, is_materialized"""

@abstractmethod
def generate_create_view_sql(self, view: dict) -> str:
    """生成 CREATE VIEW SQL"""

@abstractmethod  
def generate_drop_view_sql(self, view_name: str) -> str:
    """生成 DROP VIEW SQL"""
```

MySQL 实现:
- `SHOW FULL TABLES WHERE TABLE_TYPE = 'VIEW'`
- `SHOW CREATE VIEW view_name`
- MySQL 不支持物化视图

PostgreSQL 实现:
- `SELECT * FROM pg_views WHERE schemaname = 'public'`
- `SELECT * FROM pg_matviews WHERE schemaname = 'public'`
- 支持 MATERIALIZED VIEW

#### 2.3 DiffEngine 添加视图对比

**文件**: `src/core/diff_engine.py`

添加 DiffType:
```python
NEW_VIEW = "新增视图"
DROP_VIEW = "删除视图"  
MODIFY_VIEW = "修改视图"
```

添加 `_compare_views(source_schemas, target_schemas)` 方法:
- 比较视图名称
- 比较视图定义(SQL)
- 检测新增/删除/修改的视图

### 三、完善 SQL 生成

**文件**: `src/core/sql_generator.py`

重构 `generate_sync_sql()` 方法:

| DiffType | 实现方式 |
|----------|----------|
| NEW_TABLE | 使用 `diff.source_schema`,调用 adapter.generate_create_table_sql() |
| NEW_INDEX | 从 `diff.source_schema.indexes` 找到索引,调用 adapter.generate_add_index_sql() |
| NEW_FOREIGN_KEY | 从 `diff.source_schema.foreign_keys` 找到 FK,调用 adapter.generate_add_fk_sql() |
| MODIFY_INDEX | 先 DROP 旧索引,再 CREATE 新索引 |
| NEW_VIEW | 调用 adapter.generate_create_view_sql() |
| DROP_VIEW | 调用 adapter.generate_drop_view_sql() |
| MODIFY_VIEW | 调用 adapter.generate_create_or_replace_view_sql() |

### 四、修复索引对比 Bug

**文件**: `src/core/diff_engine.py`

在 `_compare_indexes()` 中添加索引属性比较:
```python
def _index_differs(self, source_idx: dict, target_idx: dict) -> bool:
    """比较两个索引是否真正相同(列、唯一性、类型)"""
    if source_idx['columns'] != target_idx['columns']:
        return True
    if source_idx['unique'] != target_idx['unique']:
        return True
    return False
```

当索引名相同但属性不同时,生成 MODIFY_INDEX 差异。

### 五、树形表格默认折叠

**文件**: `src/ui/diff_viewer.py`

修改第 114 行:
```python
table_item.setExpanded(False)  # 从 True 改为 False
```

## 关键文件

- `src/core/diff_engine.py` - DiffResult 扩展,视图对比逻辑
- `src/core/schema_extractor.py` - TableSchema 扩展,视图提取
- `src/core/sql_generator.py` - 完整 SQL 生成
- `src/core/adapters/base.py` - 视图抽象方法
- `src/core/adapters/mysql.py` - MySQL 视图实现
- `src/core/adapters/postgresql.py` - PostgreSQL 视图实现
- `src/ui/diff_viewer.py` - 树折叠修改

## 验证方式

1. **树折叠**: 启动对比,树默认折叠,点击展开查看字段
2. **NEW_TABLE SQL**: 勾选新增表,SQL 预览显示完整 CREATE TABLE(含列、索引、外键)
3. **NEW_INDEX SQL**: 勾选新增索引,显示 CREATE INDEX 语句
4. **MODIFY_INDEX SQL**: 修改索引属性,显示 DROP + CREATE 语句
5. **NEW_VIEW SQL**: 勾选新增视图,显示 CREATE VIEW AS ...
6. **MODIFY_VIEW SQL**: 修改视图定义,显示 CREATE OR REPLACE VIEW AS ...
7. **导出执行**: 导出 SQL 文件,在目标库执行验证
