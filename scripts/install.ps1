# Scriber — Windows install script
# Usage: powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/stvbao/Scriber/main/scripts/install.ps1 | iex"
#
# Installs to %LOCALAPPDATA%\Scriber and adds it to the user PATH.

$ErrorActionPreference = "Stop"
$Repo = "stvbao/Scriber"
$InstallDir = "$env:LOCALAPPDATA\Scriber"

function Write-Step($msg) { Write-Host "  $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "  ERROR: $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "Scriber installer" -ForegroundColor White
Write-Host "-----------------"

# ── Resolve latest release ────────────────────────────────────────────────────
Write-Step "Fetching latest release from GitHub..."
try {
    $ApiUrl = "https://api.github.com/repos/$Repo/releases/latest"
    $Release = Invoke-RestMethod -Uri $ApiUrl -Headers @{ "User-Agent" = "scriber-installer" }
} catch {
    Write-Err "Could not reach GitHub API. Check your internet connection."
}

$Version = $Release.tag_name -replace '^v', ''
$InstallerName = "Scriber-${Version}-windows-installer.exe"
$ZipName = "Scriber-${Version}-windows.zip"
$InstallerAsset = $Release.assets | Where-Object { $_.name -eq $InstallerName }
$Asset = $Release.assets | Where-Object { $_.name -eq $ZipName }

if (-not $InstallerAsset -and -not $Asset) {
    Write-Err "No Windows release found for v$Version (expected '$InstallerName' or '$ZipName')."
}

Write-Ok "Found Scriber v$Version"

# ── Installer package ─────────────────────────────────────────────────────────
if ($InstallerAsset) {
    $InstallerUrl = $InstallerAsset.browser_download_url
    $TmpInstaller = "$env:TEMP\$InstallerName"

    Write-Step "Downloading $InstallerName..."
    try {
        Invoke-WebRequest -Uri $InstallerUrl -OutFile $TmpInstaller -UseBasicParsing
    } catch {
        Write-Err "Download failed: $_"
    }
    Write-Ok "Download complete"

    Write-Step "Running installer..."
    $Process = Start-Process -FilePath $TmpInstaller `
        -ArgumentList "/SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /TASKS=`"desktopicon,addtopath`"" `
        -Wait `
        -PassThru
    Remove-Item $TmpInstaller -Force

    if ($Process.ExitCode -ne 0) {
        Write-Err "Installer failed with exit code $($Process.ExitCode)."
    }

    Write-Host ""
    Write-Host "Scriber v$Version installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Double-click Scriber on your Desktop or Start Menu to open the app."
    Write-Host "  Or open a new terminal and run: Scriber transcribe interview.m4a"
    Write-Host ""
    Write-Host "Note: Windows SmartScreen may warn on first launch because the app"
    Write-Host "is unsigned. Click 'More info' -> 'Run anyway' to proceed."
    Write-Host ""
    exit 0
}

# ── Download ──────────────────────────────────────────────────────────────────
$ZipUrl = $Asset.browser_download_url
$TmpZip = "$env:TEMP\$ZipName"
Write-Step "Downloading $ZipName..."
try {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $TmpZip -UseBasicParsing
} catch {
    Write-Err "Download failed: $_"
}
Write-Ok "Download complete"

# ── Install ───────────────────────────────────────────────────────────────────
Write-Step "Installing to $InstallDir..."
if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
}
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Expand-Archive -Path $TmpZip -DestinationPath $InstallDir -Force
Remove-Item $TmpZip

# PyInstaller creates dist/Scriber/ — flatten one level if nested
$Nested = Join-Path $InstallDir "Scriber"
if (Test-Path $Nested) {
    $Items = Get-ChildItem $Nested
    foreach ($Item in $Items) {
        Move-Item -Path $Item.FullName -Destination $InstallDir -Force
    }
    Remove-Item $Nested -Recurse -Force
}

Write-Ok "Files extracted"

# ── PATH ──────────────────────────────────────────────────────────────────────
Write-Step "Adding to PATH..."
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    Write-Ok "Added $InstallDir to user PATH"
} else {
    Write-Ok "Already in PATH"
}

# ── Desktop shortcut ──────────────────────────────────────────────────────────
Write-Step "Creating desktop shortcut..."
$Exe = Join-Path $InstallDir "Scriber.exe"
$Shortcut = "$env:USERPROFILE\Desktop\Scriber.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Lnk = $WshShell.CreateShortcut($Shortcut)
$Lnk.TargetPath = $Exe
$Lnk.WorkingDirectory = $InstallDir
$Lnk.Description = "Scriber — offline audio transcription"
$Lnk.Save()
Write-Ok "Shortcut created on Desktop"

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Scriber v$Version installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Double-click Scriber on your Desktop to open the app."
Write-Host "  Or from a terminal: Scriber transcribe interview.m4a"
Write-Host ""
Write-Host "Note: Windows SmartScreen may warn on first launch because the app"
Write-Host "is unsigned. Click 'More info' -> 'Run anyway' to proceed."
Write-Host ""
