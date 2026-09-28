# Соглашения backend-кода

## Именование и структура моделей

- Все таблицы называются `tbl_<name>`.
- Все модели живут в одном файле `backend/src/model/__init__.py` (по явной просьбе пользователя — не разносить по отдельным файлам).
- У каждой модели есть метод `to_json()`, возвращающий dict для API (ключи через дефис: `'short-description'`, а не `short_description`).
- PK новых таблиц — `Integer` autoincrement, кроме `tbl_audit_log` (`BigInteger`, ожидается большой объём строк). Легаси `tbl_user_log`/`tbl_user_login_log` используют `UUID` — это старый стиль, для новых таблиц не копируется.
- Поле `version` (Integer, optimistic locking) по факту есть только у `User` и `Product` — эндпоинты этих таблиц его проверяют (`user-modified` / `product-modified`). У `Category`, `SliderItem`, `Banner`, `CompanyInfo`, `CompanyImage` его нет: при одновременном редактировании побеждает последнее сохранение. Добавить `version` туда — изменение схемы, отдельная задача. На append-only таблицах (`ContactMessage`, `AuditLog`) оно не нужно.

## Структура ресурса (шаблон для новых эндпоинтов)

Каждый ресурс админки разложен одинаково:

- `backend/src/crm/view/<resource>.py` — блюпринт с `url_prefix='/api'`, регистрируется в `backend/src/crm/config.py`. Здесь: валидация тела запроса (`_validate(...)` копит коды ошибок в `error_msg`), права (`@roles_required`), сборка JSON (`_to_json(...)` — `model.to_json()` плюс вложенные `media`/`product`/`category`).
- `backend/src/model/<resource>_access.py` — работа с БД: `get`/`list_all`/`add`/`edit`/`delete`. Каждое изменение в той же транзакции пишет `tbl_audit_log` через `user_access._write_audit_log(...)` со снимками `old_data`/`new_data`.
- Общие валидаторы — `backend/src/crm/view/validation.py`: `is_int` (отсекает `bool`), `optional_str`, `parse_datetime` (ISO-8601 → naive UTC), `slugify`/`SLUG_RE`, `LINK_URL_RE`, `validate_display_fields` (слайды/баннеры).
- Коды ошибок — kebab-case с префиксом ресурса (`category-name-exists`, `product-modified`, ...); консоль переводит их через ключи `errors.<код>`.
- Если сущность ссылается на медиа и ссылку меняют/удаляют — после коммита вызывается `media_access.delete_if_unused(...)` (см. «Медиа»).
- Удаление, которое оставило бы «висячие» ссылки, не каскадится молча, а блокируется понятной ошибкой (`category-has-products`, `product-used-in-banners`).

## Сводка эндпоинтов админки

| Ресурс | Эндпоинты | Чтение | Изменение |
|---|---|---|---|
| Пользователи | `/api/users[/<username>]`, `/lock`, `/password`; `/api/profile/password` | superuser, admin | superuser, admin (lock/reset/delete — только superuser) |
| Медиа | `POST /api/media` | — | superuser, admin |
| Категории | `/api/categories[/<id>]` | все роли | superuser, admin |
| Товары | `/api/products[/<id>]`, `/api/products/lookup` | все роли | superuser, admin |
| Слайдер | `/api/slider-items[/<id>]` | все роли | superuser, admin |
| Баннеры | `/api/banners[/<id>]` | все роли | superuser, admin |
| О компании | `/api/company` (GET/POST/PUT, без DELETE) | все роли | superuser, admin |
| Галерея компании | `/api/company/images[/<id>]`, `/api/company/images/order` | все роли | superuser, admin |
| Заявки | `/api/contact-messages[/<id>]`, `/counts`, `/<id>/status` | все роли | статус — все роли; удаление — superuser, admin; **создание — публично, без входа** |

Эти эндпоинты проверены вручную через Flask test client на dev-БД; автотестов в проекте пока нет.

## Пользователи админ-панели

Отдельной таблицы для пользователей сайта нет — используется существующая `tbl_user` (класс `User`, PK — `username`). Решение принято явно: не плодить вторую таблицу пользователей ради поля `id`.

## Авторизация — сессионная cookie, не JWT

- `POST /login` — тело `{"username", "password"}`, при успехе ставит Flask session cookie (`session['u']`, `session['r']`, `session['l']`).
- `GET /logout` — очищает сессию.
- `GET /auth-check` — 401, если не залогинен/заблокирован; иначе 200 + заголовок `X-User-Id`. Без JSON-тела.
- `GET /me` — возвращает полный профиль (`username`/`fullname`/`role`/`email`/`lang`) для текущей сессии; нужен, потому что `/auth-check` не даёт данных для восстановления UI после перезагрузки страницы.
- Вся логика — в `backend/src/model/user_access.py`, роуты — в `backend/src/crm/view/root.py`.

