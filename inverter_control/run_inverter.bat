@echo off
chcp 65001 >nul
title Inverter Control System v0.5.3

echo 🚀 Khởi động Inverter Control System v0.5.3...
echo ================================================

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

cd /d "%SCRIPT_DIR%"

REM Kiểm tra và kích hoạt venv
if exist "%VENV_DIR%" (
    echo ✅ Phát hiện môi trường ảo (venv)
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo 📦 Tạo môi trường ảo mới...
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
)

REM Kiểm tra thư viện
echo 🔍 Kiểm tra thư viện...
python -c "import selenium, pandas, psutil, webdriver_manager" >nul 2>&1
if errorlevel 1 (
    echo 📦 Cài đặt thư viện cần thiết...
    pip install -r requirements.txt
)

REM Kiểm tra hệ thống trình duyệt
echo 🔧 Kiểm tra hệ thống trình duyệt...
python system_check.py
if errorlevel 1 (
    echo ❌ Hệ thống trình duyệt chưa sẵn sàng
    call deactivate
    pause
    exit /b 1
)

REM Chạy chương trình chính
echo ✅ Khởi chạy chương trình...
python main.py

call deactivate
echo.
echo 👋 Chương trình đã kết thúc.
pause