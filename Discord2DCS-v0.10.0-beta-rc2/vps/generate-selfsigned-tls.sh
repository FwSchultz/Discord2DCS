#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-}"
if [[ -z "$HOST" ]]; then
  echo "Usage: ./generate-selfsigned-tls.sh <vps-dns-name-or-ip>"
  exit 1
fi

mkdir -p certs

if [[ "$HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  SAN="IP:$HOST"
else
  SAN="DNS:$HOST"
fi

openssl req -x509 -newkey rsa:3072 -sha256 -days 825 -nodes \
  -keyout certs/server.key \
  -out certs/server.crt \
  -subj "/CN=$HOST" \
  -addext "subjectAltName=$SAN"

chmod 600 certs/server.key
chmod 644 certs/server.crt

echo
echo "TLS-Dateien erstellt:"
echo "  certs/server.crt  (darf auf den Windows-PC kopiert werden)"
echo "  certs/server.key  (bleibt GEHEIM auf dem VPS)"
echo
echo "Jetzt TLS_ENABLED=true in .env setzen und Docker neu starten."
