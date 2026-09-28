# Локальный запуск

## Требования

- Python 3.9 (venv уже есть в `backend/venv`).
- PostgreSQL — роль и БД `alufactory` / `alufactory` (`backend/config.ini`, `DB_URI`).
- Redis — `backend/config.ini`, `REDIS_URI` (используется для `redis`-объекта в `config.py`, не для сессий — см. ниже).
- Node.js 22 для `console/` — см. примечание про nvm ниже.

## Backend

```bash
cd backend
source venv/bin/activate
python -m backend.src.crm.web   # либо любой способ поднять Flask app из backend/src/crm/web.py
```

По умолчанию слушает `0.0.0.0:8888` (`CRM_PORT` в `config.ini`).

Первичное наполнение БД (создание таблиц + `SYSTEM`/`admin` пользователей): функции `model.init_db()` / `model.fill_default()` в `backend/src/model/__init__.py`, вызываются из `backend/src/init_db.py`. Дефолтный админ после `fill_default()`: `admin` / `12345`.

## Console (админ-панель)

```bash
cd console
nvm use            # см. примечание про Node ниже
npm install
npm run dev         # http://localhost:5173
```

Backend должен быть поднят на 8888 — dev-сервер Vite проксирует API-запросы на него (см. `admin-panel.md`).

## Известные нестыковки конфига (зафиксировано, не исправлено)

- **`Session` не инициализирован**: `config.py` выставляет `SESSION_TYPE='redis'` и т.д., но `flask_session.Session(app)` нигде не вызывается — по факту используется дефолтная подписанная cookie-сессия Flask, а не Redis-сессии. На текущий функционал (cookie-based auth в консоли) это не влияет.
- **`MEDIA_UPLOAD_FOLDER`** в `backend/config.ini` исправлен на `/Users/babajan/alu-factory/backend/media/` (раньше указывал на несуществующий `/Users/babajan/Projects/alu-factory/...`). В `example_config.ini` остался старый путь — при новой установке поправьте на свой. Папка и подпапки `<год>/<месяц>/` создаются автоматически при первой загрузке.
- **`CONTACT_RATE_LIMIT_PER_HOUR`** (необязательный ключ `config.ini`, по умолчанию 5) — лимит заявок с формы обратной связи в час с одного IP. Работает через Redis, поэтому Redis нужен запущенным (при его недоступности лимит просто не применяется).
- **Пароль `admin` в локальной dev-БД уже не `12345`** (менялся вручную) — для входа в консоль используйте актуальный.
- **`MEDIA_SERVE_URL` в `config.ini` указывает на порт 8000**, но реальный роут `/media/<file>` живёт на `CRM_PORT=8888`. При проксировании в dev используется реальный порт (8888).
- **`nvm install 22` падает при компиляции из исходников** на этой машине (несовместимость системного Clang/Xcode Command Line Tools с C++-фичами, которые использует Node 22). Рабочий Node 22 установлен через Homebrew: `brew install node@22` (keg-only, бинарник в `/opt/homebrew/opt/node@22/bin`). Если `nvm use` в `console/` не находит 22-ю версию — добавьте `/opt/homebrew/opt/node@22/bin` в `PATH` для этого проекта, либо используйте Node 20 (тоже рабочий вариант, но даёт EBADENGINE warning от `@vueuse/core`/`vue-i18n`, не блокирующий).

## Порты

| Сервис | Порт |
|---|---|
| Flask backend | 8888 |
| Vite dev-сервер (console) | 5173 |
