Discord2DCS - Standalone Caddy TLS
==================================

Voraussetzungen:
- DNS A/AAAA fuer PUBLIC_HOSTNAME zeigt auf diesen VPS.
- TCP 80 und 443 sind von aussen erreichbar.
- UDP 443 optional fuer HTTP/3.
- Auf 80/443 laeuft noch KEIN anderer Webserver/Reverse-Proxy.

.env:
PUBLIC_HOSTNAME=discord2dcs.example.com
PUBLIC_WS_URL=wss://discord2dcs.example.com/ws
TRUST_PROXY_HEADERS=true
REQUIRE_PROXY_TLS=true
TLS_ENABLED=false

Start:
docker compose -f docker-compose.caddy.yml up -d --build

docker compose -f docker-compose.caddy.yml logs -f

Caddy besorgt und erneuert das oeffentliche TLS-Zertifikat automatisch.
