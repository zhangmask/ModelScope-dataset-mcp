@echo off
chcp 65001 >nul
echo ========================================
echo    ModelScope MCP Server Dependencies
echo ========================================
echo.

echo [INFO] Checking Python environment...
python --version
if errorlevel 1 (
    echo [ERROR] Python not installed or not in PATH
    echo Please install Python 3.8+
    pause
    exit /b 1
)

echo.
echo [INFO] Upgrading pip to latest version...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARN] pip upgrade failed, continuing with dependency installation
)

echo.
echo [INFO] Installing project dependencies...
echo Installing core dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Core dependencies installation failed
    pause
    exit /b 1
)

echo.
echo [INFO] Installing development dependencies...
if exist "requirements-dev.txt" (
    pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo [WARN] Development dependencies installation failed, but core functionality not affected
    )
) else (
    echo [INFO] Development dependencies file not found, skipping
)

echo.
echo [INFO] Verifying key dependencies...
echo Checking SQLAlchemy...
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__} installed')"
if errorlevel 1 (
    echo [ERROR] SQLAlchemy verification failed
    pause
    exit /b 1
)

echo Checking aiohttp...
python -c "import aiohttp; print(f'aiohttp {aiohttp.__version__} installed')"
if errorlevel 1 (
    echo [ERROR] aiohttp verification failed
    pause
    exit /b 1
)

echo Checking pydantic...
python -c "import pydantic; print(f'pydantic {pydantic.__version__} installed')"
if errorlevel 1 (
    echo [ERROR] pydantic verification failed
    pause
    exit /b 1
)

echo.
echo [SUCCESS] All dependencies installed successfully!
echo.
echo Next steps:
echo 1. Edit config.json file to configure your API key
echo 2. Run start_server.bat to start the server
echo 3. Run test_all.bat to verify functionality
echo.
pause