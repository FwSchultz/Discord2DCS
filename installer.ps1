param(
    [ValidateSet('Install','Update','Repair','Uninstall','AutostartOn','AutostartOff','Language')]
    [string]$Mode = 'Install',
    [string]$Language = ''
)

$ErrorActionPreference = 'Stop'
$Version = '0.10.0-beta-rc2'
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallRoot = Join-Path $env:LOCALAPPDATA 'Discord2DCS'
$InstalledClient = Join-Path $InstallRoot 'pc-client'
$InstalledScripts = Join-Path $InstallRoot 'Scripts'
$InstalledMods = Join-Path $InstallRoot 'Mods'
$InstalledAssets = Join-Path $InstallRoot 'assets'
$StatePath = Join-Path $InstallRoot 'install-state.json'
$StartupName = 'Discord2DCS.lnk'

function Get-InitialLanguage([bool]$ForcePrompt = $false) {
    if (-not $ForcePrompt) {
        if ($Language -in @('de','en')) { return $Language }
        if ($env:D2DCS_LANG -in @('de','en')) { return $env:D2DCS_LANG }
        $existingConfig = Join-Path $InstalledClient 'config.json'
        if (Test-Path $existingConfig) {
            try {
                $cfg = Get-Content -Raw -Path $existingConfig | ConvertFrom-Json
                if (([string]$cfg.language) -in @('de','en')) { return [string]$cfg.language }
            } catch {}
        }
        if (Test-Path $StatePath) {
            try {
                $stateLang = (Get-Content -Raw -Path $StatePath | ConvertFrom-Json).language
                if (([string]$stateLang) -in @('de','en')) { return [string]$stateLang }
            } catch {}
        }
    }

    Write-Host ''
    Write-Host 'Discord2DCS - Sprache / Language' -ForegroundColor Cyan
    Write-Host '[1] Deutsch'
    Write-Host '[2] English'
    do { $choice = (Read-Host 'Auswahl / Choice [1/2]').Trim() } while ($choice -notin @('1','2'))
    if ($choice -eq '1') { return 'de' }
    return 'en'
}

$forceLanguagePrompt = ($Mode -eq 'Language')
$Language = Get-InitialLanguage $forceLanguagePrompt
$env:D2DCS_LANG = $Language

