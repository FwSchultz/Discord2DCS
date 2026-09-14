<div align="center">
  <img src="docs/images/discord2dcs-logo.png" alt="Discord2DCS Logo" width="190">

# Discord2DCS

**Discord ↔ DCS – ohne Alt+Tab.**

![Version](https://img.shields.io/badge/version-0.11.0-beta-blue)
![DCS World](https://img.shields.io/badge/DCS%20World-2.9%2B-informational)
![Windows](https://img.shields.io/badge/client-Windows-0078D4)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Docker](https://img.shields.io/badge/server-Docker-2496ED)
![Languages](https://img.shields.io/badge/languages-DE%20%7C%20EN-success)
![License](https://img.shields.io/badge/license-MIT-green)

[English documentation](README_EN.md)
</div>

> **Public Beta:** Die Kernfunktionen und eine vollständige Neuinstallation auf einem zweiten/sauberen Windows-PC wurden erfolgreich getestet.

## Downloads

### ✈️ Für Piloten / Clients

**[⬇️ Discord2DCS Community Client v0.11.0-beta herunterladen](https://github.com/FwSchultz/Discord2DCS/releases/download/v0.11.0-beta/Discord2DCS-Community-Client-v0.11.0-beta.zip)**

Enthält den Windows-Client, DCS-Hook, Ingame-Overlay, Installer, Update/Repair und die DCS-Special-Options.

### 🖥️ Für Community-/Server-Admins

**[⬇️ Discord2DCS Server v0.11.0-beta herunterladen](https://github.com/FwSchultz/Discord2DCS/releases/download/v0.11.0-beta/Discord2DCS-Server-v0.11.0-beta.zip)**

Enthält den Discord-Bot, die WebSocket-Bridge, Docker-Setup, TLS-Beispiele sowie die Server-Einrichtungsanleitung. Unterstützt Domain, sichere öffentliche IP ohne Domain und einen unsicheren Testmodus.


## Inhaltsverzeichnis

- [Downloads](#downloads)
- [Was ist Discord2DCS?](#was-ist-discord2dcs)
- [Was brauche ich als Pilot?](#was-brauche-ich-als-pilot)
- [Installation für Piloten – Schritt für Schritt](#installation-für-piloten--schritt-für-schritt)
- [Discord2DCS in DCS benutzen](#discord2dcs-in-dcs-benutzen)
- [DCS Einstellungen → Spezial](#dcs-einstellungen--spezial)
- [Update, Reparatur, Sprache und Deinstallation](#update-reparatur-sprache-und-deinstallation)
- [Fehlersuche für Piloten](#fehlersuche-für-piloten)
- [Für Community-Admins](#für-community-admins)
- [Discord-Adminbefehle](#discord-adminbefehle)
- [Sicherheit und Datenschutz](#sicherheit-und-datenschutz)
- [Bekannte Grenzen](#bekannte-grenzen)
- [Dateien und Projektstruktur](#dateien-und-projektstruktur)

## Was ist Discord2DCS?

Discord2DCS verbindet **einen Discord-Textkanal** mit einem eigenen Chat-Overlay in DCS World.

```text
Discord-Textkanal
       ↕
Discord2DCS Bot auf dem Community-VPS
       ↕  WSS/TLS (verschlüsselt)
Discord2DCS Windows-Client
       ↕  nur lokal: 127.0.0.1:8765
DCS GameGUI-Overlay
```

Damit kannst du während des Fliegens:

- Discord-Nachrichten direkt in DCS lesen,
- aus DCS direkt in den Discord-Kanal antworten,
- das Overlay mit `Strg + Shift + D` ein- und ausblenden,
- Discord2DCS in **DCS → Einstellungen → Spezial** aktivieren oder deaktivieren,
- Deutsch oder Englisch verwenden.

Der Gaming-PC benötigt **keine eingehende Portfreigabe**. Der Windows-Client verbindet sich selbst nach außen mit dem Community-Server.

## Was brauche ich als Pilot?

Du brauchst nur:

- DCS World unter Windows,
- Internetzugang,
- die **Serveradresse oder öffentliche IP** deiner Community,
- einen **persönlichen Pairing-Code** vom Community-Admin.

Du musst **Python, Lua, Docker und GitHub nicht kennen**. Python 3.12 wird vom Installer geprüft und bei Bedarf automatisch von python.org installiert. Die digitale Signatur des Python-Installers wird vor der Installation geprüft.

## Installation für Piloten – Schritt für Schritt

➡️ **[Community-Client v0.11.0-beta direkt herunterladen](https://github.com/FwSchultz/Discord2DCS/releases/download/v0.11.0-beta/Discord2DCS-Community-Client-v0.11.0-beta.zip)**

### 1. ZIP vollständig entpacken

Starte `INSTALL.bat` **nicht direkt aus dem ZIP-Fenster**.

1. Rechtsklick auf die heruntergeladene ZIP-Datei.
2. **Alle extrahieren…** wählen.
3. Den entpackten Ordner öffnen.

### 2. `INSTALL.bat` starten

Doppelklicke auf:

```text
INSTALL.bat
```

Der Installer fragt zuerst nach der Sprache:

```text
[1] Deutsch
[2] English
```

### 3. Was automatisch installiert wird

Der Installer:

1. sucht vorhandene DCS-Profile unter `%USERPROFILE%\Saved Games\DCS*`,
2. installiert den DCS-Hook und das Overlay,
3. installiert den Tech-Mod für **DCS → Einstellungen → Spezial → Discord2DCS**,
4. prüft Python 3.12,
5. installiert bei Bedarf Python 3.12.10 automatisch von python.org,
6. erstellt eine eigene Python-Umgebung und installiert die benötigten Pakete,
7. installiert Discord2DCS nach `%LOCALAPPDATA%\Discord2DCS`,
8. erstellt Desktop- und Startmenü-Verknüpfungen mit Discord2DCS-Icon,
9. bietet optionalen Windows-Autostart an.

Wenn noch kein DCS-Saved-Games-Profil existiert, starte DCS einmal vollständig, beende es wieder und starte danach `INSTALL.bat` erneut.

### 4. Serveradresse eingeben

Vom Admin bekommst du genau eine fertige Serveradresse. Je nach Server kann das eine Domain, eine sichere öffentliche IP oder eine Test-URL sein:

```text
dcs.example.de
203.0.113.25
ws://203.0.113.25:8766/ws   # nur Testmodus
```

Bei Domain oder einfacher öffentlicher IP ergänzt der Installer automatisch `wss://` und `/ws`. `ws://` wird weiterhin deutlich als unsicher markiert.

### 5. Pairing-Code eingeben

Beispiel:

```text
D2DCS-ABCD-EFGH-IJKL-MNOP
```

Der Pairing-Code ist nur einmal verwendbar. Beim ersten erfolgreichen Verbindungsaufbau erhält dein Client einen persönlichen Access-Token. Danach ist für normale Starts kein Pairing-Code mehr nötig.

### 6. DCS neu starten

War DCS während der Installation geöffnet, DCS **komplett schließen und neu starten**.

## Discord2DCS in DCS benutzen

### Overlay öffnen oder schließen

```text
Strg + Shift + D
```

### Nachricht nach Discord senden

1. unten in das Eingabefeld klicken,
2. Nachricht schreiben,
3. `Enter` drücken oder **Senden** anklicken.

### Anzeige leeren

**Leeren** löscht nur die lokale Anzeige im Overlay. Nachrichten im Discord-Kanal werden dadurch nicht gelöscht.

### Status

- `ONLINE` – DCS, PC-Client und VPS/Discord sind verbunden.
- `PC-CLIENT` – DCS sieht den lokalen Client, aber die Verbindung zum VPS/Discord ist noch nicht vollständig bereit.
- `OFFLINE` – keine vollständige Verbindung.

Wenn DCS noch nicht läuft, meldet der PC-Client das einmal verständlich und wartet danach still im Hintergrund.

## DCS Einstellungen → Spezial

Öffne:

```text
DCS → Einstellungen → Spezial → Discord2DCS
```

Dort gibt es:

- **Discord2DCS aktivieren** – Hauptschalter für das DCS-Modul.
- **Overlay beim DCS-Start anzeigen** – aus = Overlay startet verborgen; `Strg + Shift + D` funktioniert weiterhin.
- **Systemmeldungen im Overlay anzeigen** – blendet nur interne `[System]`-Statusmeldungen ein oder aus.
- **Sprache** – `Auto`, `Deutsch` oder `English`.

Nach Änderungen DCS komplett neu starten, damit der Hook die Optionen neu einliest.

## Update, Reparatur, Sprache und Deinstallation

Discord2DCS liegt nach der Installation unter:

```text
%LOCALAPPDATA%\Discord2DCS
```

### Update

1. neue Community-ZIP herunterladen,
2. vollständig entpacken,
3. laufenden Discord2DCS-Client schließen,
4. `UPDATE.bat` aus dem **neuen Paket** starten,
5. DCS danach neu starten.

Der persönliche Access-Token bleibt erhalten. Für ein normales Update ist kein neuer Pairing-Code nötig.

### Reparatur

```text
REPAIR.bat
```

Installiert Programmdateien, Python-Umgebung, Hook und Tech-Mod erneut. Die persönliche Kopplung bleibt erhalten.

### Sprache ändern

```text
LANGUAGE.bat
```

Alternativ kann die DCS-Overlay-Sprache unter **Einstellungen → Spezial → Discord2DCS** überschrieben werden.

### Autostart

```text
AUTOSTART-AN.bat
AUTOSTART-AUS.bat
```

### Deinstallation

```text
UNINSTALL.bat
```

Entfernt den lokalen Client, Discord2DCS-Hook, Overlay, Tech-Mod und die von Discord2DCS erstellten Verknüpfungen.

## Fehlersuche für Piloten

### „DCS ist noch nicht gestartet“

Das ist kein Fehler. Starte DCS; der Client verbindet sich automatisch mit dem lokalen Hook.

### Discord2DCS erscheint nicht unter „Spezial“

1. DCS vollständig schließen.
2. `REPAIR.bat` ausführen.
3. prüfen, ob dieser Ordner existiert:

```text
%USERPROFILE%\Saved Games\DCS\Mods\tech\Discord2DCS
```

Bei einem anderen DCS-Profil kann der Ordner z. B. `DCS.openbeta` heißen.

### Overlay erscheint nicht

Prüfe unter **Einstellungen → Spezial → Discord2DCS**, ob Discord2DCS aktiviert ist. Danach DCS neu starten und `Strg + Shift + D` drücken.

### Pairing-Code ungültig oder abgelaufen

Der Admin muss mit `/dcs-client pairing` einen neuen Code erzeugen. Ein alter oder bereits verwendeter Code kann nicht wiederverwendet werden.

### Logs für Support

Windows-Client:

```text
%LOCALAPPDATA%\Discord2DCS\pc-client\Discord2DCS-Client.log
```

DCS:

```text
%USERPROFILE%\Saved Games\DCS*\Logs\Discord2DCS.log
```

Bei einer Fehlermeldung am besten **beide Logs** mitsenden.

## Für Community-Admins

➡️ **[Server-Paket v0.11.0-beta direkt herunterladen](https://github.com/FwSchultz/Discord2DCS/releases/download/v0.11.0-beta/Discord2DCS-Server-v0.11.0-beta.zip)**

Normale Piloten benötigen **keinen eigenen VPS**. Eine Community betreibt einmal zentral den Discord2DCS-Server/Bot.

Die ausführliche Anleitung steht in [SERVER-ADMIN-GUIDE.md](SERVER-ADMIN-GUIDE.md). Das Serverpaket enthält außerdem `SETUP-SERVER.sh`, das Domain, sichere öffentliche IP ohne Domain und Testmodus interaktiv einrichtet.

**Auf einem frischen Debian-/Ubuntu-VPS installiert `SETUP-SERVER.sh` Docker Engine und Docker Compose bei Bedarf automatisch.**

Kurz benötigt werden:

- Linux-VPS oder Linux-Server,
- Docker + Docker Compose,
- Discord-Bot-Token,
- Discord-Server-ID und Textkanal-ID,
- für den empfohlenen Produktivbetrieb eine WSS/TLS-Adresse über Reverse Proxy.

## Discord-Adminbefehle

Die Verwaltung erfolgt direkt in Discord über `/dcs-client`:

| Befehl | Funktion |
|---|---|
| `/dcs-client create` | neuen Nutzer + Pairing-Code anlegen |
| `/dcs-client list` | alle Clients anzeigen |
| `/dcs-client info` | Details zu einem Nutzer |
| `/dcs-client panel` | Schnellpanel mit häufigen Aktionen |
| `/dcs-client set-expiry` | Laufzeit neu setzen |
| `/dcs-client extend` | Laufzeit verlängern |
| `/dcs-client revoke` | Client sofort sperren |
| `/dcs-client enable` | Client wieder freischalten |
| `/dcs-client pairing` | neuen Pairing-Code für eine Neuinstallation erzeugen |
| `/dcs-client delete` | Client endgültig löschen |
| `/dcs-client pairings` | offene Pairings anzeigen |
| `/dcs-client cancel-pairing` | offenen Pairing-Code stornieren |
| `/dcs-client adopt` | migrierten Alt-Client einem Discord-Nutzer zuordnen |
| `/dcs-client audit` | Admin-Audit anzeigen |

Laufzeiten können z. B. `30d`, `90d`, `365d`, `8w`, ein festes Datum oder `Lifetime` sein.

## Sicherheit und Datenschutz

- Produktionsverbindungen sollten über **WSS/TLS** laufen.
- Port `8766` wird im sicheren Docker-Compose standardmäßig nur an `127.0.0.1` gebunden.
- Jeder Nutzer besitzt einen eigenen Access-Token.
- Pairing-Codes sind einmalig und zeitlich begrenzt.
- Access-Tokens und Pairing-Codes werden serverseitig nicht im Klartext gespeichert, sondern als SHA-256-Hash verglichen.
- Die SQLite-Datenbank enthält u. a. Client-ID, Anzeigename, Discord-User-ID, Status, Laufzeit, Zeitstempel und Audit-Einträge.
- `.env`, Datenbank, Zertifikate, Pairing-Codes und Access-Tokens niemals öffentlich hochladen.

## Bekannte Grenzen

- Aktuell wird **ein fest konfigurierter Discord-Textkanal** gespiegelt.
- Chatnachrichten werden nicht automatisch übersetzt.
- Die DCS-Special-Optionen werden beim Start des Hooks eingelesen; nach Änderungen DCS neu starten.
- Der Community-Client ist für Windows/DCS ausgelegt.
- Ein sicherer Betrieb ohne Domain ist über eine feste öffentliche IPv4 und ein automatisch erneuertes Let's-Encrypt-IP-Zertifikat möglich. Der unverschlüsselte `ws://IP:8766`-Modus bleibt ausschließlich für Tests vorgesehen.

## Dateien und Projektstruktur

```text
Discord2DCS/
├── INSTALL.bat / UPDATE.bat / REPAIR.bat / UNINSTALL.bat
├── installer.ps1
├── assets/                 # Logo + Windows-Icon
├── Scripts/                # DCS GameGUI-Hook + Overlay
├── Mods/tech/Discord2DCS/  # DCS Special Options + DCS-Icon
├── pc-client/              # lokaler Windows-Bridge-Client
├── vps/                    # Discord-Bot, WebSocket-Bridge, SQLite, Docker
└── docs/                   # Dokumentation/Bilder
```

## Lizenz

Discord2DCS wird unter der **MIT License** veröffentlicht. Nutzung, Änderung und Weitergabe sind unter den Bedingungen der Datei [LICENSE](LICENSE) erlaubt.
