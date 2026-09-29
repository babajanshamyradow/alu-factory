import { createI18n } from 'vue-i18n'

import en from './locales/en.json'
import ru from './locales/ru.json'
import tr from './locales/tr.json'
import de from './locales/de.json'

// Element Plus ships its own locale files for en/ru/tr/de, used for its
// internal component strings (date-picker labels, pagination text, etc.).
import elEn from 'element-plus/dist/locale/en.mjs'
import elRu from 'element-plus/dist/locale/ru.mjs'
import elTr from 'element-plus/dist/locale/tr.mjs'
import elDe from 'element-plus/dist/locale/de.mjs'

export const SUPPORTED_LOCALES = ['en', 'ru', 'tr', 'de']

export const elementPlusLocales = {
  en: elEn,
  ru: elRu,
  tr: elTr,
  de: elDe,
}

const STORAGE_KEY = 'alu-console-lang'

export function getStoredLocale() {
  const stored = localStorage.getItem(STORAGE_KEY)
  return SUPPORTED_LOCALES.includes(stored) ? stored : 'en'
}

export function setStoredLocale(locale) {
  if (SUPPORTED_LOCALES.includes(locale)) {
    localStorage.setItem(STORAGE_KEY, locale)
  }
}

const i18n = createI18n({
  legacy: false,
  locale: getStoredLocale(),
  fallbackLocale: 'en',
  messages: { en, ru, tr, de },
})

export default i18n
