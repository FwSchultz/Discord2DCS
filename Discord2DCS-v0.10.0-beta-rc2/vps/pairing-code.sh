#!/bin/sh
set -eu

if [ $# -lt 1 ]; then
  cat <<'HELP'
Discord2DCS v0.5 Notfall-CLI

Die normale Verwaltung erfolgt jetzt in Discord ueber /dcs-client.
Dieses Script bleibt fuer Wartung/Notfaelle erhalten.

  ./pairing-code.sh clients
  ./pairing-code.sh pairings
  ./pairing-code.sh info CLIENT_ID
  ./pairing-code.sh create "Pilot Name" 90d
  ./pairing-code.sh revoke CLIENT_ID
  ./pairing-code.sh enable CLIENT_ID
  ./pairing-code.sh extend CLIENT_ID 30d
  ./pairing-code.sh set-expiry CLIENT_ID lifetime
  ./pairing-code.sh cancel-pairing PAIRING_ID
  ./pairing-code.sh adopt CLIENT_ID DISCORD_USER_ID
  ./pairing-code.sh audit --limit 20
  ./pairing-code.sh delete CLIENT_ID --yes JA_LOESCHEN
HELP
  exit 1
fi

docker compose exec -T discord2dcs python /app/pairing_admin.py "$@"
