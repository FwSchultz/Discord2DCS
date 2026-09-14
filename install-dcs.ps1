param(
    [ValidateSet('de','en')]
    [string]$Language = 'de'
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$savedGames = Join-Path $env:USERPROFILE "Saved Games"

$messages = @{
    de = @{
        missing = "Kein DCS-Saved-Games-Ordner gefunden. Erwartet wurde z. B. 'Saved Games\\DCS' oder 'Saved Games\\DCS.openbeta'."
        installed = "Discord2DCS v0.11.0-beta wurde installiert nach:"
        restart = "DCS danach vollständig neu starten."
    }
    en = @{
        missing = "No DCS Saved Games folder found. Expected e.g. 'Saved Games\\DCS' or 'Saved Games\\DCS.openbeta'."
        installed = "Discord2DCS v0.11.0-beta was installed to:"
        restart = "Restart DCS completely afterwards."
    }
}

$targets = @()
if (Test-Path $savedGames) {
    $targets = Get-ChildItem -Path $savedGames -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^DCS($|\.)' }
}
if (-not $targets -or $targets.Count -eq 0) {
    throw $messages[$Language].missing
}

$sourceScripts = Join-Path $root "Scripts"
foreach ($target in $targets) {
    $targetScripts = Join-Path $target.FullName "Scripts"
    New-Item -ItemType Directory -Force -Path $targetScripts | Out-Null
    Copy-Item -Path (Join-Path $sourceScripts "*") -Destination $targetScripts -Recurse -Force
    Set-Content -Path (Join-Path $targetScripts "Discord2DCS\\language.txt") -Value $Language -Encoding ASCII

    $sourceMod = Join-Path $root "Mods\\tech\\Discord2DCS"
    $targetTech = Join-Path $target.FullName "Mods\\tech"
    $targetMod = Join-Path $targetTech "Discord2DCS"
    New-Item -ItemType Directory -Force -Path $targetTech | Out-Null
    if (Test-Path $targetMod) { Remove-Item $targetMod -Recurse -Force }
    Copy-Item $sourceMod $targetMod -Recurse -Force
    Write-Host $messages[$Language].installed -ForegroundColor Green
    Write-Host $targetScripts -ForegroundColor Green
}
Write-Host $messages[$Language].restart -ForegroundColor Yellow
