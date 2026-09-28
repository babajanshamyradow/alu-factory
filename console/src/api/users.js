import http from './http'

export const listUsers = (search) => http.get('/api/users', { params: search ? { search } : {} })
export const getUser = (username) => http.get(`/api/users/${encodeURIComponent(username)}`)
export const createUser = (payload) => http.post('/api/users', payload)
export const updateUser = (username, payload) => http.put(`/api/users/${encodeURIComponent(username)}`, payload)
export const setUserLocked = (username, locked) =>
  http.put(`/api/users/${encodeURIComponent(username)}/lock`, { locked })
export const resetUserPassword = (username, password) =>
  http.put(`/api/users/${encodeURIComponent(username)}/password`, { password })
export const deleteUser = (username) => http.delete(`/api/users/${encodeURIComponent(username)}`)

// Any logged-in user, for their own account.
export const changeOwnPassword = (oldPassword, newPassword) =>
  http.put('/api/profile/password', { 'old-password': oldPassword, 'new-password': newPassword })
