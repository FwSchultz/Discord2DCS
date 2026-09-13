#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "[FEHLER] .env fehlt. Erst .env.example nach .env kopieren und Discord-Werte eintragen."
  exit 1
fi

DOMAIN="${1:-}"
if [[ -z "$DOMAIN" ]]; then
  read -r -p "Discord2DCS Domain/Subdomain (z.B. discord2dcs.example.com): " DOMAIN
fi
DOMAIN="${DOMAIN,,}"
DOMAIN="${DOMAIN#http://}"
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN%%/*}"

if [[ ! "$DOMAIN" =~ ^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$ ]]; then
  echo "[FEHLER] Ungueltiger Hostname: $DOMAIN"
  exit 1
fi

cp .env ".env.backup-tls-$(date +%Y%m%d-%H%M%S)"

set_env() {
  local key="$1" value="$2"
  if grep -qE "^${key}=" .env; then
    sed -i "s|^${key}=.*|${key}=${value}|" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

set_env PUBLIC_HOSTNAME "$DOMAIN"
set_env PUBLIC_WS_URL "wss://$DOMAIN/ws"
set_env TRUST_PROXY_HEADERS true
set_env REQUIRE_PROXY_TLS true
set_env WS_ALLOWED_PATHS "/ws,/"
set_env TLS_ENABLED false

echo
printf '[OK] .env fuer WSS vorbereitet:\n'
printf '     PUBLIC_WS_URL=wss://%s/ws\n' "$DOMAIN"

echo
PORTS_BUSY=0
for port in 80 443; do
  if command -v ss >/dev/null 2>&1 && ss -ltn "sport = :$port" 2>/dev/null | tail -n +2 | grep -q .; then
    echo "[INFO] Port $port ist bereits belegt."
    PORTS_BUSY=1
  fi
done

if [[ "$PORTS_BUSY" -eq 0 ]]; then
  cat <<TXT

Ports 80/443 scheinen frei zu sein.
Wenn DNS fuer $DOMAIN bereits auf diesen VPS zeigt, kannst du den mitgelieferten Caddy starten:

docker compose -f docker-compose.caddy.yml up -d --build

Danach pruefen:
curl -I https://$DOMAIN/health
TXT
else
  cat <<TXT

Auf 80/443 laeuft bereits ein Dienst. Das ist kein Fehler.
Nutze deinen bestehenden Reverse Proxy und leite nur:

  https://$DOMAIN/ws  ->  http://127.0.0.1:8766/ws

weiter. Ein Nginx-Beispiel liegt unter:
  tls/nginx-discord2dcs.conf.example

Der normale Discord2DCS-Container wird mit docker-compose.yml nur auf
127.0.0.1:8766 veroeffentlicht und ist dadurch nicht direkt aus dem Internet erreichbar.
TXT
fi
