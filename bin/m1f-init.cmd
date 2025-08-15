@echo off
rem m1f-init - Initialize m1f for a project (Windows)

setlocal enabledelayedexpansion

rem Save current directory
set "ORIGINAL_DIR=%CD%"

rem Get the directory of this script
set "BIN_DIR=%~dp0"
rem Remove trailing backslash
set "BIN_DIR=%BIN_DIR:~0,-1%"

rem Get project root (parent of bin)
for %%i in ("%BIN_DIR%") do set "PROJECT_ROOT=%%~dpi"
rem Remove trailing backslash
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

rem Set PYTHONPATH to include project root
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

rem Check if venv exists and activate if available
if exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
) else if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
)

rem Run the Python script
python "%PROJECT_ROOT%\tools\m1f_init.py" %*

rem Return to original directory
cd /d "%ORIGINAL_DIR%"

endlocal