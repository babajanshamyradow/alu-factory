import http from './http'

export function login(username, password) {
  return http.post('/login', { username, password })
}

export function logout() {
  return http.get('/logout')
}

// Restores the logged-in admin's profile (username/fullname/role/email/lang)
// after a page refresh, since the session cookie itself carries no readable
// user data. A 401/ERROR response here is a normal "not logged in" case, not
// an unexpected failure — callers should treat it as such.
export function me() {
  return http.get('/me')
}
