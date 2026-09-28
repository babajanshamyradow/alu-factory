import { ref, watch } from 'vue'

const STORAGE_KEY = 'alu-console-theme'

function readStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') return stored
  } catch {
    // localStorage unavailable — fall through to the OS preference.
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(value) {
  document.documentElement.classList.toggle('dark', value === 'dark')
}

// Module-level singleton so every component shares the same state.
const theme = ref(readStoredTheme())
applyTheme(theme.value)

watch(theme, (value) => {
  applyTheme(value)
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Non-fatal: theme just won't persist across reloads.
  }
})

export function useTheme() {
  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }
  return { theme, toggleTheme }
}
