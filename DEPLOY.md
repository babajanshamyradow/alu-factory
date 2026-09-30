# Деплой alu-factory на Ubuntu (baweraluminium.com) — полное пошаговое руководство

## 0. Контекст и итоговая схема

- Сервер: Ubuntu 22.04/24.04.
- `frontend/` и `console/` собираются **на сервере**: `deploy.sh` заливает исходники (без `node_modules`/`dist`), на сервере выполняется `npm ci && npm run build`, а `dist/` копируется в `/var/www/bawer/`. На сервере нужен Node.js 22 (см. `.nvmrc`).
- Бэкенд — два Flask-приложения: `crm` (API админки, порт 8888) и `sip` (API публичного сайта, порт 9999), запускаются через gunicorn + systemd.
- Данные: переносим локальную БД PostgreSQL и папку `backend/media` (~23 МБ).

| URL | Что обслуживает |
|---|---|
| `https://baweraluminium.com/` | статика `frontend/dist` (публичный сайт) |
| `https://baweraluminium.com/api/…` | nginx → gunicorn `sip` (127.0.0.1:9999) |
| `https://baweraluminium.com/admin/` | статика `console/dist` (админка) |
| `https://baweraluminium.com/admin-api/…` | nginx → gunicorn `crm` (127.0.0.1:8888), префикс `/admin-api` срезается |
| `https://baweraluminium.com/media/…` | nginx отдаёт файлы напрямую с диска |

**Почему `/admin-api`:** сайт и консоль оба обращаются к `/api/…`, а `/admin/login` — одновременно SPA-страница и POST-эндпоинт бэкенда. Отдельный префикс для API консоли убирает оба конфликта. `/media/` у обоих приложений — одни и те же файлы, поэтому их отдаёт nginx.

**Раскладка на сервере:**
```
/opt/alu-factory/
  backend/            # код бэкенда (rsync с Mac)
    venv/             # создаётся на сервере
    config.ini        # создаётся на сервере вручную, в git нет
    media/            # загруженные файлы
    logs/             # логи crm/sip
  deploy/             # nginx/systemd-файлы (rsync с Mac)
  frontend/           # исходники сайта, собираются на сервере
  console/            # исходники админки, собираются на сервере
/var/www/bawer/
  site/               # frontend/dist
  admin/              # console/dist
```

---

## Часть A. Изменения в коде для продакшена (уже внесены в репозиторий)

### A1. `console/vite.config.js` — base `/admin/` только для сборки
```js
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/admin/' : '/',
  plugins: [vue()],
  resolve: { … без изменений … },
  server: { … без изменений … },
}))
```

### A2. `console/src/router/index.js`
```js
history: createWebHistory(import.meta.env.BASE_URL),
```

### A3. `console/src/api/http.js`
```js
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})
```

### A4. `console/.env.production` (новый файл)
```
VITE_API_BASE=/admin-api
```
В dev переменная пустая → запросы идут как раньше через прокси Vite.

### A5. `backend/src/crm/config.py` — флаги из `config.ini`
```python
a.config['SESSION_COOKIE_SECURE'] = config['ALU_FACTORY'].getboolean('SESSION_COOKIE_SECURE', False)
…
a.debug = config['ALU_FACTORY'].getboolean('DEBUG', True)
```
Локально поведение не меняется (значения по умолчанию прежние). В `backend/example_config.ini` добавить `DEBUG` и `SESSION_COOKIE_SECURE`.

### A6. `backend/requirements.txt` (новый)
Версии из текущего `backend/venv` (`pip freeze`), **без `pycrypto`** (нигде не импортируется и не собирается на Python 3.10+), плюс `gunicorn`:
```
blinker==1.9.0
click==8.1.8
docxtpl==0.20.2
Flask==3.1.3
Flask-HTTPAuth==4.8.1
Flask-SQLAlchemy==3.1.1
itsdangerous==2.2.0
Jinja2==3.1.6
lxml==6.1.3
MarkupSafe==3.0.3
passlib==1.7.4
pillow==11.3.0
psycopg2-binary==2.9.12
pycountry==24.6.1
PyOTP==2.10.0
python-docx==1.2.0
python-magic==0.4.27
qrcode==8.2
redis==7.0.1
SQLAlchemy==2.0.54
typing_extensions==4.16.0
Werkzeug==3.1.9
xlsxwriter==3.2.9
gunicorn==23.0.0
```

