@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set UV_LINK_MODE=copy

echo ========================================
echo ai-hedge-fund GUI
echo ========================================
echo.

rem Check if Python 3.11+ is available
echo [1/5] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python not found in PATH
    goto :setup_venv
)

rem Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

rem Extract major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

rem Check if version is 3.11 or higher
if %MAJOR% LSS 3 goto :setup_venv
if %MAJOR% EQU 3 if %MINOR% LSS 11 goto :setup_venv

echo  Python %PYTHON_VERSION% meets requirements (3.11+)
goto :check_venv

:setup_venv
echo [2/5] Setting up Python 3.11 virtual environment...
if not exist "uv.exe" (
    echo  uv.exe not found in current directory
    echo Please ensure uv.exe is available
    pause
    exit /b 1
)

echo Creating virtual environment with Python 3.11...
uv.exe venv --python=3.11
if errorlevel 1 (
    echo  Failed to create virtual environment
    pause
    exit /b 1
)
echo  Virtual environment created successfully
goto :install_deps

:check_venv
echo [2/5] Checking virtual environment...
if exist ".venv" (
    echo  Virtual environment already exists
) else (
    echo Creating virtual environment...
    if not exist "uv.exe" (
        echo  uv.exe not found in current directory
        pause
        exit /b 1
    )
    uv.exe venv --python=3.11
    if errorlevel 1 (
        echo  Failed to create virtual environment
        pause
        exit /b 1
    )
    echo  Virtual environment created successfully
)

:install_deps
echo [3/5] Installing dependencies...
if not exist "requirements.txt" (
    echo  requirements.txt not found
    pause
    exit /b 1
)

echo Installing packages from requirements.txt...
uv.exe pip install -r requirements.txt
if errorlevel 1 (
    echo  Failed to install dependencies
    pause
    exit /b 1
)
echo  Dependencies installed successfully

:rename_pyproject
echo [4/5] Checking pyproject.toml...
if exist "pyproject.toml" (
    echo Renaming pyproject.toml to pyproject-old.toml...
    ren "pyproject.toml" "pyproject-old.toml"
    if errorlevel 1 (
        echo  Failed to rename pyproject.toml
        pause
        exit /b 1
    )
    echo  pyproject.toml renamed to pyproject-old.toml
) else (
    echo   pyproject.toml not found, skipping rename
)

uv run gui_main.py
