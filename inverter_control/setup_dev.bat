@echo off
REM #######################################################
REM # Setup Development Environment Script cho Windows    #
REM #######################################################

REM Thoat khoi script neu co loi xay ra
setlocal enabledelayedexpansion

REM --- 1. Tao moi truong ao (venv) ---

IF NOT EXIST "venv" (
    echo.
    echo 🌐 Tao moi truong ao (venv)...
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo ❌ LOI: Khong the tao moi truong ao. Kiem tra xem Python co trong PATH khong.
        goto :end
    )
    echo ✅ Tao venv thanh cong.
) ELSE (
    echo.
    echo 🌐 Moi truong ao venv da ton tai. Bo qua buoc tao.
)

REM --- 2. Kich hoat Venv va Cai dat pip-tools ---

REM Duong dan kich hoat Venv tren Windows
set VENV_ACTIVATE=.\venv\Scripts\activate.bat

IF EXIST "%VENV_ACTIVATE%" (
    echo.
    echo 🛠️ Kich hoat Venv va cai dat pip-tools...
    call "%VENV_ACTIVATE%"
    
    pip install pip-tools
    IF ERRORLEVEL 1 (
        echo ❌ LOI: Khong the cai dat pip-tools. Kiem tra ket noi mang.
        goto :deactivate
    )
    echo ✅ pip-tools da duoc cai dat.
) ELSE (
    echo.
    echo ❌ LOI: Khong tim thay script kich hoat Venv.
    goto :end
)

REM --- 3. Bien dich requirements.in thanh requirements.txt ---

IF EXIST "requirements.in" (
    echo.
    echo 📝 Bien dich requirements.in thanh requirements.txt...
    pip-compile requirements.in
    IF ERRORLEVEL 1 (
        echo ❌ LOI: pip-compile that bai. Kiem tra cu phap requirements.in.
        goto :deactivate
    )
    echo ✅ requirements.txt da duoc tao.
) ELSE (
    echo.
    echo ⚠️ Khong tim thay file requirements.in. Bo qua buoc bien dich.
    echo ⚠️ Vui long tao file requirements.in voi danh sach cac goi chinh.
)

REM --- 4. Dong bo cac thu vien Python (Giong nhu trong launch.bat) ---

IF EXIST "requirements.txt" (
    echo.
    echo 📦 Dong bo cac thu vien Python tu requirements.txt...
    pip-sync requirements.txt
    
    IF ERRORLEVEL 1 (
        echo ⚠️ pip-sync bi loi, thu dung pip install -r...
        pip install -r requirements.txt
        IF ERRORLEVEL 1 (
            echo ❌ LOI: Khong the cai dat cac thu vien.
            goto :deactivate
        )
    )
    echo ✅ Dong bo thu vien hoan tat.
)

REM --- 5. Ket thuc va Tat Venv ---

:deactivate
echo.
echo 🚪 Tat Venv.
deactivate

:end
echo.
echo === Qua trinh setup da hoan tat. ===
pause
endlocal