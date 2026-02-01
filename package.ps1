# STT Bot Package Builder
# Creates distribution packages for Windows and Linux

$ErrorActionPreference = "Stop"

$ProjectDir = $PSScriptRoot
$BuildDir = Join-Path $ProjectDir "build"
$Version = "1.0"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  STT Bot Package Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean build directory
if (Test-Path $BuildDir) {
    Remove-Item -Recurse -Force $BuildDir
}

# Step 1: Copy common files
Write-Host "[1/4] Copying common files..." -ForegroundColor Yellow
$CommonDir = Join-Path $BuildDir "common"
New-Item -ItemType Directory -Path $CommonDir -Force | Out-Null

Copy-Item -Recurse (Join-Path $ProjectDir "bot") (Join-Path $CommonDir "bot")
Copy-Item -Recurse (Join-Path $ProjectDir "tools") (Join-Path $CommonDir "tools")
Copy-Item (Join-Path $ProjectDir ".env.example") $CommonDir
Copy-Item (Join-Path $ProjectDir "requirements.txt") $CommonDir
Copy-Item (Join-Path $ProjectDir "README.md") $CommonDir
$licensePath = Join-Path $ProjectDir "LICENSE"
if (Test-Path $licensePath) {
    Copy-Item $licensePath $CommonDir
}

# Step 2: Create Windows package
Write-Host "[2/4] Creating Windows package..." -ForegroundColor Yellow
$WinDir = Join-Path $BuildDir "windows"
New-Item -ItemType Directory -Path $WinDir -Force | Out-Null
Copy-Item -Recurse "$CommonDir\*" "$WinDir\"
Copy-Item (Join-Path $ProjectDir "install.bat") $WinDir
Copy-Item (Join-Path $ProjectDir "run.bat") $WinDir
Copy-Item (Join-Path $ProjectDir "install.ps1") $WinDir

# Remove Linux tools from Windows package
$linuxTools = Join-Path $WinDir "tools\linux"
if (Test-Path $linuxTools) {
    Remove-Item -Recurse -Force $linuxTools
}

# Step 3: Create Linux package
Write-Host "[3/4] Creating Linux package..." -ForegroundColor Yellow
$LinDir = Join-Path $BuildDir "linux"
New-Item -ItemType Directory -Path $LinDir -Force | Out-Null
Copy-Item -Recurse "$CommonDir\*" "$LinDir\"
Copy-Item (Join-Path $ProjectDir "install.sh") $LinDir
Copy-Item (Join-Path $ProjectDir "run.sh") $LinDir

# Remove Windows tools from Linux package
$winTools = Join-Path $LinDir "tools\windows"
if (Test-Path $winTools) {
    Remove-Item -Recurse -Force $winTools
}

# Step 4: Create archives
Write-Host "[4/4] Creating archives..." -ForegroundColor Yellow
$WinZip = Join-Path $ProjectDir "stt-bot-windows-$Version.zip"
$LinZip = Join-Path $ProjectDir "stt-bot-linux-$Version.zip"

if (Test-Path $WinZip) { Remove-Item $WinZip }
if (Test-Path $LinZip) { Remove-Item $LinZip }

Compress-Archive -Path "$WinDir\*" -DestinationPath $WinZip -Force
Compress-Archive -Path "$LinDir\*" -DestinationPath $LinZip -Force

# Clean up
Remove-Item -Recurse -Force $BuildDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Packages created successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Windows package: stt-bot-windows-$Version.zip"
Write-Host "Linux package:   stt-bot-linux-$Version.zip"
Write-Host ""
