@echo off
chcp 65001 >nul
echo ========================================
echo    ModelScope MCP Server Startup
echo ========================================
echo.

echo [INFO] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed or not in PATH
    echo Please install Python 3.8+
    pause
    exit /b 1
)

echo [INFO] Checking dependencies...
pip show sqlalchemy >nul 2>&1
if errorlevel 1 (
    echo [WARN] Dependencies not installed, installing...
    call install_deps.bat
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [INFO] Checking configuration file...
if not exist "config.json" (
    echo [WARN] Configuration file not found, creating...
    if exist "config.json.example" (
        copy "config.json.example" "config.json" >nul
        echo [INFO] Configuration file created from example
        echo [WARN] Please edit config.json to configure your API key
    ) else (
        echo [ERROR] Configuration example file not found
        pause
        exit /b 1
    )
)

echo [INFO] Creating necessary directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache

echo [INFO] Starting ModelScope MCP Server...
echo [INFO] Server will run in background
echo [INFO] Press Ctrl+C to stop server
echo.

python src/modelscope_mcp/server.py

if errorlevel 1 (
    echo.
    echo [ERROR] Server startup failed
    echo Please check configuration and log files
    pause
) else (
    echo.
    echo [INFO] Server stopped
)

pause