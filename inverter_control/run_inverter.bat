@echo off
REM File: run_inverter.bat
REM Chạy chương trình inverter control trong venv trên Windows

chcp 65001 >nul
title Inverter Control System v0.5.3 (VENV)

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

echo 🚀 Khởi động Inverter Control System v0.5.3...
echo ================================================

REM Chuyển đến thư mục script
cd /d "%SCRIPT_DIR%"

REM Kiểm tra và kích hoạt venv
if exist "%VENV_DIR%" (
    echo ✅ Phát hiện môi trường ảo (venv)
    call "%VENV_DIR%\Scripts\activate.bat"
    
    REM Kiểm tra Python trong venv
    python -c "import sys; print(f'Python {sys.version}')" >nul 2>&1
    if errorlevel 1 (
        echo ❌ Lỗi môi trường ảo, đang tái tạo...
        python -m venv "%VENV_DIR%"
        call "%VENV_DIR%\Scripts\activate.bat"
    )
) else (
    echo 📦 Tạo môi trường ảo mới...
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
)

REM Kiểm tra và cài đặt thư viện
echo 🔍 Kiểm tra thư viện...
python -c "import selenium, pandas, psutil" >nul 2>&1
if errorlevel 1 (
    echo 📦 Cài đặt thư viện cần thiết...
    pip install -r requirements.txt
)

REM Chạy chương trình
echo ✅ Khởi chạy chương trình...
python main.py

REM Deactivate venv
call deactivate

echo.
echo 👋 Chương trình đã kết thúc.
pause