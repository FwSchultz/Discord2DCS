#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"
VERSION="0.11.0-beta"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"
SERVER_INFO="SERVER-INFO.txt"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

printf '\nDiscord2DCS Server Setup %s\n' "$VERSION"
printf '========================================\n\n'
printf '[1] Deutsch\n[2] English\n'
read -r -p '> ' LANG_CHOICE
[[ "$LANG_CHOICE" == "2" ]] && LANG_CODE='en' || LANG_CODE='de'

tr() {
  local key="$1"
  if [[ "$LANG_CODE" == 'en' ]]; then
    case "$key" in
      docker_missing) echo 'Docker + Docker Compose are not ready.';;
      docker_check) echo 'Checking Docker Engine and Docker Compose ...';;
      docker_install) echo 'Docker is missing. Installing Docker Engine + Compose Plugin automatically ...';;
      docker_root) echo 'Docker must be installed system-wide. Re-run this setup as root or with sudo.';;
      docker_os) echo 'Automatic Docker installation currently supports Debian and Ubuntu. Install Docker manually on this OS, then run the setup again.';;
      docker_codename) echo 'Could not determine the Debian/Ubuntu release codename.';;
      docker_ready) echo 'Docker Engine and Docker Compose are ready.';;
      docker_failed) echo 'Docker installation did not complete successfully.';;
      env_created) echo '.env created from .env.example.';;
      env_existing) echo 'Existing .env detected. Current values will be kept when you press Enter.';;
      discord_setup) echo 'Discord configuration';;
      token_prompt) echo 'Discord Bot Token (Enter = keep existing)';;
      guild_prompt) echo 'Discord Server/Guild ID';;
      channel_prompt) echo 'Discord text channel ID';;
      admin_prompt) echo 'Discord Admin User ID';;
      invalid_id) echo 'This value must contain only digits.';;
      reach_title) echo 'How should Discord2DCS be reachable?';;
      mode1) echo '[1] Domain / hostname';;
      mode2) echo '[2] Public IP without a domain (secure WSS)';;
      mode3) echo '[3] Insecure test mode';;
      domain_prompt) echo 'Domain/hostname (e.g. dcs.example.com)';;
      ip_prompt) echo 'Public IPv4 address';;
      email_prompt) echo "Email for Let's Encrypt (Enter = no email)";;
      invalid_domain) echo 'Invalid hostname.';;
      invalid_ip) echo 'Invalid public IPv4 address.';;
      ports_free) echo 'Ports 80/443 appear to be free. Caddy will be used for automatic HTTPS.';;
      ports_busy) echo 'Ports 80/443 are already in use. Discord2DCS will start locally; use the generated Nginx config with your existing reverse proxy.';;
      ip_root) echo 'Secure IP mode must configure Nginx/Certbot on the host. Run this script as root (sudo bash setup-server.sh).';;
      ip_ports) echo 'Port 80 or 443 is used by a service other than Nginx. Secure IP setup cannot continue automatically.';;
      installing) echo 'Installing/checking Nginx and Certbot 5.4+ ...';;
      cert_request) echo "Requesting a Let's Encrypt short-lived IP certificate ...";;
      cert_fail) echo 'Certificate request failed. Make sure TCP port 80 is publicly reachable and this IP belongs to this server.';;
      insecure_warn) echo 'WARNING: This mode is unencrypted and intended only for temporary testing.';;
      finished) echo 'Setup completed.';;
      give_pilots) echo 'GIVE THIS SERVER ADDRESS TO YOUR PILOTS';;
      pairing) echo 'Create a pairing code in Discord with /dcs-client create';;
      health) echo 'Health check';;
      *) echo "$key";;
    esac
  else
    case "$key" in
      docker_missing) echo 'Docker + Docker Compose sind noch nicht einsatzbereit.';;
      docker_check) echo 'Docker Engine und Docker Compose werden geprüft ...';;
      docker_install) echo 'Docker fehlt. Docker Engine + Compose Plugin werden automatisch installiert ...';;
      docker_root) echo 'Docker muss systemweit installiert werden. Starte dieses Setup erneut als root oder mit sudo.';;
      docker_os) echo 'Die automatische Docker-Installation unterstützt derzeit Debian und Ubuntu. Installiere Docker auf diesem System manuell und starte das Setup danach erneut.';;
      docker_codename) echo 'Debian-/Ubuntu-Versionscodename konnte nicht ermittelt werden.';;
      docker_ready) echo 'Docker Engine und Docker Compose sind einsatzbereit.';;
      docker_failed) echo 'Die Docker-Installation wurde nicht erfolgreich abgeschlossen.';;
      env_created) echo '.env wurde aus .env.example erstellt.';;
      env_existing) echo 'Vorhandene .env erkannt. Mit Enter bleiben vorhandene Werte erhalten.';;
      discord_setup) echo 'Discord-Konfiguration';;
      token_prompt) echo 'Discord Bot Token (Enter = vorhandenen behalten)';;
      guild_prompt) echo 'Discord Server/Guild-ID';;
      channel_prompt) echo 'Discord Textkanal-ID';;
      admin_prompt) echo 'Discord Admin Benutzer-ID';;
      invalid_id) echo 'Dieser Wert darf nur Ziffern enthalten.';;
      reach_title) echo 'Wie soll Discord2DCS erreichbar sein?';;
      mode1) echo '[1] Domain / Hostname';;
      mode2) echo '[2] Öffentliche IP ohne Domain (sicheres WSS)';;
      mode3) echo '[3] Unsicherer Testmodus';;
      domain_prompt) echo 'Domain/Hostname (z.B. dcs.example.de)';;
      ip_prompt) echo 'Öffentliche IPv4-Adresse';;
      email_prompt) echo "E-Mail für Let's Encrypt (Enter = ohne E-Mail)";;
      invalid_domain) echo 'Ungültiger Hostname.';;
      invalid_ip) echo 'Ungültige öffentliche IPv4-Adresse.';;
      ports_free) echo 'Ports 80/443 scheinen frei zu sein. Caddy wird für automatisches HTTPS verwendet.';;
      ports_busy) echo 'Ports 80/443 sind bereits belegt. Discord2DCS startet lokal; nutze die erzeugte Nginx-Konfiguration mit deinem vorhandenen Reverse Proxy.';;
      ip_root) echo 'Der sichere IP-Modus muss Nginx/Certbot auf dem Host konfigurieren. Starte das Skript als root (sudo bash setup-server.sh).';;
      ip_ports) echo 'Port 80 oder 443 wird von einem anderen Dienst als Nginx benutzt. Der sichere IP-Modus kann nicht automatisch fortfahren.';;
      installing) echo 'Nginx und Certbot 5.4+ werden installiert/geprüft ...';;
      cert_request) echo "Let's-Encrypt-IP-Zertifikat (shortlived) wird angefordert ...";;
      cert_fail) echo 'Zertifikatsanforderung fehlgeschlagen. Prüfe, ob TCP-Port 80 öffentlich erreichbar ist und die IP zu diesem Server gehört.';;
      insecure_warn) echo 'WARNUNG: Dieser Modus ist unverschlüsselt und nur für temporäre Tests gedacht.';;
      finished) echo 'Einrichtung abgeschlossen.';;
      give_pilots) echo 'DIESE SERVERADRESSE AN DEINE PILOTEN WEITERGEBEN';;
      pairing) echo 'Pairing-Code in Discord mit /dcs-client create erzeugen';;
      health) echo 'Health-Check';;
      *) echo "$key";;
    esac
  fi
}

