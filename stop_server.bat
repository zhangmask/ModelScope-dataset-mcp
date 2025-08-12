@echo off
chcp 65001 >nul
echo ========================================
echo    ModelScope MCP Server Stop Script
echo ========================================
echo.

echo [INFO] Finding ModelScope MCP server processes...

:: Find Python processes containing server.py
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "server.py"') do (
    set PID=%%i
    echo [INFO] Found server process PID: %%i
    taskkill /pid %%i /f
    if errorlevel 1 (
        echo [ERROR] Cannot stop process %%i
    ) else (
        echo [SUCCESS] Process %%i stopped
    )
)

:: Use wmic to find more precise processes
echo [INFO] Using advanced method to find processes...
for /f "tokens=2 delims=," %%i in ('wmic process where "name='python.exe' and commandline like '%%server.py%%'" get processid /format:csv ^| findstr /v "Node"') do (
    if not "%%i"=="" (
        echo [INFO] Found server process PID: %%i
        taskkill /pid %%i /f
        if errorlevel 1 (
            echo [ERROR] Cannot stop process %%i
        ) else (
            echo [SUCCESS] Process %%i stopped
        )
    )
)

:: Check port usage
echo.
echo [INFO] Checking port 8000 usage...
netstat -ano | findstr :8000
if errorlevel 1 (
    echo [INFO] Port 8000 is not in use
) else (
    echo [WARN] Port 8000 is still in use, may need manual handling
    echo Use the following command for details:
    echo netstat -ano ^| findstr :8000
)

echo.
echo [INFO] Cleaning temporary files...
if exist "*.pyc" del /q "*.pyc"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "src\modelscope_mcp\__pycache__" rmdir /s /q "src\modelscope_mcp\__pycache__"

echo.
echo [SUCCESS] ModelScope MCP server stopped
echo.
echo To restart the server, please run start_server.bat
echo.
pause