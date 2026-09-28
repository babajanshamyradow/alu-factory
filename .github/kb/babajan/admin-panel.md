# Админ-панель (`console/`)

Vue 3 + Vite + Pinia + Element Plus + vue-i18n. Подробная инструкция по запуску и структуре — в `console/README.md`, здесь — конспект для базы знаний.

## Стек

- **Vue 3** (Composition API, `<script setup>`) + **Vite** — сборка/dev-сервер.
- **Pinia** — стор `auth` (`console/src/stores/auth.js`).
- **Element Plus** — UI-компоненты (таблицы, формы, модалки, уведомления).
- **vue-i18n** — переводы, 5 языков (см. ниже).
- **axios** — HTTP-клиент, `withCredentials: true`, единый интерсептор 401 → редирект на `/login` (`console/src/api/http.js`).

## Авторизация

Cookie-сессия backend'а, без токенов на клиенте. При старте приложения (`main.js`) вызывается `GET /me` для восстановления состояния после перезагрузки страницы (сама cookie не читается из JS — она `HttpOnly`). Роутер (`console/src/router/index.js`) редиректит на `/login`, если `requiresAuth`-роут открыт без сессии.

## Dev-прокси (без CORS)

`console/vite.config.js` проксирует `/login`, `/logout`, `/auth-check`, `/me`, `/media`, `/api/*` на backend (`http://localhost:8888`) — браузер видит всё как один origin, cookie-сессия работает без `flask-cors`.

**Конвенция:** все новые backend-эндпоинты для админки размещаются под префиксом `/api/...`.

## i18n — SystemLang

Языки: `en`, `ru`, `tm`, `tr`, `de` (совпадают с backend enum `SystemLang`). Файлы переводов — `console/src/i18n/locales/*.json`. Дефолтный язык — из `User.lang`, приходящего в ответе `/login` и `/me`. Переключатель языка (`console/src/components/LangSwitcher.vue`) хранит выбор в `localStorage`, backend не трогает (нет эндпоинта для сохранения языка на сервере — можно добавить позже по той же конвенции "эндпоинт → код в консоли").

Element Plus не имеет туркменской (`tm`) локали для собственных строк (даты, пагинация) — для `tm` подставляется английская локаль Element Plus, при этом тексты самого приложения остаются туркменскими (`console/src/i18n/index.js`).

## Конвенция: новый backend-эндпоинт → код в консоли

**Стандартное правило проекта**: когда в backend добавляется эндпоинт, нужный админке, в той же задаче добавляется:

1. `console/src/api/<resource>.js` — функции `list/get/create/update/remove` через `api/http.js`.
2. `console/src/views/<resource>/<Resource>ListView.vue` + `<Resource>FormDialog.vue` (при необходимости; для единственной записи вроде «О компании» — одна страница-форма).
3. Маршрут в `console/src/router/index.js`.
4. Пункт меню в `console/src/layouts/AdminLayout.vue`.
5. Права — в `console/src/permissions.js` (зеркало `@roles_required`), `meta.permission` у маршрута, `authStore.can(...)` на меню и кнопках.
6. Ключи перевода — во все 5 файлов локалей (включая `errors.<код>` для новых кодов ошибок).

Полный шаблон с примером кода — в `console/README.md`.

## Разделы

| Маршрут | View | Что внутри |
|---|---|---|
| `/dashboard` | `views/DashboardView.vue` | Приветствие, профиль |
| `/users` | `views/users/UserListView.vue` + `UserFormDialog.vue` | Пользователи, блокировка, сброс пароля |
| `/categories` | `views/categories/CategoryListView.vue` + `CategoryFormDialog.vue` | Категории, число товаров |
| `/products` | `views/products/ProductListView.vue` + `ProductFormDialog.vue` | Товары: серверная пагинация, фильтры (поиск, категория, статус), галерея фото |
| `/slider` | `views/slider/SliderListView.vue` + `SliderFormDialog.vue` | Слайды главной, фото/видео, расписание |
| `/banners` | `views/banners/BannerListView.vue` + `BannerFormDialog.vue` | Баннеры, привязка к товару |
| `/company` | `views/company/CompanyView.vue` + `CompanyGallery.vue` | «О компании» (одна запись: создать один раз, дальше только редактировать) + фотогалерея |
| `/contact-messages` | `views/contact/ContactMessageListView.vue` + `ContactMessageDrawer.vue` | Заявки с сайта: вкладки по статусам со счётчиками, поиск, карточка в боковой панели; открытие новой заявки помечает её прочитанной. Создавать заявки из консоли нельзя — их присылает форма сайта |

Все разделы, кроме пользователей, видны всем ролям; изменения — superuser/admin (operator видит данные только для чтения). Исключение — заявки: статус может менять и operator, удалять — только superuser/admin. Права — `console/src/permissions.js`.

## Общие компоненты и утилиты

- `components/MediaUploader.vue` — одно фото/видео, `v-model` = объект медиа (`{ id, url, 'media-type', ... }`); файл загружается в `POST /api/media` сразу при выборе, форма отправляет только `id`. Проп `allow-video`.
- `components/ImageGalleryEditor.vue` — список фото в форме (`v-model` = `[{ media, isPrimary }]`): мульти-загрузка, главное фото, порядок стрелками. Изменения буферизуются до сохранения формы (используется в товаре).
- `views/company/CompanyGallery.vue` — наоборот, сохраняет каждое действие сразу (свои эндпоинты у галереи компании).
- `utils/media.js` — допустимые расширения и лимиты размера (синхронно с backend), `checkUploadFile`, `uploadErrorKey` (413 → «файл слишком большой»).
- `composables/useNewContactCount.js` — общий счётчик новых заявок: `AdminLayout.vue` опрашивает `GET /api/contact-messages/counts` раз в минуту и показывает бейдж у пункта меню (точка на иконке при свёрнутом меню); экран заявок обновляет счётчик сразу после своих изменений.
- `utils/schedule.js` — `formatDateTime(value, locale)` (локализованная дата-время), `parseUtc` (даты backend приходят как naive UTC без смещения) и `displayStatus` (`live`/`scheduled`/`expired`/`hidden` для слайдов и баннеров). В backend даты отправляются через `Date.toISOString()` (UTC).

## Паттерны экранов

- **Список + диалог формы**: `<Resource>ListView.vue` с `el-table` и `<Resource>FormDialog.vue` (`v-model` открытия + объект/ id редактируемой записи, событие `saved` → перезагрузка списка).
- **Переключатели в строке** (видимость, «рекомендуемый»): `PUT` той же записи со всеми полями строки и изменённым флагом; у товара — без ключа `images` (backend их не трогает) и с `version`.
- **Optimistic locking** (товары): при `product-modified` показать ошибку и перезагрузить список.
- **Ошибки API**: `data['error-msg']` → `t('errors.<код>')`; 401/403 уже обработаны интерсептором `http.js`, их не дублировать.

## UX-конвенции

- `ElMessage` — уведомления об успехе/ошибке действий.
- `ElMessageBox.confirm` — подтверждение перед удалением.
- `el-empty` — пустые списки; `el-alert` — ошибки загрузки (не белый экран).
- Кнопки сабмита — состояние `loading` во время запроса.
- Sidebar сворачивается на узких экранах (`AdminLayout.vue`).

## Известное ограничение

`GET /auth-check` не возвращает данные пользователя (только 200/401 + заголовок `X-User-Id`) — поэтому для восстановления профиля после F5 добавлен отдельный `GET /me` (см. `backend-conventions.md`), а не переиспользован `auth-check`.
