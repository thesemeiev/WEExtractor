# Portable folder + ZIP for Windows: unzip and run — no installer.
# Requires Python + tkinter on the build machine only.
# Usage: powershell -ExecutionPolicy Bypass -File .\build_portable_windows.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

py -3 -c "import tkinter"
if ($LASTEXITCODE -ne 0) {
    Write-Error "tkinter not available. Install Python from python.org (with Tcl/Tk)."
    exit 1
}

py -3 -m venv .venv-build
& .\.venv-build\Scripts\Activate.ps1
python -m pip install -U pip wheel
pip install -r requirements-build.txt

if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
Remove-Item -Force -ErrorAction SilentlyContinue "$PSScriptRoot\PKG-Extractor.spec"

py -m PyInstaller `
  --onedir `
  --windowed `
  --clean `
  --noconfirm `
  --name PKG-Extractor `
  --hidden-import we_wallpaper `
  --hidden-import we_media_filter `
  --hidden-import we_repkg `
  --collect-all tkinter `
  --add-data "assets/app_icon.png;assets" `
  --add-data "VERSION;." `
  pkg_extractor_gui.py

Remove-Item -Force -ErrorAction SilentlyContinue "$PSScriptRoot\PKG-Extractor.spec"

$Portable = "dist\PKG-Extractor-Portable-Windows"
if (Test-Path $Portable) { Remove-Item -Recurse -Force $Portable }
Rename-Item -Path "dist\PKG-Extractor" -NewName "PKG-Extractor-Portable-Windows"

$Portable = Join-Path $PSScriptRoot "dist\PKG-Extractor-Portable-Windows"

$RepkgDir = Join-Path $Portable "repkg"
New-Item -ItemType Directory -Force -Path $RepkgDir | Out-Null
$RepkgZip = Join-Path $env:TEMP ("RePKG-" + [Guid]::NewGuid().ToString() + ".zip")
$RepkgUrl = "https://github.com/notscuffed/repkg/releases/download/v0.4.0-alpha/RePKG.zip"
Write-Host "Downloading RePKG (notscuffed/repkg)..."
Invoke-WebRequest -Uri $RepkgUrl -OutFile $RepkgZip
Expand-Archive -Path $RepkgZip -DestinationPath $RepkgDir -Force
Remove-Item -Force $RepkgZip
if (-not (Test-Path (Join-Path $RepkgDir "RePKG.exe"))) {
    Write-Warning "RePKG.exe not found after extract — check repkg release layout."
} else {
    Write-Host "Bundled: $RepkgDir\RePKG.exe"
}

@'
@echo off
setlocal
cd /d "%~dp0"
"%~dp0PKG-Extractor.exe" %*
'@ | Set-Content -Path (Join-Path $Portable "Run.bat") -Encoding ASCII

Copy-Item -Force "packaging\README_PORTABLE.txt" (Join-Path $Portable "README.txt")
Copy-Item -Force "VERSION" (Join-Path $Portable "VERSION.txt")

$ZipPath = Join-Path $PSScriptRoot "dist\PKG-Extractor-Portable-Windows.zip"
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path $Portable -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "Portable folder: $Portable"
Write-Host "ZIP: $ZipPath"