## Права доступа — `@roles_required`

Роли статичные (`UserRole`: `superuser`, `admin`, `operator`), без таблицы прав. Каждый `/api/...`-эндпоинт закрывается декоратором `roles_required(*roles)` из `backend/src/crm/view/__init__.py`, **над** `@api_response`:

```python
@bp.route('/users', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def user_list(): ...
```

- Нет сессии / пользователь заблокирован / удалён → `401`; роль не в списке → `403`. `roles_required()` без аргументов — любой залогиненный.
- Пользователь перечитывается из БД на каждом запросе (блокировка и смена роли действуют сразу), доступен как `g.user`.
- Та же карта ролей продублирована в консоли — `console/src/permissions.js`; при новом эндпоинте обновлять оба места.

Пользователи (`backend/src/crm/view/user.py`): список/просмотр, создание, редактирование — superuser+admin (admin не трогает superuser-аккаунты и не выдаёт/не создаёт роль superuser); блокировка, сброс пароля, удаление — только superuser. Свой пароль (`PUT /api/profile/password`) меняет любой залогиненный.

Категории (`backend/src/crm/view/category.py`, логика — `backend/src/model/category_access.py`): список/просмотр — все роли; создание, редактирование, удаление — superuser+admin. Slug необязателен — генерируется из названия (с транслитерацией кириллицы). Категорию с товарами удалить нельзя (`category-has-products`). Все изменения пишутся в `tbl_audit_log` с `old_data`/`new_data`.

Слайдер (`backend/src/crm/view/slider.py`, логика — `backend/src/model/slider_access.py`, `/api/slider-items`): список/просмотр — все роли; создание, редактирование, удаление — superuser+admin. Даты `starts-at`/`ends-at` принимаются в ISO-8601 (со смещением или без — тогда считаются UTC) и хранятся как naive UTC. `link-url` — только `http(s)://...` или путь сайта `/...`. В ответе вложен объект `media` с полем `url`.

Баннеры (`backend/src/crm/view/banner.py`, логика — `backend/src/model/banner_access.py`, `/api/banners`): те же права и поля, что у слайдера, плюс необязательный `product-id`; в ответе вложен `product` (краткий: `id`/`name`/`slug`/`short-description`/`is-active`) или `null`. Общая проверка полей слайдов и баннеров (медиа, заголовки, ссылка, порядок, видимость, даты) — `validate_display_fields(data, error_msg, prefix)` в `backend/src/crm/view/validation.py`; коды ошибок — `<prefix>-<поле>-invalid`.

Товары (`backend/src/crm/view/product.py`, логика — `backend/src/model/product_access.py`, `/api/products`): список/просмотр — все роли; создание, редактирование, удаление — superuser+admin.
- `GET /api/products` — постранично: параметры `search`, `category-id`, `status` (`active`/`hidden`/`featured`), `page`, `per-page` (до 100); ответ `{items, total, page, per-page}`. В строках списка — только обложка (`cover`) и `images-count`, без полного списка фото.
- `GET /api/products/<id>` — полный товар с `images` (главное фото первым).
- `POST`/`PUT` принимают `images: [{media-id, is-primary}]` в порядке показа (до 20, только изображения, без повторов); ровно одно фото становится главным — отмеченное или первое. `PUT` требует `version` (optimistic locking, ошибка `product-modified`); без ключа `images` фото не меняются — так работают переключатели в таблице.
- Удаление запрещено, пока товар привязан к баннерам (`product-used-in-banners`); вместе с товаром удаляются его `tbl_product_image` и неиспользуемые файлы.
- `GET /api/products/lookup?search=` — краткий список (до 20) для выбора товара в форме баннера.

О компании (`backend/src/crm/view/company.py`, логика — `backend/src/model/company_access.py`, `/api/company`) — одна запись (`id = 1`, CHECK в БД): `GET` — все роли, возвращает запись или ответ без `result`, если её ещё нет; `POST` — создать, только если записи нет (иначе `company-exists`); `PUT` — полное редактирование существующей (иначе `company-not-found`); удаления нет. Superuser+admin на `POST`/`PUT`. Координаты — обе или ни одной (`company-coordinates-invalid`); логотип/обложка — `logo-media-id`/`cover-media-id` (только изображения), старые неиспользуемые файлы удаляются при замене. В консоли — одна страница `/company` (`console/src/views/company/CompanyView.vue`) без списка.

