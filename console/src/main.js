import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import './style.css'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { useAuthStore, installAuthUnauthorizedHandler } from './stores/auth'
// Side-effect import: applies the saved light/dark theme before first paint.
import './composables/useTheme'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(ElementPlus)

const authStore = useAuthStore()
installAuthUnauthorizedHandler(router)

// Confirm the session cookie (if any) before the first render, so neither the
// login page nor protected content flashes. The router guard awaits the same
// request (see stores/auth.js), so the initial navigation also waits for it.
authStore.restoreSession().finally(() => {
  app.mount('#app')
})
