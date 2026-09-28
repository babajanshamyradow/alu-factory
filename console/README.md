# Alu-Factory Admin Console

Админ-панель на Vue 3 + Vite + Pinia + Element Plus + vue-i18n. Работает поверх Flask-бэкенда (`backend/`) через сессионную cookie-авторизацию (`/login`, `/logout`, `/auth-check`, `/me`).

## Запуск

```bash
nvm use            # использует версию из .nvmrc (22); см. примечание ниже
npm install
npm run dev         # http://localhost:5173
```

Бэкенд должен быть поднят на `http://localhost:8888` (см. `backend/config.ini`, `CRM_PORT`). Dev-сервер Vite проксирует `/login`, `/logout`, `/auth-check`, `/me`, `/media`, `/api/*` на бэкенд (`vite.config.js`), поэтому cookie-сессия работает без CORS.

**Про Node**: на этой машине `nvm install 22` падает при сборке из исходников (несовместимость системного Clang с новым Node). Рабочий Node 22 установлен через Homebrew (`brew install node@22`, keg-only, лежит в `/opt/homebrew/opt/node@22/bin`). Если `nvm use` не находит 22-ю версию — добавьте `/opt/homebrew/opt/node@22/bin` в PATH вручную для этого проекта, либо используйте Node 20 (тоже работает, но даёт EBADENGINE-предупреждения от `@vueuse/core`/`vue-i18n`, не блокирующие).

## Структура

```
src/
  api/          # http.js (axios instance) + один файл на ресурс (auth, users, categories, products, contactMessages,
                #   slider, banners, company, media)
  stores/       # Pinia-сторы (auth.js)
  i18n/         # vue-i18n + locales/{en,ru,tm,tr,de}.json
  router/       # маршруты, guard requiresAuth/guestOnly
  layouts/      # AdminLayout.vue — sidebar + topbar
  views/        # экраны (по одному на ресурс, в подпапке при списке+форме)
  components/   # переиспользуемые компоненты: MediaUploader, ImageGalleryEditor, LangSwitcher, ...
  utils/        # media.js (типы/лимиты загрузки), schedule.js (UTC-даты, статус показа)
```

## Конвенция: новый backend-эндпоинт → код в консоли

Когда в backend добавляется новый эндпоинт для админки (по конвенции — под `/api/<resource>`), в этой же задаче добавляется:

1. **`src/api/<resource>.js`** — функции `list/get/create/update/remove`, вызывающие эндпоинт через `api/http.js`:
   ```js
   import http from './http'
   export const listX = () => http.get('/api/x')
   export const getX = (id) => http.get(`/api/x/${id}`)
   export const createX = (payload) => http.post('/api/x', payload)
   export const updateX = (id, payload) => http.put(`/api/x/${id}`, payload)
   export const deleteX = (id) => http.delete(`/api/x/${id}`)
   ```
2. **`src/views/<resource>/<Resource>ListView.vue`** (`<el-table>` + поиск/пагинация) и **`<Resource>FormDialog.vue`** (`<el-dialog>` с `<el-form>` и валидацией), если нужно редактирование. Для загрузки файлов — `components/MediaUploader.vue` (одно фото/видео) или `components/ImageGalleryEditor.vue` (несколько фото).
   Примеры: `views/categories/` (простой), `views/products/` (серверная пагинация, фильтры, галерея, optimistic locking), `views/company/` (единственная запись без списка).
3. **Маршрут** в `src/router/index.js`, в `children` под `requiresAuth`-родителем.
4. **Пункт меню** в `src/layouts/AdminLayout.vue` — `<el-menu-item>` с `v-if="authStore.can('<resource>.view')"` и иконкой из `@element-plus/icons-vue`.
5. **Права** — роли из `@roles_required(...)` эндпоинта добавить в `src/permissions.js`; маршрут получает `meta: { permission: '...' }`, пункт меню и кнопки — `v-if="authStore.can('...')"`.
6. **Ключи перевода** — сразу во **все пять** файлов `src/i18n/locales/*.json`, не только `en.json`: `nav.<resource>`, секция ресурса и `errors.<код>` для каждого нового кода ошибки backend.

UX-паттерны, которых стоит придерживаться на новых экранах: `ElMessage` для уведомлений об успехе/ошибке, `ElMessageBox.confirm` перед удалением, `el-empty` для пустых списков, `el-alert` для ошибок загрузки, состояние `loading` на кнопках сабмита.
