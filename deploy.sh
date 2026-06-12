#!/usr/bin/env bash
set -euo pipefail

REMOTE="datenmonster"
REMOTE_PATH="/opt/rechnungsmonster"
LOCAL_PATH="$(cd "$(dirname "$0")" && pwd)"

echo "==> Synchronisiere Dateien nach ${REMOTE}:${REMOTE_PATH} …"
rsync -av --delete \
  --exclude='.git/' \
  --exclude='.env' \
  --exclude='venv/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='node_modules/' \
  --exclude='frontend/dist/' \
  --exclude='uploads/' \
  --exclude='reports/' \
  --exclude='data/' \
  --exclude='validator/runtime/' \
  "${LOCAL_PATH}/" "${REMOTE}:${REMOTE_PATH}/"

echo "==> Baue und starte Container neu …"
ssh "${REMOTE}" "cd ${REMOTE_PATH} && \
  docker compose -f docker-compose.prod.yml build && \
  docker compose -f docker-compose.prod.yml up -d"

echo "==> Deployment abgeschlossen."