### A7. `deploy/nginx/baweraluminium.conf` (новый)
```nginx
server {
    listen 80;
    server_name baweraluminium.com www.baweraluminium.com;

    root /var/www/bawer/site;
    index index.html;
    client_max_body_size 51m;          # ANY_UPLOAD_MAX_SIZE_MB + 1

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    # Публичный сайт (Vue SPA, history mode)
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Админка (Vue SPA под /admin/)
    location = /admin { return 301 /admin/; }
    location /admin/ {
        root /var/www/bawer;
        try_files $uri $uri/ /admin/index.html;
    }

    # Загруженные файлы
    location /media/ {
        alias /opt/alu-factory/backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # API публичного сайта -> sip
    location /api/ {
        proxy_pass http://127.0.0.1:9999;
        include /etc/nginx/proxy_params;
        # перезаписываем, а не дописываем: util.get_remote_ip берёт первый IP,
        # иначе лимит формы обратной связи можно обойти подделкой заголовка
        proxy_set_header X-Forwarded-For $remote_addr;
    }

    # API админки -> crm (слэш в конце proxy_pass срезает /admin-api)
    location /admin-api/ {
        proxy_pass http://127.0.0.1:8888/;
        include /etc/nginx/proxy_params;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_read_timeout 120s;
    }
}
```

### A8. `deploy/systemd/alu-crm.service` (новый)
```ini
[Unit]
Description=Alu Factory CRM API (admin)
After=network.target postgresql.service redis-server.service

[Service]
User=alu
Group=alu
WorkingDirectory=/opt/alu-factory
ExecStart=/opt/alu-factory/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:8888 --workers 1 --threads 4 \
    --max-requests 1000 --max-requests-jitter 100 --timeout 120 \
    backend.src.crm.web:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### A9. `deploy/systemd/alu-sip.service` (новый)
```ini
[Unit]
Description=Alu Factory public site API
After=network.target postgresql.service redis-server.service

[Service]
User=alu
Group=alu
WorkingDirectory=/opt/alu-factory
ExecStart=/opt/alu-factory/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:9999 --workers 2 \
    --max-requests 1000 --max-requests-jitter 100 --timeout 60 \
    backend.src.sip.web:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
Память: 3 процесса gunicorn × ~60–80 МБ + Postgres + Redis + nginx укладываются в 1 ГБ, swap — страховка.

### A10. `deploy/deploy.sh` (запускается с Mac)
Заливает на сервер исходники `frontend/`, `console/` (без `node_modules` и `dist`), `backend/` и `deploy/`, затем по SSH на сервере: `npm ci && npm run build` для обоих фронтендов, копирует `dist/` в `/var/www/bawer/site` и `/var/www/bawer/admin`, ставит Python-зависимости и перезапускает `alu-crm`/`alu-sip`. Node.js на Mac не нужен.

---

## Часть B. Пошаговый деплой

### Шаг 1. DNS
У регистратора домена `baweraluminium.com` создать:
- A-запись `@` → `<IP сервера>`
- A-запись `www` → `<IP сервера>`

Проверка с Mac (может занять от минут до нескольких часов): `dig +short baweraluminium.com`.

### Шаг 2. Пользователь и SSH-ключ
На сервере под root:
```bash
adduser alu
usermod -aG sudo alu
```
С Mac:
```bash
ssh-copy-id alu@<IP>
ssh alu@<IP>          # дальше всё под alu через sudo
```

