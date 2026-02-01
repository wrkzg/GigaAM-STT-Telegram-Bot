@echo off
setlocal enabledelayedexpansion

REM STT Bot Package Builder
REM Creates distribution packages for Windows and Linux

echo ========================================
echo   STT Bot Package Builder
echo ========================================
echo.

set PROJECT_DIR=%~dp0
set BUILD_DIR=%PROJECT_DIR%build
set VERSION=1.0

REM Clean build directory
if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

echo [1/4] Copying common files...
xcopy /E /I /Q "%PROJECT_DIR%bot" "%BUILD_DIR%\common\bot" >nul
xcopy /E /I /Q "%PROJECT_DIR%tools" "%BUILD_DIR%\common\tools" >nul
copy /Y "%PROJECT_DIR%.env.example" "%BUILD_DIR%\common\" >nul
copy /Y "%PROJECT_DIR%requirements.txt" "%BUILD_DIR%\common\" >nul
copy /Y "%PROJECT_DIR%README.md" "%BUILD_DIR%\common\" >nul
copy /Y "%PROJECT_DIR%LICENSE" "%BUILD_DIR%\common\" >nul 2>nul

echo [2/4] Creating Windows package...
set WIN_DIR=%BUILD_DIR%\windows
mkdir "%WIN_DIR%"
xcopy /E /I /Q "%BUILD_DIR%\common\*" "%WIN_DIR%\" >nul
copy /Y "%PROJECT_DIR%install.bat" "%WIN_DIR%\" >nul
copy /Y "%PROJECT_DIR%run.bat" "%WIN_DIR%\" >nul
copy /Y "%PROJECT_DIR%install.ps1" "%WIN_DIR%\" >nul

REM Remove Linux tools from Windows package
if exist "%WIN_DIR%\tools\linux" rd /s /q "%WIN_DIR%\tools\linux"

echo [3/4] Creating Linux package...
set LIN_DIR=%BUILD_DIR%\linux
mkdir "%LIN_DIR%"
xcopy /E /I /Q "%BUILD_DIR%\common\*" "%LIN_DIR%\" >nul
copy /Y "%PROJECT_DIR%install.sh" "%LIN_DIR%\" >nul
copy /Y "%PROJECT_DIR%run.sh" "%LIN_DIR%\" >nul

REM Remove Windows tools from Linux package
if exist "%LIN_DIR%\tools\windows" rd /s /q "%LIN_DIR%\tools\windows"

echo [4/4] Creating archives...
PowerShell -Command "Compress-Archive -Path '%WIN_DIR%\*' -DestinationPath '%PROJECT_DIR%stt-bot-windows-%VERSION%.zip' -Force"
PowerShell -Command "Compress-Archive -Path '%LIN_DIR%\*' -DestinationPath '%PROJECT_DIR%stt-bot-linux-%VERSION%.zip' -Force"

REM Clean up
rd /s /q "%BUILD_DIR%"

echo.
echo ========================================
echo   Packages created successfully!
echo ========================================
echo.
echo Windows package: stt-bot-windows-%VERSION%.zip
echo Linux package:   stt-bot-linux-%VERSION%.zip
echo.
pause