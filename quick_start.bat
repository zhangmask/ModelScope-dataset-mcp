@echo off
chcp 65001 >nul

echo ========================================
echo   ModelScope MCP Server Quick Start
echo ========================================
echo.

echo [STEP 1/5] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed or not in PATH
    echo Please install Python 3.8+ and add to system PATH
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% installed

echo.
echo [STEP 2/5] Checking dependencies...
python -c "import sqlalchemy, aiohttp, pydantic" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Missing required dependencies, installing automatically...
    call install_deps.bat
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed
        pause
        exit /b 1
    )
) else (
    echo [SUCCESS] Core dependencies installed
)

echo.
echo [STEP 3/5] Checking configuration file...
if not exist "config.json" (
    echo [WARN] Configuration file not found, creating default config...
    (
        echo {
        echo   "siliconflow": {
        echo     "api_key": "YOUR_API_KEY_HERE",
        echo     "api_url": "https://api.siliconflow.cn/v1/chat/completions"
        echo   },
        echo   "database": {
        echo     "url": "sqlite:///data/modelscope_mcp.db"
        echo   },
        echo   "cache": {
        echo     "type": "memory",
        echo     "redis_url": "redis://localhost:6379/0",
        echo     "enabled": false
        echo   },
        echo   "logging": {
        echo     "level": "INFO",
        echo     "file": "logs/modelscope_mcp.log"
        echo   }
        echo }
    ) > config.json
    echo [SUCCESS] Default configuration file created
    echo [WARN] Please edit config.json to configure your SiliconFlow API key
else (
    echo [SUCCESS] Configuration file exists
)

echo.
echo [STEP 4/5] Creating necessary directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache
echo [SUCCESS] Directory structure ready

echo.
echo [STEP 5/5] Starting MCP server...
echo [INFO] Starting server, please wait...
echo [INFO] Server will start at http://localhost:8000
echo [INFO] Press Ctrl+C to stop server
echo.
echo ========================================
echo           Server Starting...
echo ========================================
echo.

:: Start server
python src/modelscope_mcp/server.py

:: If server exits unexpectedly
echo.
echo ========================================
echo           Server Stopped
echo ========================================
echo.
echo [INFO] If you encounter problems, please check:
echo 1. Configuration file correctness (config.json)
echo 2. Dependencies completely installed
echo 3. Port 8000 not occupied
echo 4. Check log file: logs/modelscope_mcp.log
echo.
echo Tip: Run menu.bat to use graphical management interface
echo.
pause