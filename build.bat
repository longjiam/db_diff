@echo off
echo ========================================
echo Database Diff Tool - Build Script
echo ========================================
echo.

echo Installing dependencies...
pip install -r requirements.txt
echo.

echo Building executable with PyInstaller...
pyinstaller --onedir ^
    --windowed ^
    --name "DBDiffTool" ^
    --icon=NONE ^
    --add-data "src/ui;src/ui" ^
    --add-data "src/core;src/core" ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=sqlalchemy ^
    --hidden-import=pymysql ^
    --hidden-import=psycopg2 ^
    main.py

echo.
echo ========================================
echo Build complete!
echo Output: dist\DBDiffTool.exe
echo ========================================
pause
