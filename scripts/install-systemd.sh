#!/usr/bin/env bash
# Install a user unit whose paths match THIS clone (not a hard-coded home).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT="$UNIT_DIR/dream-baton.service"
mkdir -p "$UNIT_DIR"

cat >"$UNIT" <<EOF
[Unit]
Description=Dream baton :8877 — Qwen default, 0731 on required/async/long
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT
EnvironmentFile=-$ROOT/.env
ExecStart=/usr/bin/python3 $ROOT/dream-baton.py
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now dream-baton.service
systemctl --user --no-pager --full status dream-baton.service | head -20
echo "installed $UNIT"
