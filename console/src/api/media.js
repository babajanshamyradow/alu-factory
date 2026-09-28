import http from './http'

// The explicit multipart header stops axios from JSON-encoding the FormData
// (http.js defaults to application/json); the browser fills in the boundary.
export const uploadMedia = (file, altText) => {
  const form = new FormData()
  form.append('file', file)
  if (altText) form.append('alt-text', altText)
  return http.post('/api/media', form, { headers: { 'Content-Type': 'multipart/form-data' } })
}
