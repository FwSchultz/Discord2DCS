# Discord2DCS 0.11.0-beta – Server Admin Guide

Normal pilots need the Community Client, **not** this server package.

## Starting from a clean server – Docker is installed automatically

On a **fresh Debian or Ubuntu VPS**, Docker does not need to be installed
manually first.

Requirements:

- Debian or Ubuntu
- root access or `sudo`
- internet access
- for secure WSS operation: a public IPv4 address and reachable ports 80/443

After extracting the package:

```bash
cd Discord2DCS-Server-v0.11.0-beta
chmod +x SETUP-SERVER.sh
sudo ./SETUP-SERVER.sh
```

If you are already logged in as `root`:

```bash
./SETUP-SERVER.sh
```

The setup automatically checks:

```text
Docker Engine available?
Docker Compose Plugin available?
Docker service running?
```

On a fresh Debian/Ubuntu host it automatically installs, when required:

```text
docker-ce
docker-ce-cli
containerd.io
docker-buildx-plugin
docker-compose-plugin
```

Docker is then enabled, started and verified before Discord2DCS configuration
continues.

> **Important:** If an existing/third-party Docker installation is detected,
> the installer does not silently remove it. This avoids putting existing
> containers at risk.


## Quick start

On a Linux VPS with Docker + Docker Compose:

```bash
chmod +x SETUP-SERVER.sh
./SETUP-SERVER.sh
```

After the Discord Bot Token, Guild ID, text-channel ID and admin User ID, choose:

```text
How should Discord2DCS be reachable?

[1] Domain / hostname
[2] Public IP without a domain (secure WSS)
[3] Insecure test mode
```

### 1 – Domain / hostname
The pilot receives e.g. `dcs.example.com`. The client automatically uses `wss://dcs.example.com/ws`. If ports 80/443 are free, the setup starts the bundled Caddy stack. If they are already occupied, Discord2DCS stays on `127.0.0.1:8766` and a generated Nginx config is provided.

### 2 – Public IP without a domain
The pilot receives e.g. `203.0.113.25`; the client uses `wss://203.0.113.25/ws` automatically.

On Debian/Ubuntu the setup configures Nginx, Certbot 5.4+, a publicly trusted Let's Encrypt IP certificate using the required `shortlived` profile, a twice-daily renewal check and automatic Nginx reload after renewal.

Requirements: fixed public IPv4, public TCP ports 80/443, run setup as root, and ports 80/443 must not be occupied by a non-Nginx service.

IP certificates are short-lived (about 160 hours), so renewal automation must stay enabled.

### 3 – Insecure test mode
Uses `ws://PUBLIC-IP:8766/ws`. This is unencrypted and for temporary testing only. The Windows installer warns the pilot and requires explicit confirmation.

## What to give pilots
At the end, the setup prints the exact server address to send to pilots and writes `vps/SERVER-INFO.txt`. Then create a one-time pairing code with `/dcs-client create`.

## Supported client input

```text
Domain:       dcs.example.com
Secure IP:    203.0.113.25
Test only:    ws://203.0.113.25:8766/ws
```

## Discord administration
Use `/dcs-client create`, `list`, `info`, `panel`, `set-expiry`, `extend`, `revoke`, `enable`, `pairing`, `delete`, `pairings`, `cancel-pairing`, `adopt`, and `audit`.
