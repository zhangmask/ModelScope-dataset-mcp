@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo ModelScope MCP Server Demo
echo ========================================
echo.
echo This demo will show:
echo 1. Environment check and dependency installation
echo 2. Auto start MCP server
echo 3. Chinese dataset query functionality
echo 4. Real API call effects
echo.
pause

echo ========================================
echo Step 1: Check Python Environment
echo ========================================
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python 3.8+
    pause
    exit /b 1
) else (
    echo [SUCCESS] Python environment check passed
    python --version
)
echo.

echo ========================================
echo Step 2: Install Dependencies
echo ========================================
echo Installing required packages...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [WARNING] Dependency installation may have issues, but continuing demo
) else (
    echo [SUCCESS] Dependencies installed successfully
)
echo.

echo ========================================
echo Step 3: Check and Start MCP Server
echo ========================================
echo Checking if MCP server is already running...
netstat -an | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo [INFO] MCP server not running, starting now...
    start /b python src/modelscope_mcp/server.py >server.log 2>&1
    echo Waiting for server startup...
    timeout /t 5 /nobreak >nul
    echo [SUCCESS] MCP server started in background
) else (
    echo [INFO] MCP server is already running on port 8000
)
echo.

echo ========================================
echo Step 4: Demo Chinese Dataset Query
echo ========================================
echo.
echo Now demonstrating MCP server Chinese dataset query:
echo.
echo 1. Query datasets containing "Chinese" keywords
echo 2. Use natural language query "find some Chinese dialogue data"
echo 3. Show query results and relevance scores
echo.
pause

echo ----------------------------------------
echo Executing query demo...
echo ----------------------------------------

echo Executing Chinese dataset query demo...
echo This will demonstrate MCP server calling AI model for Chinese dataset search
echo ========================================
echo DEMO OUTPUT START
echo ========================================
python demo_simple.py
if errorlevel 1 (
    echo ========================================
    echo DEMO OUTPUT END (WITH ERRORS)
    echo ========================================
    echo [WARNING] Demo script encountered issues
    echo Please check the error messages above
    echo You can manually run: python demo_simple.py
) else (
    echo ========================================
    echo DEMO OUTPUT END (SUCCESS)
    echo ========================================
    echo [SUCCESS] Chinese dataset query demo completed successfully
)

echo.
echo ========================================
echo Demo Summary
echo ========================================
echo.
echo ModelScope MCP Server Features:
echo + Support Chinese natural language queries
echo + Intelligent semantic understanding and matching
echo + Real-time database search
echo + Relevance scoring and ranking
echo + Flexible API interface
echo + High-performance caching mechanism
echo.
echo Technical Architecture:
echo - Python FastAPI backend
echo - SQLite database storage
echo - SiliconFlow AI semantic understanding
echo - Redis cache acceleration
echo - MCP protocol standard
echo.
echo Application Scenarios:
echo - AI model training data search
echo - Dataset intelligent recommendation
echo - Research resource discovery
echo - Automated data pipeline
echo.
echo Demo completed! Press any key to exit...
pause >nul

echo Cleaning temporary files...
if exist server.log del server.log

echo Thank you for using ModelScope MCP Server demo!
exit /b 0