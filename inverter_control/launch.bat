@echo off
REM ######################################################
REM # Launch Script cho Windows (Tương đương launch.sh) #
REM ######################################################

REM --- 1. Kích hoạt môi trường ảo (Virtual Environment - Venv) ---

REM Đường dẫn kích hoạt Venv trên Windows
set VENV_PATH=.\venv\Scripts\activate.bat

IF EXIST "%VENV_PATH%" (
    echo.
    echo 🌐 Kích hoạt môi trường ảo Venv...
    call "%VENV_PATH%"
) ELSE (
    echo.
    echo ❌ Lỗi: Không tìm thấy Venv. Chạy setup_dev.bat (hoặc setup_dev.sh) de tao moi truong.
    goto :end
)

REM --- 2. Đồng bộ các thư viện Python (pip-sync) ---

IF EXIST "requirements.txt" (
    echo.
    echo 📦 Dong bo cac thu vien Python tu requirements.txt...
    
    REM pip-sync la cach toi uu nhat, neu khong co thi dung pip install -r
    pip install pip-tools > NUL 2>&1
    
    REM Kiem tra xem pip-sync co san hay khong
    pip-sync requirements.txt
    
    IF ERRORLEVEL 1 (
        echo ⚠️ pip-sync bi loi, thu dung pip install -r...
        pip install -r requirements.txt
        IF ERRORLEVEL 1 (
            echo ❌ LOI: Khong the cai dat cac thu vien. Kiem tra ket noi mang va quyen truy cap.
            goto :deactivate
        )
    )
) ELSE (
    echo.
    echo ⚠️ Khong tim thay requirements.txt. Bo qua buoc dong bo thu vien.
)

REM --- 3. Chạy System Checker ---

echo.
echo 🔍 Kiem tra he thong...
python utils/system_checker.py

IF ERRORLEVEL 1 (
    echo.
    echo ❌ LOI: Kiem tra he thong that bai. Khong the tiep tuc.
    goto :deactivate
)

REM --- 4. Chạy Ứng dụng Chính ---

echo.
echo 🚀 Khoi dong chuong trinh chinh...
python main.py

REM --- 5. Kết thúc và Tắt Venv ---

:deactivate
echo.
echo 🚪 Ket thuc chuong trinh. Tat Venv.
deactivate

:end
pause