# Database Structure Diff & Sync Tool (DB Diff Tool)

A cross-platform database structure comparison and synchronization tool built with PySide6, supporting MySQL and PostgreSQL.

## Features

### Core Features
- **Database Structure Comparison**: Parallel extraction of two database structures for fast difference detection
- **Visual Difference Display**: Tree view showing differences in tables, columns, indexes, and foreign keys
- **Automatic SQL Generation**: Generate synchronization SQL based on selected differences
- **SQL Syntax Highlighting**: Keyword highlighting for different databases (MySQL, PostgreSQL, etc.)
- **SQL Execution**: Execute generated sync SQL directly on the target database

### Supported Database Objects
- Tables
- Columns
- Indexes
- Foreign Keys
- Views
- Procedures
- Triggers

### Database Support
- ✅ MySQL
- ✅ PostgreSQL
- 🔜 SQL Server (Planned)

### UI Features
- 🌓 Light/Dark Theme Toggle
- 📊 Four-Tab Interface (DB Config, Diff Viewer, SQL Preview, Log Panel)
- 📋 Task Management (Save/Load comparison configurations)
- 🎯 Precise Selection (Support selecting partial columns/indexes for SQL generation)
- 📈 Real-time Progress Feedback

## Screenshot

![Interface Preview](assets/screenshot.png)

## Quick Start

### Requirements
- Python 3.9+
- Windows / macOS / Linux

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python -m src.main
```

## Usage Guide

### 1. Configure Database Connections

In the "Database Configuration" tab:
- Select database type (MySQL / PostgreSQL)
- Enter connection details (host, port, username, password, database name)
- Click "Test Connection" to verify the configuration

### 2. Execute Comparison

- Configure source database (A) and target database (B)
- Click "▶ Start Comparison" button
- The program will parallelly extract both database structures and compare them

### 3. View Differences

In the "Diff Viewer" tab:
- Tree list displays all difference items
- Support select all / deselect all
- Expand table nodes to precisely select columns/indexes/foreign keys
- Table nodes support partially checked state (when some children are selected)

### 4. Preview and Generate SQL

In the "SQL Preview" tab:
- Automatically generate SQL based on selected differences
- Syntax highlighting (different colors based on database type)
- Copy SQL to clipboard
- Export as .sql file

### 5. Execute SQL

- Click "Execute SQL" button
- Execute generated sync SQL on the target database
- View execution progress and results in real-time

### 6. Task Management

Click "📋 Task Manager" button in the toolbar:
- Save current comparison configuration (for future use)
- Load saved task configurations
- Double-click task list item to quickly load and close

## Project Structure

```
db_diff_client/
├── src/
│   ├── main.py                 # Main application entry
│   ├── core/                   # Core logic
│   │   ├── adapters/           # Database adapters
│   │   │   ├── base.py         # Base adapter
│   │   │   ├── mysql.py        # MySQL adapter
│   │   │   └── postgresql.py   # PostgreSQL adapter
│   │   ├── db_connector.py     # Database connection management
│   │   ├── schema_extractor.py # Schema extractor
│   │   ├── diff_engine.py      # Difference comparison engine
│   │   ├── sql_generator.py    # SQL generator
│   │   ├── task_storage.py     # Task persistence
│   │   ├── connection_storage.py # Connection config persistence
│   │   └── theme_manager.py    # Theme manager
│   └── ui/                     # UI components
│       ├── db_config_panel.py  # Database configuration panel
│       ├── diff_viewer.py      # Difference viewer
│       ├── sql_preview_panel.py # SQL preview panel
│       ├── sql_highlighter.py  # SQL syntax highlighter
│       ├── log_panel.py        # Log panel
│       └── task_manager_panel.py # Task manager panel
├── main.py                     # PyInstaller packaging entry
├── build.bat                   # Windows build script
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation (Chinese)
└── README_EN.md                # Project documentation (English)
```

## Build & Distribution

### Windows Build

Double-click `build.bat` or run in command line:

```bash
build.bat
```

After building, the executable is located at `dist/DBDiffTool/DBDiffTool.exe`

### Build Modes

The project uses `--onedir` mode (folder mode) for fast startup.

For single-file packaging (`--onefile`), change `--onedir` to `--onefile` in `build.bat`, but startup will be slower (requires extraction).

## Keyboard Shortcuts

- `Ctrl+D` - Start comparison
- `Ctrl+E` - Export SQL
- `Ctrl+Q` - Quit application
- `Ctrl+T` - Toggle theme

## Tech Stack

- **GUI Framework**: PySide6 (Qt6)
- **Database ORM**: SQLAlchemy
- **MySQL Driver**: PyMySQL
- **PostgreSQL Driver**: psycopg2-binary
- **Packaging Tool**: PyInstaller

## Development Guide

### Adding New Database Support

1. Create a new adapter file under `src/core/adapters/` (e.g., `sqlserver.py`)
2. Inherit from `BaseDBAdapter` class and implement all abstract methods
3. Register the new adapter in `src/core/adapters/registry.py`

### Theme Customization

Modify color configurations in `src/core/theme_manager.py`:
- `DARK_THEME` - Dark theme
- `LIGHT_THEME` - Light theme

## Important Notes

- ⚠️ Always backup the target database before executing SQL
- ⚠️ Comparison task configurations are saved locally in `connections.json`
- ⚠️ Large database comparisons may take some time, please be patient

## License

MIT License

## Author

Developed in 2026
