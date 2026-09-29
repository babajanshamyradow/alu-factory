# Схема БД

Все модели определены в одном файле — `backend/src/model/__init__.py` (общий `db = SQLAlchemy()` из `backend/src/db.py`). Enum'ы — в `backend/src/model/enums.py`.

## Легаси-таблицы (из старого шаблона проекта, не относятся к alu-factory напрямую)

Эти три таблицы достались от предыдущего шаблона (CRM/Alumni Management System), но по факту это единственная таблица пользователей проекта — админ-панель авторизуется через неё.

### `tbl_user` (класс `User`)
Админы/сотрудники, логинящиеся в админ-панель.

| Поле | Тип | Описание |
|---|---|---|
| `username` | String(64), **PK** | Логин |
| `fullname` | String(64) | Полное имя |
| `password` | String(256) | Хэш пароля (`passlib.sha256_crypt`) |
| `locked` | Boolean | Заблокирован ли аккаунт |
| `role` | Enum `UserRole` (`superuser`/`admin`/`operator`) | Роль |
| `lang` | Enum `SystemLang` (`en`/`ru`/`tr`/`de`) | Язык интерфейса (используется как язык по умолчанию в админ-панели) |
| `email` | String(256), nullable | Email |
| `access_token` / `refresh_token` / `access_token_expiration` | — | API-токены (для мобильных/внешних клиентов; веб-админка использует cookie-сессию, не эти поля) |
| `firebase_token` | Text, nullable | Push-токен (не используется в alu-factory) |
| `version` | Integer | Счётчик версий для optimistic locking |

По умолчанию (`fill_default()`) заведены `SYSTEM` (роль `superuser`) и `admin`/`12345` (роль `admin`).

### `tbl_user_login_log` (класс `UserLoginLog`)
Легаси-лог попыток входа, привязан к `tbl_user.username`. **Не используется** новым auth-флоу (`root.py`) — вместо него пишется `tbl_audit_log` (см. ниже). Оставлен как есть, не трогаем.

### `tbl_user_log` (класс `UserLog`)
Легаси generic action-лог, тоже привязан к `tbl_user.username`. **Не используется** новым кодом — см. `tbl_audit_log`.

---

## Таблицы сайта alu-factory

### `tbl_media` (класс `Media`)
Общая таблица файлов (изображения/видео) — на неё ссылаются товары, слайдер, баннеры, галерея компании.

| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK | |
| `file_path` | String(500), not null | Путь относительно `MEDIA_UPLOAD_FOLDER` |
| `media_type` | Enum `MediaType` (`image`/`video`) | |
| `alt_text`, `original_filename`, `mime_type` | String, nullable | |
| `file_size_bytes`, `width`, `height` | Integer, nullable | |
| `uploaded_by` | String(64), FK → `tbl_user.username`, nullable | |
| `created_at` | DateTime | |

Жизненный цикл: строка создаётся при загрузке (`POST /api/media`), `file_path` = `<год>/<месяц>/<uuid>.<ext>`. Когда ссылающуюся строку удаляют или меняют ей медиа, `media_access.delete_if_unused` удаляет строку и файл, если на медиа больше никто не ссылается (проверяются `tbl_product_image`, `tbl_slider_item`, `tbl_banner`, `tbl_company_image`, `logo/cover` в `tbl_company_info`). Файл, загруженный в форму, которую потом закрыли без сохранения, остаётся «сиротой» — автоматической чистки таких нет.

Даты `starts_at`/`ends_at` (слайдер, баннеры) и все `created_at`/`updated_at` хранятся как naive UTC.

### `tbl_category` (класс `Category`)
| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK | |
| `name` | String(128), unique | |
| `slug` | String(160), unique | |
| `description` | Text, nullable | |
| `is_active` | Boolean | |
| `sort_order` | Integer | |
| `created_at` / `updated_at` | DateTime | |

### `tbl_product` (класс `Product`)
| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK | |
| `category_id` | Integer, FK → `tbl_category.id`, not null | |
| `name` | String(200) | |
| `slug` | String(220), unique | |
| `short_description` | String(500), nullable | |
| `description` | Text, nullable | |
| `is_active` / `is_featured` | Boolean | `is_featured` — кандидат для показа в баннере |
| `sort_order` | Integer | |
| `created_at` / `updated_at` | DateTime | |
| `version` | Integer | optimistic locking |

Связь: `Product.images` (через `ProductImage`, `lazy='dynamic'`, сортировка по `sort_order`).

### `tbl_product_image` (класс `ProductImage`)
Join-таблица товар↔медиа (товар может иметь несколько изображений, одно — основное).

| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK | |
| `product_id` | Integer, FK → `tbl_product.id` | |
| `media_id` | Integer, FK → `tbl_media.id` | |
| `is_primary` | Boolean | |
| `sort_order` | Integer | |
| `created_at` | DateTime | |

`UniqueConstraint(product_id, media_id)`. «Ровно одно `is_primary` на товар» гарантирует API (`view/product.py`), а не БД; при сохранении товара набор строк пересоздаётся целиком, `sort_order` = позиция в присланном списке.

### `tbl_slider_item` (класс `SliderItem`)
Слайдер на главной странице.

| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK | |
| `media_id` | Integer, FK → `tbl_media.id` | |
| `title`, `subtitle`, `link_url` | String, nullable | |
| `sort_order` | Integer | |
| `is_active` | Boolean | |
| `starts_at` / `ends_at` | DateTime, nullable | плановая публикация |
| `created_at` / `updated_at` | DateTime | |

### `tbl_banner` (класс `Banner`)
Динамические баннеры на главной, опционально привязаны к товару.

| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK | |
| `media_id` | Integer, FK → `tbl_media.id` | |
| `product_id` | Integer, FK → `tbl_product.id`, nullable | "использовать товар в баннере" |
| `title`, `subtitle`, `link_url` | String, nullable | |
| `sort_order` | Integer | |
| `is_active` | Boolean | |
| `starts_at` / `ends_at` | DateTime, nullable | |
| `created_at` / `updated_at` | DateTime | |

### `tbl_contact_message` (класс `ContactMessage`)
Заявки с формы обратной связи.

| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK | |
| `name` | String(150), not null | |
| `email` | String(255), nullable | |
| `phone` | String(50), nullable | |
| `message` | Text, not null | |
| `status` | Enum `ContactStatus` (`new`/`read`/`archived`) | |
| `ip_address`, `user_agent` | String, nullable | |
| `created_at` | DateTime, indexed | |

`CheckConstraint("email IS NOT NULL OR phone IS NOT NULL")`. Каждая заявка также пишет запись в `tbl_audit_log` (`action='contact_submitted'`). Жизненный цикл статуса: заявка приходит как `new`; открытие в консоли автоматически ставит `read`; дальше вручную `archived` (или обратно). Текст заявки после создания не меняется.

### `tbl_company_info` (класс `CompanyInfo`, singleton — одна строка с `id=1`)
Данные страницы "О нас".

| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK, default 1 | |
| `company_name` | String(200), not null | |
| `email`, `phone` | String, nullable | |
| `address` | Text, nullable | |
| `latitude` / `longitude` | Numeric(9,6), nullable | координаты для Google Maps |
| `description` | Text, nullable | |
| `logo_media_id` / `cover_media_id` | Integer, FK → `tbl_media.id`, nullable | |
| `updated_at` | DateTime | |

`CheckConstraint("id = 1")`.

### `tbl_company_image` (класс `CompanyImage`)
Галерея фото на странице "О нас".

| Поле | Тип | Описание |
|---|---|---|
| `id` | Integer, PK | |
| `media_id` | Integer, FK → `tbl_media.id` | |
| `caption` | String(255), nullable | |
| `sort_order` | Integer | |
| `is_active` | Boolean | |
| `created_at` | DateTime | |

### `tbl_audit_log` (класс `AuditLog`)
Единый лог: CRUD-действия админов, вход/выход/неудачные попытки входа, факт заявки с формы. Используется новым auth-флоу (`root.py`/`user_access.py`) — актуальная замена легаси `tbl_user_log`/`tbl_user_login_log`.

| Поле | Тип | Описание |
|---|---|---|
| `id` | BigInteger, PK | |
| `username` | String(64), FK → `tbl_user.username`, nullable | null — для анонимных событий (неизвестный логин при входе, заявка с формы) |
| `action` | Enum `AuditAction` (`create`/`update`/`delete`/`login`/`login_failed`/`logout`/`contact_submitted`) | |
| `table_name` | String(64), nullable | |
| `record_id` | String(64), nullable | строкой — универсально для любого PK |
| `old_data` / `new_data` | JSONB, nullable | |
| `description` | String(500), nullable | |
| `ip_address`, `user_agent` | String, nullable | |
| `created_at` | DateTime, indexed | |

Индекс также на `(table_name, record_id)`.

---

## Enum'ы (`backend/src/model/enums.py`)

- `UserRole`: `superuser`, `admin`, `operator`
- `SystemLang`: `en`, `ru`, `tr`, `de`
- `MediaType`: `image`, `video`
- `ContactStatus`: `new`, `read`, `archived`
- `AuditAction`: `create`, `update`, `delete`, `login`, `login_failed`, `logout`, `contact_submitted`