ok(){ printf "${GREEN}[OK]${NC} %s\n" "$*"; }
info(){ printf "${CYAN}[INFO]${NC} %s\n" "$*"; }
warn(){ printf "${YELLOW}[WARN]${NC} %s\n" "$*"; }
err(){ printf "${RED}[ERROR]${NC} %s\n" "$*" >&2; }
step(){ printf "\n${CYAN}==> %s${NC}\n" "$*"; }

docker_is_ready() {
  command -v docker >/dev/null 2>&1 &&
  docker --version >/dev/null 2>&1 &&
  docker compose version >/dev/null 2>&1
}

install_docker_apt_repo() {
  local os_id="$1" codename="$2" arch
  arch="$(dpkg --print-architecture)"

  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl

  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL "https://download.docker.com/linux/${os_id}/gpg" \
    -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/${os_id}
Suites: ${codename}
Components: stable
Architectures: ${arch}
Signed-By: /etc/apt/keyrings/docker.asc
EOF

  apt-get update
}

ensure_docker() {
  step "$(tr docker_check)"

  if docker_is_ready; then
    ok "$(tr docker_ready)"
    docker --version
    docker compose version
    return 0
  fi

  info "$(tr docker_missing)"

  if [[ "$EUID" -ne 0 ]]; then
    err "$(tr docker_root)"
    if [[ "$LANG_CODE" == "de" ]]; then
      printf 'Beispiel: sudo ./SETUP-SERVER.sh\n'
    else
      printf 'Example: sudo ./SETUP-SERVER.sh\n'
    fi
    exit 10
  fi

  if [[ ! -r /etc/os-release ]] || ! command -v apt-get >/dev/null 2>&1; then
    err "$(tr docker_os)"
    exit 11
  fi

  # shellcheck disable=SC1091
  . /etc/os-release
  OS_ID="${ID:-}"
  CODENAME="${VERSION_CODENAME:-}"

  case "$OS_ID" in
    ubuntu|debian) ;;
    *)
      err "$(tr docker_os)"
      exit 11
      ;;
  esac

  if [[ -z "$CODENAME" ]]; then
    err "$(tr docker_codename)"
    exit 12
  fi

  step "$(tr docker_install)"

  # If Docker exists but only Compose is missing, first try to add the
  # Compose v2 package without replacing the existing engine.
  if command -v docker >/dev/null 2>&1; then
    apt-get update
    if apt-cache show docker-compose-v2 >/dev/null 2>&1; then
      DEBIAN_FRONTEND=noninteractive apt-get install -y docker-compose-v2 || true
    fi
    if docker_is_ready; then
      systemctl enable --now docker >/dev/null 2>&1 || true
      ok "$(tr docker_ready)"
      docker --version
      docker compose version
      return 0
    fi
  fi

  install_docker_apt_repo "$OS_ID" "$CODENAME"

  # Fresh hosts: install the official Docker Engine packages.
  # We deliberately do not auto-remove an already installed third-party
  # Docker engine. On a non-clean host package conflicts should be handled
  # by the administrator instead of silently deleting packages.
  if command -v docker >/dev/null 2>&1; then
    DEBIAN_FRONTEND=noninteractive apt-get install -y docker-compose-plugin || true
  else
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  fi

  systemctl enable --now docker >/dev/null 2>&1 || true

  if ! docker_is_ready; then
    err "$(tr docker_failed)"
    if [[ "$LANG_CODE" == "de" ]]; then
      printf 'Prüfe: systemctl status docker --no-pager\n'
    else
      printf 'Check: systemctl status docker --no-pager\n'
    fi
    exit 13
  fi

  ok "$(tr docker_ready)"
  docker --version
  docker compose version
}

