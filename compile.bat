@echo off
setlocal

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies from requirements.txt.
    echo Please check your Python environment and ensure pip is working.
    pause
    exit /b 1
)

echo.
echo [2/3] Building executable with PyInstaller...
pyinstaller --noconfirm --onefile --windowed --icon="icon.ico" --name "QuickRewriter" --add-data "config.json;." --add-data "prompts.json;." "quick_rewriter.py"
if %errorlevel% neq 0 (
    echo.
    echo ERROR: PyInstaller failed to build the executable.
    echo Check the output above for specific errors.
    pause
    exit /b 1
)

echo.
echo [3/3] Creating installer with Inno Setup...
if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo.
    echo WARNING: Inno Setup compiler not found at default location.
    echo Please install Inno Setup 6 (https://jrsoftware.org/isinfo.php)
    echo or ensure ISCC.exe is in your system PATH.
    pause
    exit /b 1
)

"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer.iss"
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Inno Setup failed to create the installer.
    echo Check the output above for specific errors.
    pause
    exit /b 1
)


echo.
echo =================================
echo  Compilation Successful!
echo =================================
echo.
echo Your installer can be found in the 'Output' directory.
echo.
pause
endlocal
