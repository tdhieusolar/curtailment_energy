@echo off
setlocal enabledelayedexpansion

REM #######################################################
REM # setup_dev.bat - Windows Equivalent of setup_dev.sh #
REM #######################################################

REM ==========================================
REM CAU HINH
REM ==========================================
set VENV_NAME=venv
set REQS_IN_FILE=requirements.in
set REQS_OUT_FILE=requirements.txt
set PIP_TOOLS_PACKAGE=pip-tools

echo.
echo === KHOI TAO MOI TRUONG PHAT TRIEN (DEV SETUP) ===
echo =========================================================

REM --- 1. TAO VENV VA KICH HOAT ---
IF NOT EXIST "%VENV_NAME%" (
    echo.
    echo [TAO VENV] Dang tao Venv va kich hoat...
    python -m venv "%VENV_NAME%"
    IF ERRORLEVEL 1 (
        echo.
        echo [ERROR] Khong the tao Venv. Kiem tra Python trong PATH.
        goto :end
    )
)

set VENV_ACTIVATE_PATH="%VENV_NAME%\Scripts\activate.bat"
IF EXIST %VENV_ACTIVATE_PATH% (
    call %VENV_ACTIVATE_PATH%
    echo [SUCCESS] Da kich hoat Venv.
) ELSE (
    echo.
    echo [FATAL ERROR] Khong the tim thay script kich hoat Venv.
    goto :end
)

REM --- 2. TAO requirements.in (Neu thieu) ---
IF NOT EXIST "%REQS_IN_FILE%" (
    echo.
    echo [TAO FILE] Tao file %REQS_IN_FILE% voi cac phu thuoc mac dinh...
    
    (
        echo # Danh sach cac thu vien chinh ban su dung. Pip-tools se tu tim cac phu thuoc khac.
        echo selenium
        echo pandas
        echo psutil
        echo requests
    ) > "%REQS_IN_FILE%"
    
    echo [SUCCESS] %REQS_IN_FILE% da san sang de chinh sua.
)

REM --- 3. CAI DAT CONG CU PHAT TRIEN (PIP-TOOLS) ---
echo.
echo [CAI DAT] Dang cai dat %PIP_TOOLS_PACKAGE% de quan ly dependencies...
pip install %PIP_TOOLS_PACKAGE% --upgrade > NUL 2>&1
echo [SUCCESS] Da cai dat %PIP_TOOLS_PACKAGE%.

REM --- 4. BIEN DICH VA TAO requirements.txt ---
echo.
echo [BIEN DICH] Dang bien dich %REQS_IN_FILE% sang %REQS_OUT_FILE%...

pip-compile "%REQS_IN_FILE%"

IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Loi bien dich. Kiem tra %REQS_IN_FILE%.
    goto :deactivate
)
echo [SUCCESS] Da tao %REQS_OUT_FILE% thanh cong.

REM --- 5. CAI DAT THU VIEN VAO VENV HIEN TAI ---
echo.
echo [SYNC] Dang cai dat toan bo thu vien (Pip-sync)...
pip-sync

IF ERRORLEVEL 1 (
    echo.
    echo [WARNING] pip-sync bi loi, thu dung pip install -r...
    pip install -r "%REQS_OUT_FILE%"
)

echo.
echo [SUCCESS] MOI TRUONG PHAT TRIEN DA SAN SANG!
echo ---------------------------------------------------------
echo.
echo 👉 Bay gio ban co the chay: launch.bat

REM Khong deactivate de giu moi truong phat trien mo

:deactivate
REM Deactivate chi duoc goi neu co loi xay ra va can thoat
IF DEFINED VIRTUAL_ENV (
    deactivate
)

:end
pause
endlocal