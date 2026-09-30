#!/usr/bin/env bash
# Выкладка кода на сервер; frontend и console собираются на самом сервере.
# Использование: SERVER=alu@1.2.3.4 ./deploy/deploy.sh
set -euo pipefail
: "${SERVER:?Укажите SERVER=alu@<IP>}"
cd "$(dirname "$0")/.."

echo "==> Выкладка исходников frontend и console"
for app in frontend console; do
  rsync -az --delete \
    --exclude node_modules --exclude dist \
    "$app/" "$SERVER:/opt/alu-factory/$app/"
done

echo "==> Выкладка бэкенда"
rsync -az --delete \
  --exclude venv --exclude config.ini --exclude media --exclude logs \
  --exclude '*.egg-info' --exclude '__pycache__' \
  backend/ "$SERVER:/opt/alu-factory/backend/"
rsync -az --delete deploy/ "$SERVER:/opt/alu-factory/deploy/"

echo "==> Сборка на сервере, зависимости и рестарт"
ssh "$SERVER" '
  set -e
  cd /opt/alu-factory

  command -v npm >/dev/null || { echo "На сервере нет Node.js — см. DEPLOY.md, шаг 4"; exit 1; }

  echo "--> Сборка frontend"
  (cd frontend && npm ci --no-audit --no-fund && npm run build)
  echo "--> Сборка console"
  (cd console && npm ci --no-audit --no-fund && npm run build)

  echo "--> Публикация статики"
  rsync -a --delete frontend/dist/ /var/www/bawer/site/
  rsync -a --delete console/dist/  /var/www/bawer/admin/

  [ -d backend/venv ] || python3 -m venv backend/venv
  backend/venv/bin/pip install -q -r backend/requirements.txt
  if systemctl list-unit-files | grep -q alu-crm; then
    sudo systemctl restart alu-crm alu-sip
  fi
'
echo "==> Готово"