ensure_docker

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$ENV_EXAMPLE" "$ENV_FILE"
  ok "$(tr env_created)"
else
  cp "$ENV_FILE" ".env.backup-$(date +%Y%m%d-%H%M%S)"
  info "$(tr env_existing)"
fi

get_env(){ grep -m1 -E "^${1}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true; }
set_env(){
  local key="$1" value="$2" escaped
  escaped="${value//\\/\\\\}"; escaped="${escaped//&/\\&}"; escaped="${escaped//|/\\|}"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${escaped}|" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

is_placeholder(){ [[ -z "$1" || "$1" == *'DEIN_'* || "$1" == *'YOUR_'* || "$1" =~ ^1234567890 ]]; }
read_id(){
  local prompt="$1" key="$2" current input
  current="$(get_env "$key")"
  while true; do
    if is_placeholder "$current"; then
      read -r -p "$prompt: " input
    else
      read -r -p "$prompt [$current]: " input
      [[ -z "$input" ]] && input="$current"
    fi
    if [[ "$input" =~ ^[0-9]+$ ]]; then set_env "$key" "$input"; return; fi
    err "$(tr invalid_id)"
  done
}

step "$(tr discord_setup)"
CURRENT_TOKEN="$(get_env DISCORD_TOKEN)"
if is_placeholder "$CURRENT_TOKEN"; then
  while true; do
    read -r -s -p "$(tr token_prompt): " BOT_TOKEN; printf '\n'
    [[ -n "$BOT_TOKEN" ]] && break
  done
  set_env DISCORD_TOKEN "$BOT_TOKEN"
else
  read -r -s -p "$(tr token_prompt): " BOT_TOKEN; printf '\n'
  [[ -n "$BOT_TOKEN" ]] && set_env DISCORD_TOKEN "$BOT_TOKEN"
fi
read_id "$(tr guild_prompt)" DISCORD_GUILD_ID
read_id "$(tr channel_prompt)" DISCORD_CHANNEL_ID
read_id "$(tr admin_prompt)" ADMIN_USER_IDS
set_env WS_ALLOWED_PATHS '/ws,/'
set_env TLS_ENABLED false

valid_ipv4(){
  local ip="$1" IFS=. parts
  read -r -a parts <<< "$ip"
  [[ ${#parts[@]} -eq 4 ]] || return 1
  local p
  for p in "${parts[@]}"; do
    [[ "$p" =~ ^[0-9]{1,3}$ ]] || return 1
    ((10#$p >= 0 && 10#$p <= 255)) || return 1
  done
  [[ "$ip" != 0.* && "$ip" != 127.* && "$ip" != 169.254.* && "$ip" != 10.* && "$ip" != 192.168.* && ! "$ip" =~ ^172\.(1[6-9]|2[0-9]|3[01])\. ]]
}

detect_public_ipv4(){
  if command -v curl >/dev/null 2>&1; then curl -4 -fsS --max-time 5 https://api.ipify.org 2>/dev/null || true; fi
}

port_busy(){
  local port="$1"
  command -v ss >/dev/null 2>&1 || return 1
  ss -ltn "sport = :$port" 2>/dev/null | tail -n +2 | grep -q .
}

port_used_by_non_nginx(){
  local port="$1"
  command -v ss >/dev/null 2>&1 || return 1
  local out
  out="$(ss -ltnp "sport = :$port" 2>/dev/null | tail -n +2 || true)"
  [[ -z "$out" ]] && return 1
  grep -qi nginx <<< "$out" && return 1
  return 0
}

step "$(tr reach_title)"
echo "$(tr mode1)"
echo "$(tr mode2)"
echo "$(tr mode3)"
while true; do
  read -r -p '> ' MODE
  [[ "$MODE" =~ ^[123]$ ]] && break
 done

PILOT_ADDRESS=''
FULL_URL=''
MODE_LABEL=''

if [[ "$MODE" == '1' ]]; then
  while true; do
    read -r -p "$(tr domain_prompt): " DOMAIN
    DOMAIN="${DOMAIN,,}"; DOMAIN="${DOMAIN#http://}"; DOMAIN="${DOMAIN#https://}"; DOMAIN="${DOMAIN%%/*}"
    if [[ "$DOMAIN" =~ ^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$ ]]; then break; fi
    err "$(tr invalid_domain)"
  done

  set_env PUBLIC_HOSTNAME "$DOMAIN"
  set_env PUBLIC_WS_URL "wss://$DOMAIN/ws"
  set_env TRUST_PROXY_HEADERS true
  set_env REQUIRE_PROXY_TLS true
  PILOT_ADDRESS="$DOMAIN"
  FULL_URL="wss://$DOMAIN/ws"
  MODE_LABEL='Domain / Hostname'

  if ! port_busy 80 && ! port_busy 443; then
    info "$(tr ports_free)"
    docker compose -f docker-compose.caddy.yml up -d --build
    HEALTH_URL="https://$DOMAIN/health"
  else
    warn "$(tr ports_busy)"
    docker compose up -d --build
    sed "s/DOMAIN/$DOMAIN/g" tls/nginx-discord2dcs.conf.example > tls/nginx-discord2dcs.generated.conf
    HEALTH_URL="https://$DOMAIN/health"
    printf '\nGenerated: %s\n' "$(pwd)/tls/nginx-discord2dcs.generated.conf"
    if [[ "$LANG_CODE" == 'de' ]]; then
      printf 'Richte das TLS-Zertifikat in deinem vorhandenen Reverse Proxy ein und lade diese Konfiguration.\n'
    else
      printf 'Configure the TLS certificate in your existing reverse proxy and load this generated configuration.\n'
    fi
  fi

elif [[ "$MODE" == '2' ]]; then
  DETECTED_IP="$(detect_public_ipv4)"
  while true; do
    if [[ -n "$DETECTED_IP" ]]; then
      read -r -p "$(tr ip_prompt) [$DETECTED_IP]: " PUBLIC_IP
      [[ -z "$PUBLIC_IP" ]] && PUBLIC_IP="$DETECTED_IP"
    else
      read -r -p "$(tr ip_prompt): " PUBLIC_IP
    fi
    valid_ipv4 "$PUBLIC_IP" && break
    err "$(tr invalid_ip)"
  done

  if [[ "$EUID" -ne 0 ]]; then err "$(tr ip_root)"; exit 2; fi
  if port_used_by_non_nginx 80 || port_used_by_non_nginx 443; then err "$(tr ip_ports)"; exit 3; fi

  set_env PUBLIC_HOSTNAME "$PUBLIC_IP"
  set_env PUBLIC_WS_URL "wss://$PUBLIC_IP/ws"
  set_env TRUST_PROXY_HEADERS true
  set_env REQUIRE_PROXY_TLS true
  PILOT_ADDRESS="$PUBLIC_IP"
  FULL_URL="wss://$PUBLIC_IP/ws"
  MODE_LABEL='Public IP / secure WSS'

  step "$(tr installing)"
  if ! command -v nginx >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
      apt-get update
      DEBIAN_FRONTEND=noninteractive apt-get install -y nginx curl ca-certificates python3 python3-venv
    else
      err 'Automatic secure-IP setup currently supports Debian/Ubuntu hosts with apt-get.'
      exit 4
    fi
  fi
  systemctl enable --now nginx >/dev/null 2>&1 || true

  version_ge(){ [[ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" == "$2" ]]; }
  CERTBOT=''
  if command -v certbot >/dev/null 2>&1; then
    CBV="$(certbot --version 2>/dev/null | awk '{print $2}')"
    if [[ -n "$CBV" ]] && version_ge "$CBV" '5.4'; then CERTBOT="$(command -v certbot)"; fi
  fi
  if [[ -z "$CERTBOT" && -x /opt/discord2dcs-certbot/bin/certbot ]]; then
    CBV="$(/opt/discord2dcs-certbot/bin/certbot --version 2>/dev/null | awk '{print $2}')"
    if [[ -n "$CBV" ]] && version_ge "$CBV" '5.4'; then CERTBOT='/opt/discord2dcs-certbot/bin/certbot'; fi
  fi
  if [[ -z "$CERTBOT" ]]; then
    if ! command -v python3 >/dev/null 2>&1 || ! python3 -m venv --help >/dev/null 2>&1; then
      apt-get update
      DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv
    fi
    rm -rf /opt/discord2dcs-certbot
    python3 -m venv /opt/discord2dcs-certbot
    /opt/discord2dcs-certbot/bin/pip install --upgrade pip >/dev/null
    /opt/discord2dcs-certbot/bin/pip install 'certbot>=5.4,<6' >/dev/null
    CERTBOT='/opt/discord2dcs-certbot/bin/certbot'
  fi
  ok "Certbot $($CERTBOT --version | awk '{print $2}')"

  WEBROOT='/var/www/discord2dcs-certbot'
  mkdir -p "$WEBROOT/.well-known/acme-challenge"
  docker compose up -d --build

  BOOTSTRAP='/etc/nginx/conf.d/discord2dcs-ip-bootstrap.conf'
  FINALCONF='/etc/nginx/conf.d/discord2dcs-ip.conf'
  rm -f "$FINALCONF"
  cat > "$BOOTSTRAP" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $PUBLIC_IP;

    location ^~ /.well-known/acme-challenge/ {
        root $WEBROOT;
        default_type text/plain;
        try_files \$uri =404;
    }

    location = /health {
        add_header Content-Type text/plain;
        return 200 "Discord2DCS certificate setup\\n";
    }

    location / { return 404; }
}
EOF
  nginx -t
  systemctl reload nginx

  read -r -p "$(tr email_prompt): " LE_EMAIL
  step "$(tr cert_request)"
  CB_ARGS=(certonly --non-interactive --agree-tos --preferred-profile shortlived --webroot --webroot-path "$WEBROOT" --ip-address "$PUBLIC_IP")
  if [[ -n "$LE_EMAIL" ]]; then CB_ARGS+=(--email "$LE_EMAIL"); else CB_ARGS+=(--register-unsafely-without-email); fi
  if ! "$CERTBOT" "${CB_ARGS[@]}"; then err "$(tr cert_fail)"; exit 5; fi

  CERT_DIR="/etc/letsencrypt/live/$PUBLIC_IP"
  cat > "$FINALCONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $PUBLIC_IP;

    location ^~ /.well-known/acme-challenge/ {
        root $WEBROOT;
        default_type text/plain;
        try_files \$uri =404;
    }

    location / { return 301 https://$PUBLIC_IP\$request_uri; }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name $PUBLIC_IP;

    ssl_certificate     $CERT_DIR/fullchain.pem;
    ssl_certificate_key $CERT_DIR/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location = /ws {
        proxy_pass http://127.0.0.1:8766;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 75s;
        proxy_send_timeout 75s;
    }

    location = /health {
        add_header Content-Type text/plain;
        return 200 "Discord2DCS OK\\n";
    }

    location / { return 404; }
}
EOF
  rm -f "$BOOTSTRAP"
  nginx -t
  systemctl reload nginx

  mkdir -p /etc/letsencrypt/renewal-hooks/deploy
  cat > /etc/letsencrypt/renewal-hooks/deploy/discord2dcs-nginx-reload.sh <<'EOF'
#!/usr/bin/env bash
set -e
nginx -t
systemctl reload nginx
EOF
  chmod 755 /etc/letsencrypt/renewal-hooks/deploy/discord2dcs-nginx-reload.sh

  cat > /etc/systemd/system/discord2dcs-certbot-renew.service <<EOF
[Unit]
Description=Renew Discord2DCS Let's Encrypt certificate
After=network-online.target

[Service]
Type=oneshot
ExecStart=$CERTBOT renew --quiet
EOF
  cat > /etc/systemd/system/discord2dcs-certbot-renew.timer <<'EOF'
[Unit]
Description=Check Discord2DCS TLS certificate twice daily

[Timer]
OnBootSec=15min
OnUnitActiveSec=12h
RandomizedDelaySec=20min
Persistent=true

[Install]
WantedBy=timers.target
EOF
  systemctl daemon-reload
  systemctl enable --now discord2dcs-certbot-renew.timer
  HEALTH_URL="https://$PUBLIC_IP/health"

else
  DETECTED_IP="$(detect_public_ipv4)"
  while true; do
    if [[ -n "$DETECTED_IP" ]]; then
      read -r -p "$(tr ip_prompt) [$DETECTED_IP]: " PUBLIC_IP
      [[ -z "$PUBLIC_IP" ]] && PUBLIC_IP="$DETECTED_IP"
    else
      read -r -p "$(tr ip_prompt): " PUBLIC_IP
    fi
    valid_ipv4 "$PUBLIC_IP" && break
    err "$(tr invalid_ip)"
  done

  warn "$(tr insecure_warn)"
  set_env PUBLIC_HOSTNAME "$PUBLIC_IP"
  set_env PUBLIC_WS_URL "ws://$PUBLIC_IP:8766/ws"
  set_env TRUST_PROXY_HEADERS false
  set_env REQUIRE_PROXY_TLS false
  PILOT_ADDRESS="ws://$PUBLIC_IP:8766/ws"
  FULL_URL="$PILOT_ADDRESS"
  MODE_LABEL='Insecure test mode'
  docker compose -f docker-compose.insecure-test.yml up -d --build
  HEALTH_URL="n/a - test via client connection or docker compose logs"
fi

cat > "$SERVER_INFO" <<EOF
Discord2DCS Server $VERSION

Mode: $MODE_LABEL
Server address for pilots: $PILOT_ADDRESS
Full WebSocket URL: $FULL_URL

Create pilot pairing codes in Discord with:
/dcs-client create
EOF

printf '\n============================================================\n'
printf "${GREEN}%s${NC}\n" "$(tr give_pilots)"
printf '============================================================\n'
printf '%s\n' "$PILOT_ADDRESS"
printf '============================================================\n'
printf '%s\n' "$(tr pairing)"
printf '%s: %s\n' "$(tr health)" "$HEALTH_URL"
printf 'Info file: %s\n' "$(pwd)/$SERVER_INFO"
printf '\n%s\n' "$(tr finished)"