$Texts = @{
    de = @{
        warning='WARNUNG'; install_files='Programmdateien installieren/aktualisieren'; repair_files='Installierte Programmdateien werden für Reparatur verwendet.';
        installation='Installation'; dcs_install='DCS-Hook installieren'; dcs_files='DCS-Dateien'; python_check='Python 3.12 und PC-Client prüfen'; python_ready='Python-Umgebung und Abhängigkeiten sind bereit.';
        legacy_ok='Vorhandene Kopplung aus alter Installation übernommen'; legacy_warn='Alte config.json konnte nicht automatisch übernommen werden'; configured='PC-Client konfiguriert.';
        token_found='Vorhandene persönliche Kopplung erkannt. Access-Token bleibt erhalten.'; pair_found='Vorhandener Pairing-Code erkannt und beibehalten.';
        community_setup='Community-Verbindung einrichten'; server_example='Beispiel: dcs.example.de   oder   wss://dcs.example.de/ws'; server_address='Serveradresse'; insecure='Diese Verbindung ist NICHT verschlüsselt.';
        insecure_confirm='Unsicheres ws:// wirklich verwenden? Tippe JA'; pair_code='Persönlicher Pairing-Code'; shortcuts='Verknüpfungen erstellen'; shortcuts_ok='Desktop- und Startmenü-Verknüpfungen erstellt.';
        autostart_off='Windows-Autostart deaktiviert.'; autostart_on='Windows-Autostart aktiviert.'; autostart_prompt='Discord2DCS bei Windows-Anmeldung automatisch im Hintergrund starten? [J/n]';
        uninstall='Discord2DCS deinstallieren'; uninstall_hooks='DCS-Hook und Verknüpfungen entfernt.'; uninstall_delete='Die lokale Discord2DCS-Installation wird jetzt gelöscht.';
        finished='Fertig'; install_folder='Installationsordner'; version='Version'; autostart='Autostart'; on='AN'; off='AUS'; dcs_running='DCS läuft gerade. DCS einmal komplett neu starten, damit der aktualisierte Hook geladen wird.';
        starting='Discord2DCS wird jetzt gestartet ...'; done='Installation/Aktualisierung abgeschlossen.'; language_saved='Sprache wurde auf Deutsch gesetzt.';
        invalid_url='Ungültige WebSocket-Serveradresse.'; empty_server='Serveradresse darf nicht leer sein.'; empty_pair='Pairing-Code darf nicht leer sein.'; insecure_abort='Installation wegen unsicherer Serveradresse abgebrochen.';
        setup_failed='PC-Client-Setup fehlgeschlagen'; missing_dcs='Kein DCS-Saved-Games-Profil gefunden. Starte DCS einmal vollständig, beende es wieder und starte danach INSTALL.bat erneut.'; missing_pcclient='pc-client fehlt im Installationspaket'; missing_scripts='Scripts-Ordner fehlt im Installationspaket'; missing_mods='Mods-Ordner fehlt im Installationspaket'; missing_setup='setup-client.bat fehlt'; missing_hidden='start-client-hidden.vbs fehlt'; autostart_description='Discord2DCS automatisch im Hintergrund starten'; language_shortcut='Discord2DCS Sprache ändern'; start_shortcut='Discord2DCS starten'; repair_shortcut='Discord2DCS reparieren'; uninstall_shortcut='Discord2DCS deinstallieren';
    }
    en = @{
        warning='WARNING'; install_files='Install/update program files'; repair_files='Using installed program files for repair.';
        installation='Installation'; dcs_install='Install DCS hook'; dcs_files='DCS files'; python_check='Check Python 3.12 and PC client'; python_ready='Python environment and dependencies are ready.';
        legacy_ok='Existing pairing imported from previous installation'; legacy_warn='Old config.json could not be imported automatically'; configured='PC client configured.';
        token_found='Existing personal pairing detected. Access token will be kept.'; pair_found='Existing pairing code detected and kept.';
        community_setup='Set up community connection'; server_example='Example: dcs.example.com   or   wss://dcs.example.com/ws'; server_address='Server address'; insecure='This connection is NOT encrypted.';
        insecure_confirm='Really use insecure ws://? Type YES'; pair_code='Personal pairing code'; shortcuts='Create shortcuts'; shortcuts_ok='Desktop and Start Menu shortcuts created.';
        autostart_off='Windows autostart disabled.'; autostart_on='Windows autostart enabled.'; autostart_prompt='Start Discord2DCS automatically in the background when Windows signs in? [Y/n]';
        uninstall='Uninstall Discord2DCS'; uninstall_hooks='DCS hook and shortcuts removed.'; uninstall_delete='The local Discord2DCS installation will now be deleted.';
        finished='Done'; install_folder='Installation folder'; version='Version'; autostart='Autostart'; on='ON'; off='OFF'; dcs_running='DCS is currently running. Restart DCS completely so the updated hook is loaded.';
        starting='Discord2DCS will now start ...'; done='Installation/update completed.'; language_saved='Language set to English.';
        invalid_url='Invalid WebSocket server address.'; empty_server='Server address must not be empty.'; empty_pair='Pairing code must not be empty.'; insecure_abort='Installation cancelled because of insecure server address.';
        setup_failed='PC client setup failed'; missing_dcs='No DCS Saved Games profile was found. Start DCS once, close it completely, then run INSTALL.bat again.'; missing_pcclient='pc-client is missing from the installation package'; missing_scripts='Scripts folder is missing from the installation package'; missing_mods='Mods folder is missing from the installation package'; missing_setup='setup-client.bat is missing'; missing_hidden='start-client-hidden.vbs is missing'; autostart_description='Start Discord2DCS automatically in the background'; language_shortcut='Discord2DCS Language'; start_shortcut='Start Discord2DCS'; repair_shortcut='Repair Discord2DCS'; uninstall_shortcut='Uninstall Discord2DCS';
    }
}
function T([string]$Key) {
    $value = $Texts[$Language][$Key]
    if ($null -eq $value) { return $Key }
    return [string]$value
}

