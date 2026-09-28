# Архитектура

## Части проекта

```
alu-factory/
  backend/     # Flask + SQLAlchemy + PostgreSQL — API и модели
  console/     # Vue 3 админ-панель (этот документ описывает связь с backend)
  frontend/    # публичный сайт компании — пока не начат
  qrcode/      # отдельный скрипт генерации QR-кодов, не связан с web-приложением
```

## backend/

- Точка входа: `backend/src/crm/web.py` → `backend/src/crm/config.py:app_create()`. Несмотря на название папки `crm`, это и есть основное Flask-приложение сайта (папка не переименована с прошлого шаблона проекта, см. `backend-conventions.md`).
- Конфиг: `backend/config.ini`, секция `[ALU_FACTORY]`. Ключевые значения: `DB_URI` (Postgres), `REDIS_URI`, `CRM_PORT=8888`, `MEDIA_UPLOAD_FOLDER`, `SECRET_KEY`.
- ORM: Flask-SQLAlchemy, единый экземпляр `db` в `backend/src/db.py`.
- Модели: `backend/src/model/__init__.py` (все таблицы + enum'ы из `backend/src/model/enums.py`).
- Слой доступа к данным: `backend/src/model/<resource>_access.py` (`user_access`, `category_access`, `product_access`, `slider_access`, `banner_access`, `company_access`, `company_image_access`, `contact_access`, `media_access`) — запросы, изменения, запись аудит-лога.
- Роуты: `backend/src/crm/view/` — блюпринт `root` (`root.py`: `/login`, `/logout`, `/auth-check`, `/me`, `/media/...`) без префикса; ресурсы админки — отдельные блюпринты с префиксом `/api` (`user`, `category`, `product`, `slider`, `banner`, `company`, `media`, `contact`), все регистрируются в `config.py`. Общие валидаторы — `view/validation.py`. Общий JSON-конверт ответа — `backend/src/crm/view/__init__.py:api_response`.
- Авторизация: сессионная cookie (Flask session), не JWT. Подробности — `backend-conventions.md`.
- Медиа-файлы: загружаются через `POST /api/media`, хранятся на диске в `MEDIA_UPLOAD_FOLDER/<год>/<месяц>/`, отдаются через `GET /media/<path:filename>`. Лимиты — `IMAGE_UPLOAD_MAX_SIZE_MB` / `ANY_UPLOAD_MAX_SIZE_MB` из `config.ini` (Flask `MAX_CONTENT_LENGTH` = второй лимит + 1 МБ).

## console/

Vue 3 + Vite + Pinia + Element Plus + vue-i18n. Работает через ту же cookie-сессию backend'а (в dev — через прокси Vite на порт backend'а, без CORS). Подробности — `admin-panel.md`.

## frontend/

Публичный сайт компании (слайдер, баннеры, товары, "О нас", форма обратной связи). Пока не реализован. Данные для него уже редактируются в админке. Из публичных (без авторизации) эндпоинтов есть только отправка формы обратной связи — `POST /api/contact-messages`; эндпоинтов для чтения контента сайтом ещё нет — остальные `/api/...` закрыты `@roles_required`. Публичному сайту нужно будет показывать только `is_active` записи и учитывать расписание `starts_at`/`ends_at` (хранится в UTC).

## qrcode/

Самостоятельный Python-скрипт (`generate_qr.py`) для генерации QR-кодов, не интегрирован с web-приложением.

## Порты (dev)

| Сервис | Порт |
|---|---|
| Flask backend | 8888 |
| Vite dev-сервер (console) | 5173 |
| PostgreSQL | 5432 (роль/БД `alufactory`) |
| Redis | стандартный, из `REDIS_URI` |
