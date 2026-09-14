# Discord2DCS – Roadmap

> Discord ↔ DCS without Alt+Tab

Diese Roadmap zeigt die geplante Weiterentwicklung von Discord2DCS nach `v0.11.0-beta`.

Der Fokus liegt bewusst zuerst auf dem **DCS-Ingame-Overlay**. Danach folgen Wartung, Server-Administration, Discord-Funktionen, Multi-Community-Unterstützung und weitere Komfortfunktionen.

---

## Status-Legende

| Status | Bedeutung |
|---|---|
| ✅ | Erledigt / veröffentlicht |
| 🔧 | In Arbeit / nächster Schwerpunkt |
| 📋 | Geplant |
| 💡 | Idee für später |

---

# ✅ Aktueller Stand – v0.11.0-beta

Bereits umgesetzt und getestet:

- Discord → DCS Nachrichten
- DCS → Discord Antworten
- eigenes DCS GameGUI-Overlay
- Overlay mit `Strg + Shift + D` ein-/ausblendbar
- DCS Special Options
- Deutsch / English
- persönliches einmaliges Pairing
- individueller Access-Token pro Pilot
- Client-Laufzeiten inkl. `Lifetime`
- Discord-Adminverwaltung über `/dcs-client`
- SQLite-Datenbank
- WSS/TLS
- Domain-/Hostname-Betrieb
- sicherer Betrieb ohne Domain über öffentliche IPv4
- Let's-Encrypt-IP-Zertifikat
- automatische Zertifikatserneuerung
- unsicherer `ws://`-Testmodus
- automatisches Docker-/Compose-Setup auf frischem Debian/Ubuntu
- Windows-Installer
- Update / Repair / Uninstall
- optionaler Windows-Autostart
- Desktop-Icon
- DCS-Special-Options-Icon
- GitHub Release
- MIT License
- Community-Client- und Server-Paket getrennt

---

# 🔧 v0.12.x – DCS-Overlay 2.0

**Höchste Priorität**

Ziel: Das Overlay soll deutlich flexibler, moderner und angenehmer im täglichen Flugbetrieb werden.

## v0.12.0-beta-rc1 – technische Basis

### Fensterposition und Größe

- [ ] Position des Overlays dauerhaft speichern
- [ ] Fenstergröße dauerhaft speichern
- [ ] Position nach DCS-Neustart wiederherstellen
- [ ] Größe nach DCS-Neustart wiederherstellen
- [ ] Position bei geänderter Bildschirmauflösung auf sichtbaren Bereich begrenzen
- [ ] Ultrawide-Auflösungen berücksichtigen
- [ ] Multi-Monitor-Setups berücksichtigen

### Dynamisches Resize

Beim Vergrößern oder Verkleinern des Fensters sollen alle Bedienelemente korrekt mitwachsen.

- [ ] Chatbereich wächst horizontal und vertikal
- [ ] Eingabefeld wächst horizontal
- [ ] `Senden` bleibt rechts positioniert
- [ ] `Leeren` bleibt rechts positioniert
- [ ] keine überlappenden Elemente
- [ ] sinnvolle minimale Fenstergröße
- [ ] sinnvolle maximale Fenstergröße

### Schriftgröße

Einstellbare Schriftgröße für Chat und Eingabefeld:

- [ ] Klein – 12
- [ ] Normal – 14
- [ ] Groß – 16
- [ ] Sehr groß – 18

Die Auswahl soll über:

```text
DCS → Einstellungen → Spezial → Discord2DCS
```

erfolgen.

### Transparenz

Einstellbare Overlay-Transparenz:

- [ ] 50 %
- [ ] 70 %
- [ ] 85 %
- [ ] 100 %

Die Lesbarkeit des Textes soll unabhängig von der Hintergrundtransparenz erhalten bleiben.

---

## v0.12.0-beta-rc2 – Komfort & Darstellung

### Zeitstempel

Optionaler Zeitstempel vor Chatnachrichten:

```text
[20:14] Freefall: Bin gleich airborne.
[20:15] Schultz: Copy.
```

- [ ] Zeitstempel EIN/AUS
- [ ] lokale Uhrzeit verwenden
- [ ] kompakte Darstellung

### Statusanzeige

Modernere und kompaktere Statusanzeige.

Beispiel:

```text
Discord2DCS                          ● ONLINE
```

oder:

```text
● DCS     ● Client     ● Discord
```

Geplant:

- [ ] DCS-Verbindung anzeigen
- [ ] Windows-Client-Verbindung anzeigen
- [ ] Discord/VPS-Verbindung anzeigen
- [ ] klare OFFLINE-/CONNECTING-/ONLINE-Zustände

### Auto-Hide

Optionales automatisches Ausblenden:

- [ ] Nie
- [ ] nach 10 Sekunden
- [ ] nach 30 Sekunden
- [ ] nach 60 Sekunden

Verhalten:

- neue Nachricht → Overlay optional automatisch einblenden
- Timeout → Overlay wieder ausblenden
- `Strg + Shift + D` funktioniert jederzeit weiterhin

### Sichtbarkeitszustand merken

Optional:

- [ ] letzten sichtbaren/versteckten Zustand speichern
- [ ] Verhalten beim DCS-Start auswählbar

### Overlay sperren

- [ ] Fensterposition sperren
- [ ] Fenstergröße sperren
- [ ] versehentliches Verschieben im Flug verhindern

### Nachrichtenanzeige

- [ ] Anzahl sichtbarer Nachrichten einstellbar
- [ ] Scrollverhalten verbessern
- [ ] neue Nachricht automatisch sichtbar machen
- [ ] lokale Anzeige weiterhin mit `Leeren` zurücksetzen

---

## v0.12.x – optischer Feinschliff

Zielbild:

```text
┌ Discord2DCS                              ● ONLINE ┐
│                                                     │
│ [20:14] Freefall: Bin gleich airborne.              │
│ [20:15] Schultz: Copy.                              │
│ [20:16] Balu: Treffpunkt WP2.                       │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Nachricht schreiben...           [Senden] [Leeren] │
└─────────────────────────────────────────────────────┘
```

Geplant:

- [ ] modernes dunkles Design
- [ ] leicht transparente Oberfläche
- [ ] dezente Cyan-/Blau-Akzente passend zum Discord2DCS-Logo
- [ ] gute Lesbarkeit bei Tag- und Nachtmissionen
- [ ] kompakter Header
- [ ] bessere visuelle Trennung von Chat und Eingabe
- [ ] Discord-Namen übersichtlicher darstellen
- [ ] optional unterschiedliche Darstellung eigener Nachrichten

---

## DCS Special Options – geplante Erweiterung

Geplant:

```text
Discord2DCS
────────────────────────────────

☑ Discord2DCS aktivieren
☑ Overlay beim DCS-Start anzeigen
☐ Systemmeldungen anzeigen

Sprache:
[ Auto                  ▼ ]

Schriftgröße:
[ Normal (14)           ▼ ]

Transparenz:
[ 85 %                  ▼ ]

Zeitstempel:
[ Ein                   ▼ ]

Auto-Hide:
[ Nie                   ▼ ]
```

Position und Fenstergröße sollen **nicht** über das Optionsmenü eingestellt werden.

Diese werden direkt ingame mit der Maus angepasst und automatisch gespeichert.

---

# 📋 v0.13.x – Update & Wartung

Ziel: Discord2DCS soll einfacher aktuell und wartbar bleiben.

- [ ] automatischer Update-Check für den Windows-Client
- [ ] Hinweis „Neue Version verfügbar“
- [ ] optionaler One-Click-Updater
- [ ] Versionsvergleich Client ↔ Server
- [ ] verständliche Meldung bei inkompatiblen Versionen
- [ ] Server-Update-Script
- [ ] automatisches Backup von `.env`
- [ ] automatisches Backup der SQLite-Datenbank
- [ ] Update-Rollback bei Fehlern
- [ ] `/dcs-client status`
- [ ] Serverversion anzeigen
- [ ] Uptime anzeigen
- [ ] Anzahl verbundener Clients anzeigen

---

# 📋 v0.14.x – Server-Setup & Administration

Ziel: Ein Serverbetreiber soll Discord2DCS mit möglichst wenig Linux-Vorkenntnissen betreiben können.

## Setup-Assistent