try { $Host.UI.RawUI.WindowTitle = "Discord2DCS $Mode $Version [$Language]" } catch {}

function Write-Step([string]$Text) {
    Write-Host "`n==> $Text" -ForegroundColor Cyan
}

function Write-Ok([string]$Text) {
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Write-Warn([string]$Text) {
    Write-Host ("[" + (T 'warning') + "] " + $Text) -ForegroundColor Yellow
}

function Normalize-WebSocketUrl([string]$InputUrl) {
    $value = $InputUrl.Trim()
    if ([string]::IsNullOrWhiteSpace($value)) { throw (T 'empty_server') }

    if ($value -match '^wss?://') {
        $normalized = $value.TrimEnd('/')
        try {
            $uri = [System.Uri]$normalized
            if ([string]::IsNullOrWhiteSpace($uri.AbsolutePath) -or $uri.AbsolutePath -eq '/') {
                return "$normalized/ws"
            }
        } catch {
            throw (T 'invalid_url')
        }
        return $normalized
    }

    return "wss://${value.TrimEnd('/')}/ws"
}

function Get-DcsSavedGamesTargets {
    $savedGames = Join-Path $env:USERPROFILE 'Saved Games'
    $targets = @()
    if (Test-Path $savedGames) {
        $targets = @(Get-ChildItem -Path $savedGames -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq 'DCS' -or $_.Name -like 'DCS.*' } |
            Sort-Object FullName)
    }

    if (-not $targets -or $targets.Count -eq 0) {
        throw (T 'missing_dcs')
    }
    return @($targets)
}

function Read-State {
    if (-not (Test-Path $StatePath)) { return $null }
    try { return Get-Content -Raw -Path $StatePath | ConvertFrom-Json } catch { return $null }
}

function Write-State([System.IO.DirectoryInfo[]]$Targets, [bool]$AutostartEnabled) {
    New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
    $state = [ordered]@{
        version = $Version
        installed_at = (Get-Date).ToString('o')
        install_root = $InstallRoot
        dcs_targets = @($Targets | ForEach-Object { $_.FullName })
        autostart = $AutostartEnabled
        language = $Language
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($StatePath, (($state | ConvertTo-Json -Depth 5) + [Environment]::NewLine), $utf8NoBom)
}

function Stop-InstalledClient {
    $pidPath = Join-Path $InstalledClient 'client.pid'
    if (-not (Test-Path $pidPath)) { return }
    try {
        $clientPid = [int](Get-Content -Raw -Path $pidPath).Trim()
        if ($clientPid -gt 0) {
            $proc = Get-Process -Id $clientPid -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $clientPid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 300
            }
        }
    } catch {}
    Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
}

