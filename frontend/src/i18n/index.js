import { createI18n } from 'vue-i18n'

import en from './locales/en.json'
import ru from './locales/ru.json'
import tr from './locales/tr.json'
import de from './locales/de.json'

// Same set as SystemLang in backend/src/model/enums.py.
export const SUPPORTED_LOCALES = ['en', 'ru', 'tr', 'de']

export const LOCALE_LABELS = {
  en: 'English',
  ru: 'Русский',
  tr: 'Türkçe',
  de: 'Deutsch',
}

const STORAGE_KEY = 'alu-site-lang'

function initialLocale() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (SUPPORTED_LOCALES.includes(stored)) return stored
  } catch {
    // Storage blocked (private mode) — fall through to the browser language.
  }
  const browser = (navigator.language || 'en').slice(0, 2).toLowerCase()
  return SUPPORTED_LOCALES.includes(browser) ? browser : 'en'
}

// Russian: 1 товар | 2 товара | 5 товаров (choice index 0 = "none").
function ruPlural(choice, choicesLength) {
  if (choice === 0) return 0
  const n = Math.abs(choice) % 100
  const n1 = n % 10
  const form = n > 10 && n < 20 ? 3 : n1 === 1 ? 1 : n1 >= 2 && n1 <= 4 ? 2 : 3
  return Math.min(form, choicesLength - 1)
}

const i18n = createI18n({
  legacy: false,
  locale: initialLocale(),
  fallbackLocale: 'en',
  messages: { en, ru, tr, de },
  pluralRules: { ru: ruPlural },
})

export function setLocale(locale) {
  if (!SUPPORTED_LOCALES.includes(locale)) return
  i18n.global.locale.value = locale
  document.documentElement.lang = locale
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // Not persisted — the choice still applies for this visit.
  }
}

document.documentElement.lang = i18n.global.locale.value

export default i18n
