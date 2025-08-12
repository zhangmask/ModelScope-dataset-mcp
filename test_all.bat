@echo off
chcp 65001 >nul
echo ========================================
echo    ModelScope MCP Server Function Tests
echo ========================================
echo.

echo [INFO] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed or not in PATH
    pause
    exit /b 1
)

echo [INFO] Checking project files...
if not exist "src\modelscope_mcp\server.py" (
    echo [ERROR] Project files incomplete
    pause
    exit /b 1
)

echo [INFO] Checking configuration file...
if not exist "config.json" (
    echo [ERROR] Configuration file not found, please run start_server.bat first
    pause
    exit /b 1
)

echo.
echo ========================================
echo           Running Test Suite
echo ========================================
echo.

echo [TEST 1] Running simple MCP function test...
echo ----------------------------------------
python test_mcp_simple.py
if errorlevel 1 (
    echo [ERROR] MCP function test failed
    set TEST_FAILED=1
) else (
    echo [SUCCESS] MCP function test passed
)

echo.
echo [TEST 2] Running dataset query test...
echo ----------------------------------------
if exist "test_dataset_query.py" (
    python test_dataset_query.py
    if errorlevel 1 (
        echo [ERROR] Dataset query test failed
        set TEST_FAILED=1
    ) else (
        echo [SUCCESS] Dataset query test passed
    )
) else (
    echo [SKIP] Dataset query test file not found
)

echo.
echo [TEST 3] Running unit tests...
echo ----------------------------------------
if exist "tests" (
    python -m pytest tests/ -v
    if errorlevel 1 (
        echo [ERROR] Unit tests failed
        set TEST_FAILED=1
    ) else (
        echo [SUCCESS] Unit tests passed
    )
) else (
    echo [SKIP] Unit test directory not found
)

echo.
echo [TEST 4] Checking database connection...
echo ----------------------------------------
if exist "check_db.py" (
    python check_db.py
    if errorlevel 1 (
        echo [ERROR] Database connection test failed
        set TEST_FAILED=1
    ) else (
        echo [SUCCESS] Database connection normal
    )
) else (
    echo [SKIP] Database check script not found
)

echo.
echo ========================================
echo           Test Results Summary
echo ========================================

if defined TEST_FAILED (
    echo [RESULT] Some tests failed
    echo.
    echo Troubleshooting suggestions:
    echo 1. Check if API key in configuration file is correct
    echo 2. Ensure network connection is normal
    echo 3. Check logs/modelscope_mcp.log log file
    echo 4. Run install_deps.bat to reinstall dependencies
    echo.
) else (
    echo [RESULT] All tests passed!
    echo.
    echo ModelScope MCP server functions normally, ready to use:
    echo 1. Run start_server.bat to start the server
    echo 2. Use MCP client to connect to the server
    echo 3. Start querying ModelScope datasets
    echo.
)

pause