- [ ] bestehende Installation erkennen
- [ ] Install / Update / Repair auswählen
- [ ] Docker-Status prüfen
- [ ] Firewall prüfen
- [ ] Ports 80 / 443 prüfen
- [ ] öffentliche IPv4 automatisch erkennen
- [ ] Domainauflösung prüfen
- [ ] TLS/WSS automatisch testen
- [ ] Health-Check am Ende automatisch ausführen
- [ ] Discord-Bot-Verbindung testen
- [ ] Guild-ID prüfen
- [ ] Channel-ID prüfen
- [ ] Bot-Berechtigungen prüfen
- [ ] Admin-ID / Admin-Rolle prüfen

## Server-Werkzeuge

- [ ] `SERVER-INFO.sh`
- [ ] aktuelle Client-Adresse erneut anzeigen
- [ ] `STATUS-SERVER.sh`
- [ ] `REPAIR-SERVER.sh`
- [ ] `UPDATE-SERVER.sh`
- [ ] `UNINSTALL-SERVER.sh`
- [ ] Backup erstellen
- [ ] Backup wiederherstellen

---

# 📋 v0.15.x – Discord-Funktionen

Ziel: Mehr Flexibilität für Staffeln und Communities.

- [ ] mehrere erlaubte Discord-Kanäle
- [ ] Kanalwechsel direkt im DCS-Overlay
- [ ] Standardkanal definierbar
- [ ] rollenbasierte Kanalberechtigungen
- [ ] Pilot sieht nur freigegebene Kanäle
- [ ] Nachrichtenformat konfigurierbar
- [ ] Discord-Name übersichtlicher anzeigen
- [ ] optional DCS-Spielername ↔ Discord-Name zuordnen
- [ ] Discord-Adminpanel erweitern
- [ ] Kanalverwaltung über Discord-Kommandos

Beispiel:

```text
Discord2DCS

Kanal:
[ #flight-training ▼ ]
```

---

# 📋 v0.16.x – Multi-Community / Multi-Instance

Ziel: Ein einzelner Discord2DCS-Server soll mehrere getrennte Communities bedienen können.

Beispiel:

```text
VPS
├── Staffel Alpha
├── Staffel Bravo
└── Staffel Charlie
```

Geplant:

- [ ] mehrere Discord Guilds auf einer Serverinstanz
- [ ] getrennte Konfiguration pro Community
- [ ] getrennte Discord-Kanäle
- [ ] getrennte Admins
- [ ] getrennte Client-Daten
- [ ] getrennte Pairing-Codes
- [ ] getrennte Audit-Logs
- [ ] getrennte Laufzeiten
- [ ] eindeutige Community-ID
- [ ] optional getrennte WSS-Pfade

Beispiel:

```text
wss://server.example.de/alpha/ws
wss://server.example.de/bravo/ws
```

Damit könnte ein Betreiber mehrere kleine DCS-Staffeln auf einem einzigen VPS hosten.

---

# 📋 v0.17.x – Windows-Client GUI & Tray

Ziel: Der Windows-Client soll vollständig im Hintergrund laufen können.

## Tray-Icon

- [ ] Discord2DCS-Icon im Windows-Systemtray
- [ ] Client starten / stoppen
- [ ] Status anzeigen
- [ ] Logs öffnen
- [ ] Einstellungen öffnen
- [ ] Update prüfen
- [ ] Beenden

## Kleine Status-GUI

Beispiel:

```text
Discord2DCS

● Server verbunden
● DCS verbunden
● Pairing gültig

Server:
wss://dcs.example.de/ws

[ Logs öffnen ]
[ Einstellungen ]
[ Update prüfen ]
```

Geplant:

- [ ] Serveradresse ändern
- [ ] Sprache ändern
- [ ] Autostart ändern
- [ ] Pairing erneuern
- [ ] Client-ID anzeigen
- [ ] Token-Ablaufdatum anzeigen
- [ ] Verbindung manuell neu aufbauen

---

# 📋 v0.18.x – Sicherheit, Backup & Audit

Ziel: Sicherer und langfristig stabiler Community-Betrieb.

- [ ] Token-Rotation
- [ ] Access-Token manuell neu erzeugen
- [ ] Pairing-Rate-Limits weiter härten
- [ ] Login-/Auth-Rate-Limits
- [ ] automatische SQLite-Backups
- [ ] Backup-Rotation
- [ ] konfigurierbare Aufbewahrungsdauer
- [ ] Restore-Funktion
- [ ] abgelaufene Clients automatisch archivieren
- [ ] Audit-Log erweitern
- [ ] Admin-Aktionen besser filtern
- [ ] Warnung bei unsicherem `ws://`-Produktivbetrieb
- [ ] Security-Check im Server-Setup
- [ ] TLS-Zertifikatsstatus anzeigen
- [ ] Zertifikatsablauf überwachen

