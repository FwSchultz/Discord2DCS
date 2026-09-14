#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/vps"
exec bash ./setup-server.sh "$@"
