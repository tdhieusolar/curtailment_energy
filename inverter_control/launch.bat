@echo off
setlocal

REM ######################################################
REM # launch.bat - Windows Equivalent of launch.sh       #
REM ######################################################

REM ==========================================
REM CAU HINH
REM ==========================================
set VENV_NAME=venv
set REQUIREMENTS_FILE=requirements.txt
set MAIN_SCRIPT=app_launcher.py

echo.
echo === INVERTER CONTROL SYSTEM - PROFESSIONAL LAUNCHER ===
echo =======================================================

REM --- 1. KIEM TRA PYTHON VA FILE REQUIREMENTS ---

REM Kiem tra Python co san hay khong
where python > NUL 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Khong tim thay Python. Vui long cai dat Python va them vao PATH.
    goto :end
)

REM Kiem tra file requirements.txt
IF NOT EXIST "%REQUIREMENTS_FILE%" (
    echo.
    echo [ERROR TRIEN KHAI] File %REQUIREMENTS_FILE% bi thieu.
    echo Vui long chay setup_dev.bat de tao file nay.
    goto :end
)

REM Kiem tra kich thuoc file (khong rỗng)
for %%f in ("%REQUIREMENTS_FILE%") do set FILE_SIZE=%%~zf
IF "%FILE_SIZE%" EQU "0" (
    echo.
    echo [ERROR TRIEN KHAI] File %REQUIREMENTS_FILE% bi rong.
    echo Vui long kiem tra lai requirements.in
    goto :end
)
echo [SUCCESS] Da tim thay file %REQUIREMENTS_FILE% (Toan ven)

REM --- 2. KIEM TRA & TAO VENV ---
IF NOT EXIST "%VENV_NAME%" (
    echo.
    echo [VENV] Khong tim thay moi truong ao. Dang tao moi...
    python -m venv "%VENV_NAME%"
    IF ERRORLEVEL 1 (
        echo [ERROR] Tao venv that bai!
        goto :end
    )
    echo [SUCCESS] Da tao venv thanh cong!
)
echo [SUCCESS] Da tim thay moi truong ao (%VENV_NAME%).

REM --- 3. KICH HOAT & CAI DAT THU VIEN ---
set VENV_ACTIVATE_PATH="%VENV_NAME%\Scripts\activate.bat"

IF EXIST %VENV_ACTIVATE_PATH% (
    call %VENV_ACTIVATE_PATH%
) ELSE (
    echo [FATAL ERROR] Khong tim thay script kich hoat Venv.
    goto :end
)

echo.
echo [SYNC] Dang dong bo thu vien tu %REQUIREMENTS_FILE%...
pip install --upgrade pip > NUL 2>&1
REM Su dung cờ -q (quiet) va --no-cache-dir de cai dat chuyen nghiep
pip install -r "%REQUIREMENTS_FILE%" --no-cache-dir -q

IF ERRORLEVEL 0 (
    echo [SUCCESS] Thu vien da san sang trong Venv!
) ELSE (
    echo [ERROR] Loi khi cai dat thu vien. Vui long kiem tra requirements.txt
    REM Van tiep tuc de chay app voi log chi tiet hon
)


REM --- 4. KHOI CHAY UNG DUNG ---
echo ---------------------------------------------------
echo [LAUNCH] Dang khoi chay ung dung...
echo ---------------------------------------------------

python "%MAIN_SCRIPT%"

REM --- 5. KET THUC ---
:deactivate
deactivate
echo.
echo [QUIT] Ung dung da ket thuc.

:end
pause
endlocal