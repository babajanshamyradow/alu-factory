#!/usr/bin/env bash
# Сборка фронтендов локально и выкладка всего на сервер.
# Использование: SERVER=alu@1.2.3.4 ./deploy/deploy.sh
set -euo pipefail
: "${SERVER:?Укажите SERVER=alu@<IP>}"
cd "$(dirname "$0")/.."

echo "==> Сборка frontend"
(cd frontend && npm ci && npm run build)
echo "==> Сборка console"
(cd console && npm ci && npm run build)

echo "==> Выкладка статики"
rsync -az --delete frontend/dist/ "$SERVER:/var/www/bawer/site/"
rsync -az --delete console/dist/  "$SERVER:/var/www/bawer/admin/"

echo "==> Выкладка бэкенда"
rsync -az --delete \
  --exclude venv --exclude config.ini --exclude media --exclude logs \
  --exclude '*.egg-info' --exclude '__pycache__' \
  backend/ "$SERVER:/opt/alu-factory/backend/"
rsync -az --delete deploy/ "$SERVER:/opt/alu-factory/deploy/"

echo "==> Зависимости и рестарт"
ssh "$SERVER" '
  set -e
  cd /opt/alu-factory
  [ -d backend/venv ] || python3 -m venv backend/venv
  backend/venv/bin/pip install -q -r backend/requirements.txt
  if systemctl list-unit-files | grep -q alu-crm; then
    sudo systemctl restart alu-crm alu-sip
  fi
'
echo "==> Готово"
