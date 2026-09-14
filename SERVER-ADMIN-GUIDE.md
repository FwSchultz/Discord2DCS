# Discord2DCS 0.11.0-beta – Server-Admin-Anleitung

Normale Piloten benötigen **nicht** dieses Serverpaket, sondern den Community-Client.

## Server bei Null starten – Docker wird automatisch eingerichtet

Für einen **frischen Debian- oder Ubuntu-VPS** musst du Docker nicht vorher
manuell installieren.

Voraussetzungen:

- Debian oder Ubuntu
- Root-Zugriff bzw. `sudo`
- Internetzugang
- für sicheren WSS-Betrieb: öffentliche IPv4 sowie erreichbare Ports 80/443

Nach dem Entpacken:

```bash
cd Discord2DCS-Server-v0.11.0-beta
chmod +x SETUP-SERVER.sh
sudo ./SETUP-SERVER.sh
```

Wenn du bereits als `root` angemeldet bist, reicht:

```bash
./SETUP-SERVER.sh
```

Das Setup prüft automatisch:

```text
Docker Engine vorhanden?
Docker Compose Plugin vorhanden?
Docker-Dienst aktiv?
```

Auf einem frischen Debian-/Ubuntu-System installiert es bei Bedarf automatisch:

```text
docker-ce
docker-ce-cli
containerd.io
docker-buildx-plugin
docker-compose-plugin
```

Anschließend wird Docker gestartet, für den Systemstart aktiviert und noch
einmal geprüft. Erst danach beginnt die Discord2DCS-Konfiguration.

> **Wichtig:** Erkennt das Setup auf einem bereits benutzten Server eine
> fremde/ältere Docker-Installation, entfernt es diese nicht automatisch.
> Dadurch werden bestehende Container nicht ungefragt gefährdet.


## Schnellstart

Auf einem Linux-VPS mit Docker + Docker Compose:

```bash
chmod +x SETUP-SERVER.sh
./SETUP-SERVER.sh
```

Das Setup fragt zuerst Discord Bot Token, Server-ID, Textkanal-ID und Admin-User-ID ab. Danach erscheint:

```text
Wie soll Discord2DCS erreichbar sein?

[1] Domain / Hostname
[2] Öffentliche IP ohne Domain (sicheres WSS)
[3] Unsicherer Testmodus
```

## Modus 1 – Domain / Hostname

Beispiel:

```text
dcs.meinecommunity.de
```

Discord2DCS verwendet:

```text
wss://dcs.meinecommunity.de/ws
```

Sind Port 80 und 443 frei, startet das Setup den mitgelieferten Caddy-Stack. Caddy kümmert sich automatisch um HTTPS/WSS und Zertifikatserneuerung.

Sind Port 80/443 schon belegt, startet Discord2DCS nur lokal auf `127.0.0.1:8766` und erzeugt:

```text
vps/tls/nginx-discord2dcs.generated.conf
```

für einen vorhandenen Reverse Proxy.

## Modus 2 – Öffentliche IP ohne Domain

Beispiel:

```text
203.0.113.25
```

Der Pilot kann anschließend einfach diese IP in den Client eingeben. Der Client macht daraus:

```text
wss://203.0.113.25/ws
```

Das Setup richtet auf Debian/Ubuntu automatisch ein:

- Nginx als TLS-Reverse-Proxy,
- Certbot 5.4+,
- ein öffentlich vertrauenswürdiges Let's-Encrypt-IP-Zertifikat,
- das verpflichtende `shortlived`-Zertifikatsprofil,
- automatische Zertifikatsprüfung zweimal täglich,
- Nginx-Reload nach erfolgreicher Erneuerung.

Wichtig: Let's-Encrypt-IP-Zertifikate sind nur ungefähr 6 Tage / 160 Stunden gültig. Die automatische Erneuerung darf daher nicht abgeschaltet werden.

Voraussetzungen:

- feste öffentliche IPv4-Adresse,
- TCP 80 und 443 öffentlich erreichbar,
- Setup als root (`sudo bash SETUP-SERVER.sh`),
- Port 80/443 dürfen nicht von einem anderen Dienst als Nginx belegt sein.

## Modus 3 – Unsicherer Testmodus

Der Server wird direkt veröffentlicht als:

```text
ws://203.0.113.25:8766/ws
```

Das ist **nicht verschlüsselt** und nur für temporäre Tests vorgesehen. Der Windows-Installer warnt den Piloten ausdrücklich und verlangt eine Bestätigung.

## Was bekommt der Pilot vom Admin?

Am Ende schreibt das Server-Setup deutlich:

```text
DIESE SERVERADRESSE AN DEINE PILOTEN WEITERGEBEN
================================================
203.0.113.25
================================================
```

Zusätzlich wird `vps/SERVER-INFO.txt` erzeugt.

Danach in Discord:

```text
/dcs-client create
```

Pairing-Code und Serveradresse an den Piloten senden – mehr muss der Pilot nicht konfigurieren.

## Client-Eingaben

Der aktuelle Windows-Installer akzeptiert alle drei Formen:

```text
Domain:              dcs.example.de
Sichere öffentliche IP: 203.0.113.25
Testmodus:           ws://203.0.113.25:8766/ws
```

Bei Domain und einfacher IP ergänzt der Client `wss://` und `/ws` automatisch.

## Discord-Bot vorbereiten

Im Discord Developer Portal:

1. Application/Bot anlegen.
2. **Message Content Intent** aktivieren.
3. Bot mit `bot` und `applications.commands` einladen.
4. Im Zielkanal Kanal sehen, Nachrichten senden, Links einbetten und Nachrichtenverlauf lesen erlauben.
5. Discord Entwicklermodus einschalten und Server-ID, Kanal-ID und Admin-User-ID kopieren.

## Administration

```text
/dcs-client create
/dcs-client list
/dcs-client info
/dcs-client panel
/dcs-client set-expiry
/dcs-client extend
/dcs-client revoke
/dcs-client enable
/dcs-client pairing
/dcs-client delete
/dcs-client pairings
/dcs-client cancel-pairing
/dcs-client adopt
/dcs-client audit
```

## Persistente Daten

```text
vps/data/discord2dcs.db
```

Vor einem Serverupdate `.env` und `data/` sichern. Diese Dateien niemals öffentlich auf GitHub hochladen.
