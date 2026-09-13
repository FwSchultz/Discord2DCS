# Discord2DCS – Server-Admin-Anleitung

Diese Anleitung richtet sich an den Betreiber einer Community. Normale Piloten brauchen diesen Teil **nicht**.

## 1. Voraussetzungen

Empfohlen:

- Linux-VPS mit öffentlicher IPv4,
- Docker Engine + Docker Compose,
- Discord-Bot/Application,
- ein Discord-Textkanal für Discord2DCS,
- für Produktion: Domain/Subdomain + TLS-Reverse-Proxy (Nginx oder Caddy).

## 2. Discord-Bot erstellen

1. Im Discord Developer Portal eine neue Application erstellen.
2. Unter **Bot** einen Bot anlegen und den Token sicher kopieren.
3. **Message Content Intent** aktivieren – Discord2DCS liest neue Nachrichten aus dem konfigurierten Kanal.
4. Den Bot mit den Scopes `bot` und `applications.commands` auf den eigenen Discord-Server einladen.
5. Im Zielkanal mindestens **Kanal sehen**, **Nachrichten senden** und **Links einbetten** erlauben.
6. In Discord den Entwicklermodus aktivieren und Server-ID, Kanal-ID sowie die eigene Admin-User-ID kopieren.

Bot-Token niemals in Screenshots, GitHub, Support-Logs oder öffentliche ZIPs packen.

## 3. VPS-Dateien installieren

Kopiere den Ordner `vps/` z. B. nach:

```bash
/root/bots/discord2dcs
```

Dann:

```bash
cd /root/bots/discord2dcs
cp .env.example .env
nano .env
```

Mindestens anpassen:

```env
DISCORD_TOKEN=DEIN_BOT_TOKEN
DISCORD_CHANNEL_ID=DEINE_KANAL_ID
DISCORD_GUILD_ID=DEINE_SERVER_ID
ADMIN_USER_IDS=DEINE_DISCORD_USER_ID
PUBLIC_WS_URL=wss://dcs.example.de/ws
```

Optional können Admin-Rollen über `ADMIN_ROLE_IDS` freigeschaltet werden. `ALLOW_GUILD_ADMIN=false` ist der sicherere Standard.

## 4. Container starten

```bash
docker compose up -d --build
docker compose logs --tail 100 discord2dcs
```

Erwartet werden u. a. Start, Discord-Login, gekoppelter Kanal und synchronisierte Slash-Commands.

Das sichere Standard-Compose veröffentlicht WebSocket-Port 8766 nur lokal:

```text
127.0.0.1:8766->8766/tcp
```

## 5. TLS/WSS für Produktion

### Vorhandener Nginx

Leite nur `/ws` auf `http://127.0.0.1:8766` weiter. Das Beispiel liegt in:

```text
vps/tls/nginx-discord2dcs.conf.example
```

Für aktuelles Nginx sollte im TLS-Serverblock die moderne Syntax verwendet werden:

```nginx
listen 443 ssl;
listen [::]:443 ssl;
http2 on;
```

Nach Änderungen:

```bash
nginx -t
systemctl reload nginx
curl -I https://dcs.example.de/health
```

### Freie Ports 80/443

Wenn kein anderer Webserver läuft, kann der mitgelieferte Caddy-Stack verwendet werden. Caddy besorgt und erneuert das Zertifikat automatisch.

### Ohne Domain

Der derzeitige Release Candidate automatisiert einen öffentlich vertrauenswürdigen WSS-Endpunkt ohne Domain noch nicht. `docker-compose.insecure-test.yml` bzw. `ws://IP:8766` ist ausschließlich für Tests gedacht. Für eine öffentliche Community Domain/WSS verwenden, bis der No-Domain-Produktivweg fertig integriert und getestet ist.

## 6. Discord-Clientverwaltung

Die normalen Adminaufgaben laufen komplett in Discord:

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

### Typischer neuer Benutzer

`/dcs-client create` → Discord-Mitglied auswählen → Laufzeit auswählen → Pairing-Code wird als private Antwort angezeigt und nach Möglichkeit zusätzlich per DM versendet.

Die Token-Laufzeit beginnt beim erfolgreichen Pairing. Der Pairing-Code selbst ist separat zeitlich begrenzt und nur einmal verwendbar.

### Sperren

`/dcs-client revoke` sperrt den Nutzer. `enable` hebt die Sperre auf, verlängert aber keinen bereits abgelaufenen Token.

### Neuinstallation

Für einen bestehenden Nutzer `/dcs-client pairing` verwenden. Beim erfolgreichen Neu-Pairing wird der alte Access-Token ersetzt.

## 7. Daten und Backups

Persistente Daten liegen standardmäßig unter:

```text
vps/data/discord2dcs.db
```

Vor Updates:

```bash
cp .env .env.backup
cp -a data data.backup
```

Danach neue Programmdateien kopieren und:

```bash
docker compose down
docker compose up -d --build
docker compose logs --tail 100 discord2dcs
```

`.env` und `data/` bei normalen Updates nicht löschen.

## 8. Sicherheit

- `.env` niemals committen.
- SQLite-Datenbank niemals öffentlich teilen.
- Zertifikats-Private-Keys niemals committen.
- WSS/TLS für öffentliche Nutzung verwenden.
- `BRIDGE_SECRET` nur für Altclient-Migration verwenden und danach entfernen.
- Adminzugriff möglichst über konkrete `ADMIN_USER_IDS`/`ADMIN_ROLE_IDS` begrenzen.
- Regelmäßig `certbot renew --dry-run` bzw. Caddy-Zertifikatserneuerung prüfen.

## 9. VPS-Logs

```bash
docker compose logs --tail 100 discord2dcs
```

Für Live-Ausgabe:

```bash
docker compose logs -f discord2dcs
```
