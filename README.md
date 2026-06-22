# 数据库结构对比同步工具 (DB Diff Tool)

一个基于 PySide6 的跨平台数据库结构对比和同步工具，支持 MySQL 和 PostgreSQL。

## 功能特性

### 核心功能
- **数据库结构对比**：并行提取两个数据库的结构，快速找出差异
- **可视化差异展示**：树形结构展示表、字段、索引、外键的差异
- **SQL 自动生成**：根据勾选的差异项自动生成同步 SQL
- **SQL 语法高亮**：支持 MySQL、PostgreSQL 等不同数据库的关键字高亮
- **SQL 执行**：直接在目标数据库执行生成的同步 SQL

### 支持的数据库对象
- 表（Table）
- 字段（Column）
- 索引（Index）
- 外键（Foreign Key）
- 视图（View）
- 存储过程（Procedure）
- 触发器（Trigger）

### 数据库支持
- ✅ MySQL
- ✅ PostgreSQL
- 🔜 SQL Server（规划中）

### UI 特性
- 🌓 白天/黑夜主题切换
- 📊 四标签页界面（数据库配置、差异对比、SQL 预览、运行日志）
- 📋 对比任务管理（保存/加载对比配置）
- 🎯 精确勾选（支持只选择部分字段/索引生成 SQL）
- 📈 实时进度反馈

## 截图

![界面预览](assets/screenshot.png)

## 快速开始

### 环境要求
- Python 3.9+
- Windows / macOS / Linux

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python -m src.main
```

## 使用说明

### 1. 配置数据库连接

在「数据库配置」标签页：
- 选择数据库类型（MySQL / PostgreSQL）
- 填写连接信息（主机、端口、用户名、密码、数据库名）
- 点击「测试连接」验证配置

### 2. 执行对比

- 配置好源数据库（A）和目标数据库（B）
- 点击「▶ 开始对比」按钮
- 程序会并行提取两个数据库的结构并对比

### 3. 查看差异

在「差异对比」标签页：
- 树形列表展示所有差异项
- 支持全选/取消全选
- 可以展开表节点，精确选择字段/索引/外键
- 表节点支持半选状态（部分子项被选中）

### 4. 预览和生成 SQL

在「SQL 预览」标签页：
- 自动根据勾选的差异项生成 SQL
- 支持语法高亮（根据数据库类型显示不同颜色）
- 可以复制 SQL 到剪贴板
- 可以导出为 .sql 文件

### 5. 执行 SQL

- 点击「执行 SQL」按钮
- 在目标数据库执行生成的同步 SQL
- 实时查看执行进度和结果

### 6. 任务管理

点击工具栏的「📋 任务管理」按钮：
- 保存当前对比配置（方便下次使用）
- 加载已保存的任务配置
- 双击任务列表项快速加载并关闭

## 项目结构

```
db_diff_client/
├── src/
│   ├── main.py                 # 主程序入口
│   ├── core/                   # 核心逻辑
│   │   ├── adapters/           # 数据库适配器
│   │   │   ├── base.py         # 基础适配器
│   │   │   ├── mysql.py        # MySQL 适配器
│   │   │   └── postgresql.py   # PostgreSQL 适配器
│   │   ├── db_connector.py     # 数据库连接管理
│   │   ├── schema_extractor.py # 结构提取器
│   │   ├── diff_engine.py      # 差异对比引擎
│   │   ├── sql_generator.py    # SQL 生成器
│   │   ├── task_storage.py     # 任务持久化
│   │   ├── connection_storage.py # 连接配置持久化
│   │   └── theme_manager.py    # 主题管理器
│   └── ui/                     # 界面组件
│       ├── db_config_panel.py  # 数据库配置面板
│       ├── diff_viewer.py      # 差异查看器
│       ├── sql_preview_panel.py # SQL 预览面板
│       ├── sql_highlighter.py  # SQL 语法高亮器
│       ├── log_panel.py        # 日志面板
│       └── task_manager_panel.py # 任务管理面板
├── main.py                     # PyInstaller 打包入口
├── build.bat                   # Windows 打包脚本
├── requirements.txt            # Python 依赖
└── README.md                   # 项目文档
```

## 打包发布

### Windows 打包

双击运行 `build.bat` 或在命令行执行：

```bash
build.bat
```

打包完成后，可执行文件位于 `dist/DBDiffTool/DBDiffTool.exe`

### 打包模式

项目使用 `--onedir` 模式打包（文件夹模式），优点是启动速度快。

如需单文件打包（`--onefile`），修改 `build.bat` 中的 `--onedir` 为 `--onefile`，但启动会较慢（需要解压）。

## 快捷键

- `Ctrl+D` - 开始对比
- `Ctrl+E` - 导出 SQL
- `Ctrl+Q` - 退出程序
- `Ctrl+T` - 切换主题

## 技术栈

- **GUI 框架**：PySide6 (Qt6)
- **数据库**：SQLAlchemy
- **MySQL 驱动**：PyMySQL
- **PostgreSQL 驱动**：psycopg2-binary
- **打包工具**：PyInstaller

## 开发说明

### 添加新的数据库支持

1. 在 `src/core/adapters/` 下创建新的适配器文件（如 `sqlserver.py`）
2. 继承 `BaseDBAdapter` 类，实现所有抽象方法
3. 在 `src/core/adapters/registry.py` 中注册新适配器

### 主题定制

在 `src/core/theme_manager.py` 中修改颜色配置：
- `DARK_THEME` - 黑夜主题
- `LIGHT_THEME` - 白天主题

## 注意事项

- ⚠️ 执行 SQL 前请备份目标数据库
- ⚠️ 对比任务配置保存在本地 `connections.json` 文件中
- ⚠️ 大数据库对比可能需要较长时间，请耐心等待

## 许可证

MIT License

## 作者

开发于 2026 年
