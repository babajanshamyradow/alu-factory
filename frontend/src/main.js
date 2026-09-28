import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import i18n from './i18n'
import directives from './directives'

import 'swiper/css'
import 'swiper/css/effect-fade'
import 'swiper/css/thumbs'
import './styles/base.css'

createApp(App).use(createPinia()).use(router).use(i18n).use(directives).mount('#app')
