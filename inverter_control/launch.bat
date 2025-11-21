@echo off
chcp 65001 >nul
title Inverter Control System - Universal Launcher

echo 🚀 Inverter Control System - Universal Launcher
echo ================================================

:: Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không được cài đặt!
    echo 📦 Vui lòng cài đặt Python trước
    pause
    exit /b 1
)

:: Thử app_launcher trước, nếu lỗi thì dùng run_app
echo 🔧 Đang khởi chạy với app_launcher...
python app_launcher.py
if errorlevel 1 (
    echo ⚠️ app_launcher gặp vấn đề, thử run_app...
    python run_app.py
)

pause