### Шаг 3. Обновление системы, swap, firewall
```bash
sudo apt update && sudo apt upgrade -y

# swap 2 ГБ — обязательно при 1 ГБ RAM
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-swap.conf
sudo sysctl --system
free -h               # должна появиться строка Swap: 2.0Gi

sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Шаг 4. Пакеты
```bash
sudo apt install -y nginx postgresql redis-server \
  python3-venv python3-dev build-essential libpq-dev libmagic1 \
  rsync certbot python3-certbot-nginx

# Node.js 22 для сборки frontend/console (Vite 8 требует Node >= 20.19)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v               # v22.x
```

### Шаг 5. Урезать память Redis и PostgreSQL
```bash
sudo sed -i 's/^# *maxmemory <bytes>/maxmemory 64mb/' /etc/redis/redis.conf
echo 'maxmemory-policy allkeys-lru' | sudo tee -a /etc/redis/redis.conf

PGCONF=$(ls /etc/postgresql/*/main/postgresql.conf)
sudo sed -i "s/^#\?shared_buffers.*/shared_buffers = 128MB/" $PGCONF
sudo sed -i "s/^#\?max_connections.*/max_connections = 30/" $PGCONF

sudo systemctl restart redis-server postgresql
```

### Шаг 6. База данных
```bash
sudo -u postgres psql -c "CREATE USER alufactory WITH PASSWORD 'СИЛЬНЫЙ_ПАРОЛЬ';"
sudo -u postgres psql -c "CREATE DATABASE alufactory OWNER alufactory;"
```

### Шаг 7. Каталоги
```bash
sudo mkdir -p /opt/alu-factory/frontend /opt/alu-factory/console /opt/alu-factory/backend/media /opt/alu-factory/backend/logs /var/www/bawer/site /var/www/bawer/admin
sudo chown -R alu:alu /opt/alu-factory /var/www/bawer
sudo chmod o+x /opt /opt/alu-factory /opt/alu-factory/backend     # nginx (www-data) должен дойти до media
chmod -R o+rX /opt/alu-factory/backend/media
```

### Шаг 8. Перенос данных (с Mac, из корня проекта)
```bash
pg_dump -Fc -U alufactory -h localhost alufactory > alufactory.dump
scp alufactory.dump alu@<IP>:~
rsync -az backend/media/ alu@<IP>:/opt/alu-factory/backend/media/
```
На сервере:
```bash
pg_restore --no-owner --role=alufactory -h localhost -U alufactory -d alufactory ~/alufactory.dump
chmod -R o+rX /opt/alu-factory/backend/media
rm ~/alufactory.dump
```

### Шаг 9. Первая выкладка кода (с Mac)
```bash
chmod +x deploy/deploy.sh
SERVER=alu@<IP> ./deploy/deploy.sh
```
Скрипт зальёт исходники, соберёт оба фронтенда на сервере, опубликует статику, создаст venv и поставит зависимости. Рестарт сервисов пропустится — их ещё нет.

### Шаг 10. `config.ini` на сервере
Сгенерировать ключ: `python3 -c "import secrets; print(secrets.token_hex(32))"`
Создать `/opt/alu-factory/backend/config.ini`:
```ini
# Configuration file for ALU_FACTORY (production)
[ALU_FACTORY]
DB_URI = postgresql://alufactory:СИЛЬНЫЙ_ПАРОЛЬ@localhost/alufactory
REDIS_URI = redis://127.0.0.1:6379
SECRET_KEY = <сгенерированный ключ>
REDIS_PREFIX = alufactory
CRM_PORT = 8888
SIP_PORT = 9999
COMPANY_ID = alufactory

MEDIA_UPLOAD_FOLDER = /opt/alu-factory/backend/media/
APP_PATH = /opt/alu-factory/backend/
MEDIA_SERVE_URL = https://baweraluminium.com/media/

IMAGE_UPLOAD_MAX_SIZE_MB = 5
DOCUMENT_UPLOAD_MAX_SIZE_MB = 20
TEMPLATE_UPLOAD_MAX_SIZE_MB = 10
ANY_UPLOAD_MAX_SIZE_MB = 50

DEBUG = false
SESSION_COOKIE_SECURE = true
```
```bash
chmod 600 /opt/alu-factory/backend/config.ini
```
> Новый `SECRET_KEY` разлогинит все старые сессии — это нормально.

### Шаг 11. Запуск бэкенда (systemd)
```bash
sudo cp /opt/alu-factory/deploy/systemd/alu-crm.service /opt/alu-factory/deploy/systemd/alu-sip.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now alu-crm alu-sip
systemctl status alu-crm alu-sip --no-pager
curl -s http://127.0.0.1:9999/api/company | head -c 300; echo
```

### Шаг 12. nginx
```bash
sudo cp /opt/alu-factory/deploy/nginx/baweraluminium.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/baweraluminium.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```
Проверка: `http://baweraluminium.com` открывает сайт.

### Шаг 13. HTTPS (Let's Encrypt)
```bash
sudo certbot --nginx -d baweraluminium.com -d www.baweraluminium.com --redirect -m <ваш email> --agree-tos
sudo systemctl status certbot.timer      # автопродление
```
После этого сайт работает по HTTPS, cookie сессии админки ставится с флагом Secure.

### Шаг 14. Проверка
- `https://baweraluminium.com` — сайт, слайдер, картинки из `/media/`; F5 на внутренней странице не даёт 404; форма обратной связи отправляется.
- `https://baweraluminium.com/admin/` — вход (логин/пароль из вашей локальной БД), список товаров, загрузка картинки, F5 на `/admin/products`.
- `free -h` — есть свободная память и swap.

### Шаг 15. Обновления в дальнейшем
Любые изменения кода — одна команда с Mac:
```bash
SERVER=alu@<IP> ./deploy/deploy.sh
```
Если менялись `deploy/nginx` или `deploy/systemd` — после скрипта повторить копирование из шагов 11/12 и `sudo systemctl daemon-reload` / `sudo systemctl reload nginx`.

### Шаг 16. Бэкап (рекомендуется)
```bash
mkdir -p ~/backups
crontab -e
# добавить строку — ежедневный дамп в 3:00, хранить 14 дней:
0 3 * * * pg_dump -Fc -h localhost -U alufactory alufactory > ~/backups/db-$(date +\%F).dump && find ~/backups -name 'db-*.dump' -mtime +14 -delete
```
Для работы без пароля создать `~/.pgpass`: `localhost:5432:alufactory:alufactory:СИЛЬНЫЙ_ПАРОЛЬ` и `chmod 600 ~/.pgpass`. Папку `media` периодически забирать на Mac: `rsync -az alu@<IP>:/opt/alu-factory/backend/media/ ./media-backup/`.

---

## Диагностика
| Проблема | Где смотреть |
|---|---|
| 502 Bad Gateway | `journalctl -u alu-crm -n 100` / `journalctl -u alu-sip -n 100` |
| Ошибки приложения | `/opt/alu-factory/backend/logs/` |
| nginx | `/var/log/nginx/error.log` |
| Картинки 403/404 | права на `/opt/alu-factory/backend/media` (шаг 7), `MEDIA_UPLOAD_FOLDER` |
| Админка не логинится | зашли по `http://`, а не `https://` (cookie Secure); `DEBUG`/`SESSION_COOKIE_SECURE` в config.ini |
| Не хватает памяти | `free -h`, `sudo systemctl status` — уменьшить `--workers` у sip до 1 |

## Проверка правок кода (локально, до деплоя)
- `npm run dev` в `console/` работает как раньше (логин, загрузка картинки).
- `npm run build` в `frontend/` и `console/` проходит; в `console/dist/index.html` пути к ассетам начинаются с `/admin/`.
- Бэкенд локально стартует с текущим `config.ini` без новых ключей.
