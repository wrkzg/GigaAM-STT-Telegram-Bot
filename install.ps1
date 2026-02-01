# STT Bot Portable Installer
# Requires PowerShell 5.1+ (Windows 10/11)

$ErrorActionPreference = "Stop"

# Project root
$ProjectRoot = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation STT Bot (Portable)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to get Python version from executable
function Test-PythonVersion {
    param([string]$PythonExe)

    try {
        $output = & $PythonExe --version 2>&1
        if ($output -match "Python (\d+)\.(\d+)\.(\d+)") {
            return @{
                Major = [int]$Matches[1]
                Minor = [int]$Matches[2]
                Patch = [int]$Matches[3]
                Full = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                Path = $PythonExe
            }
        }
    } catch {
        return $null
    }
    return $null
}

# Function to find compatible Python
function Find-CompatiblePython {
    $candidates = @()

    # Check user-local Python installations
    $localPrograms = "$env:LOCALAPPDATA\Programs\Python"
    if (Test-Path $localPrograms) {
        $dirs = Get-ChildItem $localPrograms -Directory -ErrorAction SilentlyContinue
        foreach ($dir in $dirs) {
            $pythonExe = "$($dir.FullName)\python.exe"
            if (Test-Path $pythonExe) {
                $candidates += $pythonExe
            }
        }
    }

    # Check program files
    $programFiles = @("${env:ProgramFiles}\Python", "${env:ProgramFiles(x86)}\Python")
    foreach ($pf in $programFiles) {
        if (Test-Path $pf) {
            $dirs = Get-ChildItem $pf -Directory -ErrorAction SilentlyContinue
            foreach ($dir in $dirs) {
                $pythonExe = "$($dir.FullName)\python.exe"
                if (Test-Path $pythonExe) {
                    $candidates += $pythonExe
                }
            }
        }
    }

    # Check local portable installation
    $localPython = "$ProjectRoot\python310\python.exe"
    if (Test-Path $localPython) {
        $candidates += $localPython
    }

    # Remove duplicates
    $candidates = $candidates | Select-Object -Unique

    # Test each candidate
    foreach ($candidate in $candidates) {
        $ver = Test-PythonVersion $candidate
        if ($ver -and $ver.Major -eq 3 -and ($ver.Minor -eq 10 -or $ver.Minor -eq 11)) {
            Write-Host "Found compatible Python: $($ver.Full) at $($ver.Path)" -ForegroundColor Green
            return $ver
        }
    }

    return $null
}

