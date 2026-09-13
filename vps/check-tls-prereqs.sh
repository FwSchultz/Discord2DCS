#!/usr/bin/env bash
set -u

echo "Discord2DCS TLS-Pruefung"
echo "========================="
echo

echo "Belegte HTTP/HTTPS-Ports:"
if command -v ss >/dev/null 2>&1; then
  ss -ltnp 2>/dev/null | awk 'NR==1 || $4 ~ /:80$/ || $4 ~ /:443$/'
else
  echo "ss wurde nicht gefunden."
fi

echo
if [[ -f .env ]]; then
  echo "Relevante .env-Werte:"
  grep -E '^(PUBLIC_HOSTNAME|PUBLIC_WS_URL|WS_PORT|TRUST_PROXY_HEADERS|REQUIRE_PROXY_TLS|TLS_ENABLED)=' .env || true
else
  echo ".env nicht gefunden."
fi

echo
echo "Docker Container mit veroeffentlichten Ports:"
docker ps --format 'table {{.Names}}\t{{.Ports}}' 2>/dev/null || true