Галерея компании (`tbl_company_image`, логика — `backend/src/model/company_image_access.py`, роуты — в том же `company.py`): `GET/POST /api/company/images`, `PUT/DELETE /api/company/images/<id>`, `PUT /api/company/images/order` с `{"ids": [...]}` — все id галереи в новом порядке (если набор не совпадает с текущим — `company-images-modified`). `POST` без `sort-order` добавляет фото в конец. Права — как у компании. В консоли — блок `CompanyGallery.vue` на странице `/company` (виден, когда компания создана); каждое действие сохраняется сразу, без кнопки «Сохранить».

Заявки с формы обратной связи (`backend/src/crm/view/contact.py`, логика — `backend/src/model/contact_access.py`, `/api/contact-messages`):
- `POST` — **единственный публичный эндпоинт** (без `@roles_required`), для формы на сайте. Поля `name`, `email`/`phone` (хотя бы одно — как CHECK в БД), `message` (до 5000). Защита от спама: скрытое поле-ловушка `website` (если заполнено — ответ `SUCCESS`, но ничего не сохраняется) и лимит `CONTACT_RATE_LIMIT_PER_HOUR` (по умолчанию 5) заявок в час с одного IP через Redis (`<REDIS_PREFIX>:contact-rate:<ip>`; при недоступном Redis лимит пропускается, а не блокирует клиентов). Невалидные запросы в лимит не считаются. IP берётся из `get_remote_ip()`, который доверяет `X-Forwarded-For` — в проде за реверс-прокси он должен перезаписывать этот заголовок, иначе лимит обходится подменой. Каждая заявка пишет `tbl_audit_log` с `action='contact_submitted'`.
- `GET` — постранично, новые сверху: `search` (имя/email/телефон/текст), `status`, `page`, `per-page`; в ответе также `counts` по статусам. `GET /counts` — только счётчики (для бейджа в меню). `GET /<id>` — полная заявка с `ip-address`/`user-agent`.
- `PUT /<id>/status` `{"status": "new|read|archived"}` — единственное изменение: текст клиента не редактируется. `DELETE /<id>` — superuser+admin.

`slugify(value, max_len)` и `SLUG_RE` — в `backend/src/crm/view/validation.py`, общие для категорий и товаров.

## Конверт ответа API

`backend/src/crm/view/__init__.py:api_response` — декоратор, оборачивающий `(status, error_msg, result)` в JSON:

```json
{"status": "SUCCESS", "result": {...}}
{"status": "ERROR", "error-msg": ["some-error-code"]}
```

`status == 'NOT_ALLOWED'` или `'permission-denied'` в `error-msg` → голый `Response(status=403)`.

## Аудит-лог

`tbl_audit_log` (класс `AuditLog`) — единая таблица для:
- CRUD-действий админа (`action='create'/'update'/'delete'`, `table_name`, `record_id`),
- входа/выхода/неудачных попыток входа (`action='login'/'login_failed'/'logout'`),
- факта заявки с формы обратной связи (`action='contact_submitted'`).

Пишется через приватную функцию `user_access._write_audit_log(...)`. Легаси `tbl_user_log`/`tbl_user_login_log` для этого не используются — они остались от старого шаблона и не подключены к новому коду.

## Медиа

Файлы хранятся на диске (`MEDIA_UPLOAD_FOLDER` из `config.ini`), в БД — только путь (`tbl_media.file_path`) и метаданные. Раздаются через `GET /media/<path:filename>`.

Загрузка — общий эндпоинт `POST /api/media` (multipart, поле `file`, опционально `alt-text`; superuser+admin): `backend/src/crm/view/media.py` + `backend/src/model/media_access.py`. Разрешены jpg/jpeg/png/webp/gif (до `IMAGE_UPLOAD_MAX_SIZE_MB`) и mp4/webm (до `ANY_UPLOAD_MAX_SIZE_MB`); SVG запрещён намеренно (XSS). Картинки проверяются Pillow, ширина/высота сохраняются. Путь файла — `MEDIA_UPLOAD_FOLDER/<год>/<месяц>/<uuid>.<ext>`.

Сущности, ссылающиеся на медиа, принимают только `media-id`. После удаления сущности или смены её медиа вызывается `media_access.delete_if_unused(...)` — удаляет строку и файл, если на медиа больше никто не ссылается. В консоли загрузка — через переиспользуемый компонент `console/src/components/MediaUploader.vue`.