# Function to install Python locally
function Install-LocalPython {
    $localPythonDir = "$ProjectRoot\python310"

    Write-Host "Installing Python 3.10.11 locally to project..." -ForegroundColor Yellow
    Write-Host "Location: $localPythonDir" -ForegroundColor Cyan
    Write-Host ""

    # Remove existing installation if any
    if (Test-Path $localPythonDir) {
        Write-Host "Removing existing local Python..." -ForegroundColor Yellow
        Remove-Item -Path $localPythonDir -Recurse -Force
    }

    # Remove existing .venv if any
    if (Test-Path ".venv") {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Path ".venv" -Recurse -Force
    }

    # Download installer with multiple sources
    Write-Host "Downloading Python installer..." -ForegroundColor Green

    # Multiple download sources (in order of preference)
    $urls = @(
        "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe",
        "https://ftp.nluug.nl/pub/python/3.10.11/python-3.10.11-amd64.exe",
        "https://ftp.pasteur.fr/pub/python/3.10.11/python-3.10.11-amd64.exe"
    )

    $installer = "$env:TEMP\python_portable_installer.exe"
    $downloaded = $false

    foreach ($url in $urls) {
        try {
            Write-Host "Trying: $url" -ForegroundColor Cyan
            Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing -TimeoutSec 60
            if (Test-Path $installer) {
                $fileSize = (Get-Item $installer).Length
                if ($fileSize -gt 1MB) {
                    $downloaded = $true
                    Write-Host "Downloaded successfully ($([math]::Round($fileSize/1MB, 2)) MB)" -ForegroundColor Green
                    break
                }
            }
        } catch {
            Write-Host "Failed: $($url.split('/')[-1])" -ForegroundColor DarkYellow
            continue
        }
    }

    if (-not $downloaded) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Download Failed - All Sources Unavailable" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download Python manually:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Option 1 - Official Site:" -ForegroundColor Cyan
        Write-Host "  https://www.python.org/downloads/release/python-31011/" -ForegroundColor White
        Write-Host "  File: python-3.10.11-amd64.exe" -ForegroundColor White
        Write-Host ""
        Write-Host "Option 2 - Alternative Mirror:" -ForegroundColor Cyan
        Write-Host "  https://github.com/python/cpython/raw/v3.10.11/PCbuild/amd64/" -ForegroundColor White
        Write-Host ""
        Write-Host "After download, place the installer in this folder and run:" -ForegroundColor Yellow
        Write-Host "  .\python-3.10.11-amd64.exe /quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir=python310" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Install to local directory
    Write-Host "Installing Python (please wait)..." -ForegroundColor Green
    $argsList = "/quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir=$localPythonDir"

    $process = Start-Process -FilePath $installer -ArgumentList $argsList -Wait -PassThru
    Remove-Item $installer -Force

    if ($process.ExitCode -eq 0 -and (Test-Path "$localPythonDir\python.exe")) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Python 3.10.11 installed locally!" -ForegroundColor Green
        Write-Host "Location: $localPythonDir" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        return "$localPythonDir\python.exe"
    } else {
        Write-Host "ERROR: Failed to install Python" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Step 1: Find or install compatible Python
Write-Host "[1/7] Checking Python..." -ForegroundColor Cyan

$pythonVer = Find-CompatiblePython

if ($null -eq $pythonVer) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Compatible Python Not Found" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Required: Python 3.10.x or 3.11.x" -ForegroundColor Yellow
    Write-Host "Found: Python 3.14 in PATH (incompatible)" -ForegroundColor Red
    Write-Host ""
    Write-Host "PyTorch 2.5.1 (required by GigaAM) is not available for Python 3.14+" -ForegroundColor Red
    Write-Host ""

    $response = Read-Host "Install Python 3.10.11 locally in project folder? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        $pythonExe = Install-LocalPython
        $pythonVer = Test-PythonVersion $pythonExe
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Manual Installation Required" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Download Python 3.10.11 from one of these sources:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. Official Site (if available):" -ForegroundColor Cyan
        Write-Host "   https://www.python.org/downloads/release/python-31011/" -ForegroundColor White
        Write-Host "   File: python-3.10.11-amd64.exe" -ForegroundColor White
        Write-Host ""
        Write-Host "2. Alternative Mirrors:" -ForegroundColor Cyan
        Write-Host "   https://ftp.nluug.nl/pub/python/3.10.11/python-3.10.11-amd64.exe" -ForegroundColor White
        Write-Host "   https://ftp.pasteur.fr/pub/python/3.10.11/python-3.10.11-amd64.exe" -ForegroundColor White
        Write-Host ""
        Write-Host "After download, run:" -ForegroundColor Yellow
        Write-Host "   .\python-3.10.11-amd64.exe /quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir=python310" -ForegroundColor White
        Write-Host ""
        Write-Host "Then run: .\install.bat" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
}

$pythonExe = $pythonVer.Path
Write-Host "Using: $pythonExe" -ForegroundColor Green
Write-Host ""

# Step 2: Create virtual environment
Write-Host "[2/7] Creating virtual environment..." -ForegroundColor Cyan

if (Test-Path ".venv") {
    Write-Host "Virtual environment exists, recreating with correct Python..." -ForegroundColor Yellow
    Remove-Item -Path ".venv" -Recurse -Force
}

& $pythonExe -m venv .venv

if ($LASTEXITCODE -eq 0) {
    Write-Host "Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to create venv" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 3: Activate virtual environment
Write-Host "[3/7] Activating virtual environment..." -ForegroundColor Cyan

$activateScript = ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to find activation script" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 4: Upgrade pip
Write-Host "[4/7] Upgrading pip..." -ForegroundColor Cyan
& python -m pip install --upgrade pip -q
Write-Host "pip upgraded" -ForegroundColor Green
Write-Host ""

# Step 5: Install dependencies
Write-Host "[5/7] Installing dependencies..." -ForegroundColor Cyan
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

Write-Host "- Installing PyTorch (~2GB)..." -ForegroundColor Cyan
& pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install PyTorch" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "- Installing GigaAM and other dependencies..." -ForegroundColor Cyan
& pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 6: Create folders
Write-Host "[6/7] Creating folders..." -ForegroundColor Cyan

if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

if (-not (Test-Path "temp")) {
    New-Item -ItemType Directory -Path "temp" -Force | Out-Null
}

Write-Host "Folders created" -ForegroundColor Green
Write-Host ""

# Step 7: Configuration
Write-Host "[7/7] Configuration..." -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "Configuration Required" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Created .env from .env.example" -ForegroundColor Green
    Write-Host ""
    Write-Host "Open .env and set your TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
    Write-Host "Get token from: @BotFather in Telegram" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To run the bot:" -ForegroundColor Cyan
Write-Host "  1. Open .env and set TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
Write-Host "  2. Run: .\run.bat" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
