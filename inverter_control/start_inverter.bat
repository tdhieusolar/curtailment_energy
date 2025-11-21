@echo off
REM File: start_inverter.bat
REM Phiên bản nâng cao cho Windows với venv

setlocal EnableDelayedExpansion

chcp 65001 >nul
title Inverter Control System v0.5.3 - Advanced (VENV)

set "SCRIPT_DIR=%~dp0"
set "LOG_FILE=%SCRIPT_DIR%startup.log"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "CONFIG_FILE=inverter_config.xlsx"

REM Hàm log
call :log "🚀 BẮT ĐẦU KHỞI CHẠY INVERTER CONTROL SYSTEM (VENV)"
call :log "===================================================="

REM Chuyển đến thư mục script
cd /d "%SCRIPT_DIR%"

REM Kiểm tra file
call :check_files
if errorlevel 1 (
    call :log "❌ Không thể khởi chạy do thiếu file"
    pause
    exit /b 1
)

REM Thiết lập venv
call :setup_venv
if errorlevel 1 (
    call :log "❌ Không thể thiết lập venv"
    pause
    exit /b 1
)

REM Kiểm tra dependencies
call :check_dependencies
if errorlevel 1 (
    call :log "❌ Không thể cài đặt dependencies"
    pause
    exit /b 1
)

REM Chạy chương trình chính
call :log "🎯 ĐANG KHỞI CHẠY CHƯƠNG TRÌNH CHÍNH..."
echo.

python main.py
set EXIT_CODE=!errorlevel!

echo.
call :log "🔚 Chương trình đã kết thúc với mã: !EXIT_CODE!"

if !EXIT_CODE!==0 (
    call :log "✅ KẾT THÚC THÀNH CÔNG"
) else (
    call :log "❌ KẾT THÚC VỚI LỖI"
)

call deactivate
pause
exit /b 0

REM ========== FUNCTIONS ==========

:log
echo [%date% %time%] %~1 >> "%LOG_FILE%"
echo %~1
exit /b 0

:check_files
call :log "🔍 Kiểm tra file cần thiết..."
if not exist "main.py" (
    call :log "❌ Thiếu file: main.py"
    exit /b 1
)
if not exist "requirements.txt" (
    call :log "❌ Thiếu file: requirements.txt"
    exit /b 1
)
if not exist "%CONFIG_FILE%" (
    call :log "⚠️  File cấu hình Excel không tồn tại, sẽ sử dụng config mặc định"
)
call :log "✅ Tất cả file cần thiết đã tồn tại"
exit /b 0

:setup_venv
call :log "🐍 Thiết lập môi trường ảo..."
if exist "%VENV_DIR%" (
    call :log "✅ Phát hiện venv tồn tại"
    call "%VENV_DIR%\Scripts\activate.bat"
    
    python -c "import sys; print(f'Python {sys.version}')" >nul 2>&1
    if errorlevel 1 (
        call :log "⚠️ Venv bị lỗi, tái tạo..."
        goto create_venv
    )
    
    for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version.split()[0])" 2^>^&1') do set PY_VERSION=%%i
    call :log "✅ Venv hoạt động - Python !PY_VERSION!"
    exit /b 0
) else (
    :create_venv
    call :log "📦 Tạo venv mới..."
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        call :log "❌ Lỗi tạo venv!"
        exit /b 1
    )
    call "%VENV_DIR%\Scripts\activate.bat"
    call :log "✅ Đã tạo và kích hoạt venv"
    exit /b 0
)

:check_dependencies
call :log "📦 Kiểm tra dependencies..."
python -c "import selenium, pandas, psutil, openpyxl" >nul 2>&1
if errorlevel 1 (
    call :log "⚠️ Thiếu thư viện, đang cài đặt..."
    pip install -r requirements.txt
    if errorlevel 1 (
        call :log "❌ Lỗi cài đặt thư viện!"
        exit /b 1
    )
    call :log "✅ Cài đặt thư viện thành công"
) else (
    call :log "✅ Tất cả thư viện đã sẵn sàng"
)
exit /b 0