---

# 📋 v0.19.x – Release Candidate für v1.0

Ab diesem Punkt keine großen neuen Features mehr.

Fokus:

- [ ] Bugfixes
- [ ] Performance
- [ ] Stabilität
- [ ] Dokumentation
- [ ] Migration

## Testmatrix

- [ ] Windows 10
- [ ] Windows 11
- [ ] DCS World 2.9+
- [ ] Single-Monitor
- [ ] Multi-Monitor
- [ ] Ultrawide
- [ ] Debian Server
- [ ] Ubuntu Server
- [ ] Domain + WSS
- [ ] öffentliche IPv4 ohne Domain + WSS
- [ ] unsicherer Testmodus
- [ ] Upgrade von älteren Beta-Versionen
- [ ] Neuinstallation
- [ ] Repair
- [ ] Uninstall / Reinstall
- [ ] Zertifikatserneuerung
- [ ] DB-Backup / Restore
- [ ] DE / EN vollständig prüfen

---

# 🎯 v1.0.0 – Stable Release

Ziel: Discord2DCS ist für den normalen Community-Betrieb vollständig stabil und dokumentiert.

Geplant für v1.0:

- [ ] stabiles DCS-Overlay 2.0
- [ ] stabile Clientinstallation
- [ ] stabiler Server-Installer
- [ ] Domain-Betrieb
- [ ] sichere öffentliche IPv4 ohne Domain
- [ ] automatisierte Zertifikatserneuerung
- [ ] Update-System
- [ ] Backup / Restore
- [ ] Multi-Channel
- [ ] Windows-Tray-GUI
- [ ] vollständige DE-/EN-Dokumentation
- [ ] Migration Beta → Stable ohne neues Pairing
- [ ] GitHub Release
- [ ] DCS User Files Release

---

# 💡 Nach v1.0 – mögliche Erweiterungen

Diese Punkte sind Ideen und noch nicht fest eingeplant.

## Web-Dashboard

- Weboberfläche für Serveradmins
- Clientverwaltung
- Online-/Offline-Status
- Tokenlaufzeiten
- Audit-Logs
- Backups
- Serverstatus

## DCS-Server-Integration

Mögliche automatische Meldungen:

```text
Mission gestartet
Mission beendet
Server neu gestartet
Spieler verbunden
Spieler getrennt
```

## Missionsabhängige Discord-Kanäle

- automatischer Missionskanal
- Trainingskanäle
- Eventkanäle
- temporäre Kanäle

## SRS-Integration

Nur wenn ein klarer Mehrwert entsteht.

Mögliche Ideen:

- SRS-Status anzeigen
- Frequenzinformationen
- gemeinsame Community-Statusinformationen

## Plugin- / API-System

- externe Community-Tools anbinden
- eigene Bots
- Webhooks
- REST/API
- optionale Module

## Statistiken

Nur ohne unnötige Speicherung privater Nachrichteninhalte.

Mögliche Werte:

- verbundene Clients
- Nachrichtenanzahl
- Uptime
- Verbindungsqualität
- Serverstatus

---

# Entwicklungsprinzipien

Bei neuen Funktionen gelten weiterhin folgende Ziele:

1. **Einfach für Piloten**
2. **Einfach für Serverbetreiber**
3. **Keine unnötigen Portfreigaben auf Gaming-PCs**
4. **Sichere WSS/TLS-Verbindungen für Produktion**
5. **Keine Secrets im GitHub-Repository**
6. **Deutsch und Englisch**
7. **Bestehende Installationen möglichst ohne Neu-Pairing aktualisieren**
8. **Keine Breaking Changes ohne sauberen Migrationsweg**
9. **Neue Funktionen zuerst als Release Candidate testen**
10. **Stabilität vor Feature-Menge**

---

# Nächster Entwicklungsschritt

## 🔧 Discord2DCS v0.12.0-beta-rc1

Als Nächstes:

```text
DCS-Overlay
├── Position speichern
├── Größe speichern
├── dynamisches Resize
├── Schriftgröße
└── Transparenz
```

Danach folgt `v0.12.0-beta-rc2` mit Zeitstempel, Statusanzeige, Auto-Hide und optischem Feinschliff.
