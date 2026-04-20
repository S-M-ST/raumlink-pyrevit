# update_raumlink.ps1
# Holt den aktuellen Branch von GitHub und installiert ihn nach
# pyBD.extension\pyBD.tab\RaumLink.panel (bzw. pyBD.extension\RaumLink_SharedParams.txt).
#
# Benutzung:
#   Rechtsklick -> "Mit PowerShell ausfuehren"
# oder
#   PS> .\update_raumlink.ps1 [-Branch main] [-ExtRoot "Q:\..\pyBD.extension"]

[CmdletBinding()]
param(
    [string]$Branch  = "claude/fix-sharedparams-binding-kPDMV",
    [string]$Repo    = "S-M-ST/raumlink-pyrevit",
    [string]$ExtRoot = "Q:\10436_BuD\_BuD_CLOUD\000_pyRevit\pyBD.extension",
    [string]$TabName   = "pyBD.tab",
    [string]$PanelName = "RaumLink.panel"
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# --- Download ZIP ---
$zipUrl  = "https://github.com/$Repo/archive/refs/heads/$Branch.zip"
$tmpBase = Join-Path ([IO.Path]::GetTempPath()) ("raumlink_" + [Guid]::NewGuid().ToString("N"))
$zipPath = "$tmpBase.zip"
$extract = "$tmpBase"

Write-Host "Downloading $zipUrl ..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

Write-Host "Extracting ..." -ForegroundColor Cyan
Expand-Archive -Path $zipPath -DestinationPath $extract -Force

# Top-level Ordner im ZIP (raumlink-pyrevit-<branch-mit-dashes>)
$zipRoot = Get-ChildItem $extract | Where-Object { $_.PSIsContainer } | Select-Object -First 1
if (-not $zipRoot) { throw "ZIP-Inhalt leer." }

$srcPanel       = Join-Path $zipRoot.FullName "TestRaumLink.extension\RaumLink.tab\Raum.panel"
$srcParams      = Join-Path $zipRoot.FullName "TestRaumLink.extension\RaumLink_SharedParams.txt"

$dstPanel       = Join-Path $ExtRoot "$TabName\$PanelName"
$dstParamsExt   = Join-Path $ExtRoot "RaumLink_SharedParams.txt"   # Ort den das Skript erwartet
$dstParamsTab   = Join-Path (Join-Path $ExtRoot $TabName) "RaumLink_SharedParams.txt"

# --- Sanity Checks ---
if (-not (Test-Path $ExtRoot)) { throw "Extension-Root nicht gefunden: $ExtRoot" }
if (-not (Test-Path $srcPanel))  { throw "Panel im ZIP nicht gefunden: $srcPanel" }
if (-not (Test-Path $srcParams)) { throw "SharedParams im ZIP nicht gefunden: $srcParams" }

# --- Panel-Ordner spiegeln (pushbuttons + bundle.yaml) ---
Write-Host "Syncing panel -> $dstPanel" -ForegroundColor Cyan
if (-not (Test-Path $dstPanel)) { New-Item -ItemType Directory -Path $dstPanel | Out-Null }
Copy-Item -Path (Join-Path $srcPanel "*") -Destination $dstPanel -Recurse -Force

# --- SharedParams-Datei an korrekte Stelle (Extension-Root) ---
Write-Host "Copying SharedParams -> $dstParamsExt" -ForegroundColor Cyan
Copy-Item -Path $srcParams -Destination $dstParamsExt -Force

# Falls noch eine veraltete Version auf Tab-Ebene liegt: warnen
if (Test-Path $dstParamsTab) {
    Write-Host "WARN: veraltete RaumLink_SharedParams.txt liegt noch unter $dstParamsTab" -ForegroundColor Yellow
    Write-Host "      Wird vom Skript NICHT gelesen. Manuell loeschen wenn nicht gebraucht." -ForegroundColor Yellow
}

# --- Cleanup ---
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
Remove-Item $extract -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "OK. Branch '$Branch' ist installiert." -ForegroundColor Green
Write-Host "In Revit: pyRevit -> Reload (oder Revit neu starten)." -ForegroundColor Green
