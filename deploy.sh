#!/usr/bin/env bash
set -euo pipefail

REMOTE="datenmonster"
REMOTE_PATH="/opt/rechnungsmonster"
LOCAL_PATH="$(cd "$(dirname "$0")" && pwd)"

# ---------------------------------------------------------------------------
# Versionscheck: gepinnte Versionen mit Docker Hub vergleichen
# ---------------------------------------------------------------------------
check_versions() {
    echo "==> Prüfe Tool-Versionen …"

    local current_kosit current_verapdf
    current_kosit=$(grep -oP 'kosit-validator-xrechnung:\K\S+' "${LOCAL_PATH}/docker-compose.prod.yml" | head -1)
    current_verapdf=$(grep -oP 'verapdf/cli:\K\S+' "${LOCAL_PATH}/backend/Dockerfile" | head -1)

    local latest_kosit latest_verapdf
    latest_kosit=$(curl -sf --max-time 5 \
        "https://hub.docker.com/v2/repositories/apps4everything/kosit-validator-xrechnung/tags?page_size=25" \
        | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
tags = [t['name'] for t in data.get('results', []) if re.match(r'^\d+\.\d+\.\d+-\d+$', t['name'])]
tags.sort(key=lambda x: [int(p) for p in re.split(r'[-.]', x)], reverse=True)
print(tags[0] if tags else '')
" 2>/dev/null || echo "")

    latest_verapdf=$(curl -sf --max-time 5 \
        "https://hub.docker.com/v2/repositories/verapdf/cli/tags?page_size=25" \
        | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
tags = [t['name'] for t in data.get('results', []) if re.match(r'^v\d+\.\d+\.\d+$', t['name'])]
tags.sort(key=lambda x: [int(p) for p in x.lstrip('v').split('.')], reverse=True)
print(tags[0] if tags else '')
" 2>/dev/null || echo "")

    local outdated=0

    if [ -z "$latest_kosit" ]; then
        echo "  [?]  KoSIT Validator: ${current_kosit} (Docker Hub nicht erreichbar)"
    elif [ "$current_kosit" = "$latest_kosit" ]; then
        echo "  [OK] KoSIT Validator: ${current_kosit}"
    else
        echo "  [!!] KoSIT Validator: ${current_kosit} → ${latest_kosit} verfügbar"
        echo "       docker-compose.prod.yml + docker-compose.yml anpassen"
        outdated=1
    fi

    if [ -z "$latest_verapdf" ]; then
        echo "  [?]  veraPDF:          ${current_verapdf} (Docker Hub nicht erreichbar)"
    elif [ "$current_verapdf" = "$latest_verapdf" ]; then
        echo "  [OK] veraPDF:          ${current_verapdf}"
    else
        echo "  [!!] veraPDF:          ${current_verapdf} → ${latest_verapdf} verfügbar"
        echo "       backend/Dockerfile anpassen"
        outdated=1
    fi

    if [ "$outdated" -eq 1 ]; then
        echo ""
        read -r -p "     Trotzdem deployen? [j/N] " antwort
        if [[ ! "$antwort" =~ ^[jJ]$ ]]; then
            echo "Deploy abgebrochen."
            exit 1
        fi
    fi
    echo ""
}

check_versions

echo "==> Synchronisiere Dateien nach ${REMOTE}:${REMOTE_PATH} …"
rsync -av --delete \
  --exclude='.git/' \
  --exclude='.claude/' \
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
