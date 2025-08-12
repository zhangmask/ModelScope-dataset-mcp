@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ModelScope MCP Server Management Menu
echo.
echo ========================================
echo   ModelScope MCP Server Management
echo ========================================
echo.
echo 1. Start Server
echo 2. Stop Server
echo 3. Install/Update Dependencies
echo 4. Run Tests
echo 5. Check Server Status
echo 6. View Server Logs
echo 7. Edit Configuration
echo 8. View Design Documentation
echo 9. Developer Tools
echo 0. Exit
echo.
echo ========================================
echo.

set /p choice="Please select an option (0-9): "

if "%choice%"=="1" goto start_server
if "%choice%"=="2" goto stop_server
if "%choice%"=="3" goto install_deps
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto check_status
if "%choice%"=="6" goto view_logs
if "%choice%"=="7" goto edit_config
if "%choice%"=="8" goto view_docs
if "%choice%"=="9" goto dev_tools
if "%choice%"=="0" goto exit

echo Invalid option. Please try again.
pause
goto menu

:start_server
echo.
echo Starting ModelScope MCP Server...
echo.
call start_server.bat
pause
goto menu

:stop_server
echo.
echo Stopping ModelScope MCP Server...
echo.
call stop_server.bat
pause
goto menu

:install_deps
echo.
echo Installing/Updating Dependencies...
echo.
call install_deps.bat
pause
goto menu

:run_tests
echo.
echo Running Tests...
echo.
call test_all.bat
pause
goto menu

:check_status
echo.
echo Checking Server Status...
echo.
tasklist /fi "imagename eq python.exe" /fi "windowtitle eq *modelscope*" 2>nul | find "python.exe" >nul
if %errorlevel%==0 (
    echo Server is running.
) else (
    echo Server is not running.
)
echo.
pause
goto menu

:view_logs
echo.
echo Viewing Server Logs...
echo.
if exist "logs\server.log" (
    type "logs\server.log" | more
) else (
    echo No log file found.
)
pause
goto menu

:edit_config
echo.
echo Opening Configuration File...
echo.
if exist "config.json" (
    notepad "config.json"
) else (
    echo Configuration file not found.
)
pause
goto menu

:view_docs
echo.
echo Opening Design Documentation...
echo.
if exist "DESIGN.md" (
    notepad "DESIGN.md"
) else (
    echo Documentation file not found.
)
pause
goto menu

:dev_tools
echo.
echo ========================================
echo   Developer Tools
echo ========================================
echo.
echo 1. Run Simple Test
echo 2. Check Database
echo 3. Test Query Parsing
echo 4. Test Direct Query
echo 5. Back to Main Menu
echo.
set /p dev_choice="Select option (1-5): "

if "%dev_choice%"=="1" (
    echo Running simple test...
    python test_simple.py
) else if "%dev_choice%"=="2" (
    echo Checking database...
    python check_db.py
) else if "%dev_choice%"=="3" (
    echo Testing query parsing...
    python test_query_parsing.py
) else if "%dev_choice%"=="4" (
    echo Testing direct query...
    python test_direct_query.py
) else if "%dev_choice%"=="5" (
    goto menu
) else (
    echo Invalid option.
)
pause
goto menu

:exit
echo.
echo Goodbye!
echo.
exit /b 0

:menu
goto :eof