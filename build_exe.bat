@echo off
setlocal
cd /d "%~dp0"

echo Installing game requirements...
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
py -3 -m pip install -r requirements-build.txt

if errorlevel 1 (
    echo.
    echo Install failed. Make sure Python is installed and added to PATH.
    pause
    exit /b 1
)

echo.
echo Building MutationRPG.exe...
py -3 build_exe.py

if errorlevel 1 (
    echo.
    echo Build failed. Read the error message above.
    pause
    exit /b 1
)

echo.
echo Done! Your EXE is here:
echo dist\MutationRPG.exe
echo.
pause
