import { defineStore } from 'pinia'

import * as authApi from '@/api/auth'
import { setUnauthorizedHandler } from '@/api/http'
import { hasPermission } from '@/permissions'

const STORAGE_KEY = 'alu-console-user'

// Shared by main.js and the router guard so /me is requested only once on boot.
let restorePromise = null

function readCachedUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function writeCachedUser(user) {
  try {
    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  } catch {
    // localStorage unavailable (private mode, etc.) — non-fatal, session
    // still works, only the "instant" fullname-after-refresh UX is lost.
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // Seeded from localStorage so a page refresh shows the fullname/role
    // immediately instead of a blank shell while /me resolves. This is a
    // deliberate client-side cache of the last known /login or /me result —
    // the backend itself has no endpoint that returns this on its own
    // (the session cookie carries no readable user data), see console/README.md.
    user: readCachedUser(),
    isAuthenticated: false,
    ready: false,
  }),
  getters: {
    role: (state) => state.user?.role ?? null,
    lang: (state) => state.user?.lang ?? 'en',
    // Usage: authStore.can('users.create')
    can: (state) => (permission) => hasPermission(state.user?.role, permission),
  },
  actions: {
    async login(username, password) {
      const { data } = await authApi.login(username, password)
      if (data.status === 'SUCCESS') {
        this.setUser(data.result)
        this.isAuthenticated = true
        return { success: true }
      }
      return { success: false, errors: data['error-msg'] || [] }
    },

    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.clearSession()
      }
    },

    // Called on app boot (and awaited by the router guard) to confirm the
    // session cookie (if any) is still valid and refresh the cached user
    // profile. Repeated calls share the same in-flight request.
    restoreSession() {
      restorePromise ??= this._fetchSession()
      return restorePromise
    },

    async _fetchSession() {
      try {
        const { data } = await authApi.me()
        if (data.status === 'SUCCESS') {
          this.setUser(data.result)
          this.isAuthenticated = true
        } else {
          this.clearSession()
        }
      } catch {
        this.clearSession()
      } finally {
        this.ready = true
      }
    },

    setUser(user) {
      this.user = user
      writeCachedUser(user)
    },

    clearSession() {
      this.user = null
      this.isAuthenticated = false
      writeCachedUser(null)
    },
  },
})

// Wired once here (not in api/http.js) to avoid a circular import between
// this store and the axios instance it configures.
export function installAuthUnauthorizedHandler(router) {
  setUnauthorizedHandler(() => {
    const authStore = useAuthStore()
    const wasAuthenticated = authStore.isAuthenticated
    authStore.clearSession()
    if (wasAuthenticated && router.currentRoute.value.name !== 'login') {
      router.push({ name: 'login' })
    }
  })
}