function Sync-InstallFiles {
    Write-Step (T 'install_files')
    $sourceFull = [System.IO.Path]::GetFullPath($SourceRoot).TrimEnd('\')
    $installFull = [System.IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
    if ($sourceFull -ieq $installFull) {
        Write-Ok (T 'repair_files')
        return
    }
    New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $InstalledClient | Out-Null
    New-Item -ItemType Directory -Force -Path $InstalledScripts | Out-Null

    $sourceClient = Join-Path $SourceRoot 'pc-client'
    if (-not (Test-Path $sourceClient)) { throw ((T 'missing_pcclient') + ": $sourceClient") }

    $preserve = @('config.json','Discord2DCS-Client.log','client.pid')
    Get-ChildItem -Path $sourceClient -File | ForEach-Object {
        if ($preserve -notcontains $_.Name) {
            Copy-Item $_.FullName (Join-Path $InstalledClient $_.Name) -Force
        }
    }
    $sourceLocales = Join-Path $sourceClient 'locales'
    if (Test-Path $sourceLocales) {
        $targetLocales = Join-Path $InstalledClient 'locales'
        if (Test-Path $targetLocales) { Remove-Item $targetLocales -Recurse -Force }
        Copy-Item $sourceLocales $targetLocales -Recurse -Force
    }


    $sourceAssets = Join-Path $SourceRoot 'assets'
    if (Test-Path $sourceAssets) {
        if (Test-Path $InstalledAssets) { Remove-Item $InstalledAssets -Recurse -Force }
        Copy-Item $sourceAssets $InstalledAssets -Recurse -Force
    }

    $sourceScripts = Join-Path $SourceRoot 'Scripts'
    if (-not (Test-Path $sourceScripts)) { throw ((T 'missing_scripts') + ": $sourceScripts") }
    if (Test-Path $InstalledScripts) { Remove-Item $InstalledScripts -Recurse -Force }
    Copy-Item $sourceScripts $InstalledScripts -Recurse -Force

    $sourceMods = Join-Path $SourceRoot 'Mods'
    if (-not (Test-Path $sourceMods)) { throw ((T 'missing_mods') + ": $sourceMods") }
    if (Test-Path $InstalledMods) { Remove-Item $InstalledMods -Recurse -Force }
    Copy-Item $sourceMods $InstalledMods -Recurse -Force

    foreach ($name in @('installer.ps1','INSTALL.bat','UPDATE.bat','REPAIR.bat','UNINSTALL.bat','AUTOSTART-AN.bat','AUTOSTART-AUS.bat','LANGUAGE.bat','README.md','README_EN.md','DCS-USER-FILES-DESCRIPTION.txt')) {
        $src = Join-Path $SourceRoot $name
        if (Test-Path $src) { Copy-Item $src (Join-Path $InstallRoot $name) -Force }
    }

    Write-Ok ((T 'installation') + ": $InstallRoot")
}

function Install-DcsScripts([System.IO.DirectoryInfo[]]$Targets) {
    Write-Step (T 'dcs_install')
    foreach ($target in $Targets) {
        $targetScripts = Join-Path $target.FullName 'Scripts'
        New-Item -ItemType Directory -Force -Path $targetScripts | Out-Null
        Copy-Item -Path (Join-Path $InstalledScripts '*') -Destination $targetScripts -Recurse -Force

        $sourceMod = Join-Path $InstalledMods 'tech\Discord2DCS'
        $targetTech = Join-Path $target.FullName 'Mods\\tech'
        $targetMod = Join-Path $targetTech 'Discord2DCS'
        New-Item -ItemType Directory -Force -Path $targetTech | Out-Null
        if (Test-Path $targetMod) { Remove-Item $targetMod -Recurse -Force }
        Copy-Item $sourceMod $targetMod -Recurse -Force

        Write-Ok ((T 'dcs_files') + ": $targetScripts")
        Write-Ok ("DCS Special Options: " + $targetMod)
    }
}

function Remove-DcsScripts {
    $targets = @()
    $state = Read-State
    if ($state -and $state.dcs_targets) {
        foreach ($path in @($state.dcs_targets)) {
            if (Test-Path $path) { $targets += Get-Item $path }
        }
    }
    if (-not $targets) { $targets = Get-DcsSavedGamesTargets }

    foreach ($target in $targets) {
        $hook = Join-Path $target.FullName 'Scripts\Hooks\Discord2DCS.lua'
        $uiDir = Join-Path $target.FullName 'Scripts\Discord2DCS'
        $modDir = Join-Path $target.FullName 'Mods\\tech\\Discord2DCS'
        Remove-Item $hook -Force -ErrorAction SilentlyContinue
        Remove-Item $uiDir -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item $modDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Run-ClientSetup {
    Write-Step (T 'python_check')
    $setup = Join-Path $InstalledClient 'setup-client.bat'
    if (-not (Test-Path $setup)) { throw ((T 'missing_setup') + ": $setup") }
    & $setup '--silent'
    if ($LASTEXITCODE -ne 0) { throw ((T 'setup_failed') + " (Code $LASTEXITCODE).") }
    Write-Ok (T 'python_ready')
}

function Import-LegacyConfigFromDesktopShortcut {
    $newConfig = Join-Path $InstalledClient 'config.json'
    if (Test-Path $newConfig) { return }
    try {
        $desktopLink = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Discord2DCS.lnk'
        if (-not (Test-Path $desktopLink)) { return }
        $shell = New-Object -ComObject WScript.Shell
        $oldShortcut = $shell.CreateShortcut($desktopLink)
        $oldDir = [string]$oldShortcut.WorkingDirectory
        if ([string]::IsNullOrWhiteSpace($oldDir) -and $oldShortcut.TargetPath) {
            $oldDir = Split-Path -Parent $oldShortcut.TargetPath
        }
        if ([string]::IsNullOrWhiteSpace($oldDir)) { return }
        if ([System.IO.Path]::GetFullPath($oldDir).TrimEnd('\') -ieq [System.IO.Path]::GetFullPath($InstalledClient).TrimEnd('\')) { return }
        $oldConfig = Join-Path $oldDir 'config.json'
        if (Test-Path $oldConfig) {
            Copy-Item $oldConfig $newConfig -Force
            Write-Ok ((T 'legacy_ok') + ": $oldDir")
        }
    } catch {
        Write-Warn ((T 'legacy_warn') + ": $($_.Exception.Message)")
    }
}

function Get-ExistingConfig {
    $configPath = Join-Path $InstalledClient 'config.json'
    if (-not (Test-Path $configPath)) { return $null }
    try { return Get-Content -Raw -Path $configPath | ConvertFrom-Json } catch { return $null }
}

function Write-NewClientConfig([string]$Url, [string]$PairCode) {
    $configPath = Join-Path $InstalledClient 'config.json'
    if (Test-Path $configPath) {
        Copy-Item $configPath "$configPath.bak" -Force
    }
    $config = [ordered]@{
        vps_url = $Url
        pairing_code = $PairCode.Trim()
        access_token = ''
        client_name = $env:USERNAME
        dcs_host = '127.0.0.1'
        dcs_port = 8765
        reconnect_seconds = 3.0
        tls_ca_file = ''
        queue_size = 50
        log_level = 'INFO'
        language = $Language
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($configPath, (($config | ConvertTo-Json -Depth 4) + [Environment]::NewLine), $utf8NoBom)
    Write-Ok (T 'configured')
}

function Update-ConfiguredLanguage {
    $configPath = Join-Path $InstalledClient 'config.json'
    if (Test-Path $configPath) {
        try {
            $cfg = Get-Content -Raw -Path $configPath | ConvertFrom-Json
            $cfg | Add-Member -NotePropertyName language -NotePropertyValue $Language -Force
            $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
            [System.IO.File]::WriteAllText($configPath, (($cfg | ConvertTo-Json -Depth 8) + [Environment]::NewLine), $utf8NoBom)
        } catch { Write-Warn $_.Exception.Message }
    }
}

function Write-DcsLanguage([System.IO.DirectoryInfo[]]$Targets) {
    foreach ($target in $Targets) {
        $langPath = Join-Path $target.FullName 'Scripts\Discord2DCS\language.txt'
        $parent = Split-Path -Parent $langPath
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        [System.IO.File]::WriteAllText($langPath, ($Language + [Environment]::NewLine), (New-Object System.Text.UTF8Encoding($false)))
    }
}

function Ensure-ConnectionConfig {
    $existing = Get-ExistingConfig
    if ($existing -and -not [string]::IsNullOrWhiteSpace([string]$existing.access_token)) {
        Write-Ok (T 'token_found')
        return
    }
    if ($existing -and -not [string]::IsNullOrWhiteSpace([string]$existing.pairing_code)) {
        Write-Ok (T 'pair_found')
        return
    }

    Write-Step (T 'community_setup')
    Write-Host (T 'server_example')
    $serverInput = Read-Host (T 'server_address')
    $url = Normalize-WebSocketUrl $serverInput
    if ($url -like 'ws://*') {
        Write-Warn (T 'insecure')
        $confirm = Read-Host (T 'insecure_confirm')
        if ($confirm.Trim().ToUpperInvariant() -notin @('JA','YES','Y')) { throw (T 'insecure_abort') }
    }
    $pairCode = Read-Host (T 'pair_code')
    if ([string]::IsNullOrWhiteSpace($pairCode)) { throw (T 'empty_pair') }
    Write-NewClientConfig -Url $url -PairCode $pairCode
}

function Get-StartupFolder {
    return [Environment]::GetFolderPath('Startup')
}

function Get-AutostartShortcutPath {
    return Join-Path (Get-StartupFolder) $StartupName
}

function Is-AutostartEnabled {
    return Test-Path (Get-AutostartShortcutPath)
}

function Set-Autostart([bool]$Enabled) {
    $icon = Join-Path $InstalledAssets 'Discord2DCS.ico'
    $shortcutPath = Get-AutostartShortcutPath
    if (-not $Enabled) {
        Remove-Item $shortcutPath -Force -ErrorAction SilentlyContinue
        Write-Ok (T 'autostart_off')
        return
    }
    $vbs = Join-Path $InstalledClient 'start-client-hidden.vbs'
    if (-not (Test-Path $vbs)) { throw (T 'missing_hidden') }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "$env:SystemRoot\System32\wscript.exe"
    $shortcut.Arguments = '"' + $vbs + '"'
    $shortcut.WorkingDirectory = $InstalledClient
    $shortcut.Description = T 'autostart_description'
    if ($icon -and (Test-Path -LiteralPath $icon)) { $shortcut.IconLocation = "$icon,0" }
    $shortcut.Save()
    Write-Ok (T 'autostart_on')
}

function Create-Shortcuts {
    $icon = Join-Path $InstalledAssets 'Discord2DCS.ico'
    Write-Step (T 'shortcuts')
    $shell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    $desktopLink = Join-Path $desktop 'Discord2DCS.lnk'
    $shortcut = $shell.CreateShortcut($desktopLink)
    $shortcut.TargetPath = Join-Path $InstalledClient 'start-client.bat'
    $shortcut.WorkingDirectory = $InstalledClient
    $shortcut.Description = 'Discord2DCS PC Client'
    if ($icon -and (Test-Path -LiteralPath $icon)) { $shortcut.IconLocation = "$icon,0" }
    $shortcut.Save()

    $programs = [Environment]::GetFolderPath('Programs')
    $menuDir = Join-Path $programs 'Discord2DCS'
    if (Test-Path $menuDir) { Remove-Item $menuDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $menuDir | Out-Null

    $links = @{}
    $links[((T 'start_shortcut') + '.lnk')] = (Join-Path $InstalledClient 'start-client.bat')
    $links[((T 'repair_shortcut') + '.lnk')] = (Join-Path $InstallRoot 'REPAIR.bat')
    $links[((T 'uninstall_shortcut') + '.lnk')] = (Join-Path $InstallRoot 'UNINSTALL.bat')
    $links[((T 'language_shortcut') + '.lnk')] = (Join-Path $InstallRoot 'LANGUAGE.bat')
    foreach ($item in $links.GetEnumerator()) {
        $lnk = $shell.CreateShortcut((Join-Path $menuDir $item.Key))
        $lnk.TargetPath = $item.Value
        $lnk.WorkingDirectory = $InstallRoot
        $lnk.Description = $item.Key.Replace('.lnk','')
        if ($icon -and (Test-Path -LiteralPath $icon)) { $lnk.IconLocation = "$icon,0" }
        $lnk.Save()
    }
    Write-Ok (T 'shortcuts_ok')
}

function Remove-Shortcuts {
    Remove-Item (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Discord2DCS.lnk') -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path ([Environment]::GetFolderPath('Programs')) 'Discord2DCS') -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Get-AutostartShortcutPath) -Force -ErrorAction SilentlyContinue
}

function Prompt-AutostartIfFirstInstall {
    $state = Read-State
    if ($Mode -in @('Update','Repair') -and $state) {
        return (Is-AutostartEnabled)
    }
    $answer = Read-Host (T 'autostart_prompt')
    return (-not ($answer.Trim().ToLowerInvariant() -in @('n','nein','no')))
}

function Start-ClientVisible {
    $start = Join-Path $InstalledClient 'start-client.bat'
    if (Test-Path $start) {
        Start-Process -FilePath $start -WorkingDirectory $InstalledClient
    }
}

function Show-Header {
    Clear-Host
    Write-Host '==============================================' -ForegroundColor DarkCyan
    Write-Host " Discord2DCS $Mode $Version" -ForegroundColor White
    Write-Host '==============================================' -ForegroundColor DarkCyan
}

Show-Header

if ($Mode -eq 'AutostartOn') {
    Set-Autostart $true
    exit 0
}
if ($Mode -eq 'AutostartOff') {
    Set-Autostart $false
    exit 0
}

if ($Mode -eq 'Language') {
    Stop-InstalledClient
    $targets = Get-DcsSavedGamesTargets
    Update-ConfiguredLanguage
    Write-DcsLanguage -Targets $targets
    Create-Shortcuts
    $autostartEnabled = Is-AutostartEnabled
    Write-State -Targets $targets -AutostartEnabled $autostartEnabled
    Write-Ok (T 'language_saved')
    if (Get-Process -Name 'DCS' -ErrorAction SilentlyContinue) { Write-Warn (T 'dcs_running') }
    Start-ClientVisible
    exit 0
}

if ($Mode -eq 'Uninstall') {
    Write-Step (T 'uninstall')
    Stop-InstalledClient
    Remove-Shortcuts
    Remove-DcsScripts
    Write-Ok (T 'uninstall_hooks')
    Write-Host (T 'uninstall_delete') -ForegroundColor Yellow
    $escaped = $InstallRoot.Replace('"','')
    Start-Process -FilePath "$env:SystemRoot\System32\cmd.exe" -ArgumentList '/c', "timeout /t 2 /nobreak >nul & rmdir /s /q `"$escaped`"" -WindowStyle Hidden
    exit 0
}

# Install / Update / Repair
Sync-InstallFiles
Stop-InstalledClient
$targets = Get-DcsSavedGamesTargets
Install-DcsScripts -Targets $targets
Write-DcsLanguage -Targets $targets
Run-ClientSetup
Import-LegacyConfigFromDesktopShortcut
Ensure-ConnectionConfig
Update-ConfiguredLanguage
Create-Shortcuts

$autostart = Prompt-AutostartIfFirstInstall
Set-Autostart $autostart
Write-State -Targets $targets -AutostartEnabled $autostart

Write-Step (T 'finished')
Write-Host ((T 'install_folder') + ": $InstallRoot") -ForegroundColor Green
Write-Host ((T 'version') + ": $Version") -ForegroundColor Green
if ($autostart) {
    Write-Host ((T 'autostart') + ': ' + (T 'on')) -ForegroundColor Green
} else {
    Write-Host ((T 'autostart') + ': ' + (T 'off')) -ForegroundColor Yellow
}

$dcsRunning = Get-Process -Name 'DCS' -ErrorAction SilentlyContinue
if ($dcsRunning) {
    Write-Warn (T 'dcs_running')
}

if ($Mode -ne 'Repair') {
    Write-Host ("`n" + (T 'starting')) -ForegroundColor Cyan
    Start-ClientVisible
}
Write-Host (T 'done') -ForegroundColor Green
exit 0
