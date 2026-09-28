import http from './http'

// params: { search, status: 'new'|'read'|'archived', page, 'per-page' }
// → result: { items, total, page, 'per-page', counts: { new, read, archived } }
export const listContactMessages = (params) => http.get('/api/contact-messages', { params })
export const getContactMessageCounts = () => http.get('/api/contact-messages/counts')
// Full message incl. 'ip-address' / 'user-agent'.
export const getContactMessage = (id) => http.get(`/api/contact-messages/${id}`)
// The customer's text is read-only; only the processing status changes.
export const setContactMessageStatus = (id, status) => http.put(`/api/contact-messages/${id}/status`, { status })
export const deleteContactMessage = (id) => http.delete(`/api/contact-messages/${id}`)
// Creating messages is the public website form's job: POST /api/contact-messages (no login).
