import http, { unwrap } from './http'

// Public site API (backend/src/sip). Everything is anonymous and read-only
// except the contact form.
export const getCompany = () => unwrap(http.get('/api/company'))
export const getSlider = () => unwrap(http.get('/api/slider'), [])
export const getBanners = () => unwrap(http.get('/api/banners'), [])
export const getCategories = () => unwrap(http.get('/api/categories'), [])

// params: { search?, category? (slug), featured? (1), page?, 'per-page'? }
export const getProducts = (params) =>
  unwrap(http.get('/api/products', { params }), { items: [], total: 0, page: 1, 'per-page': 12 })
export const getProduct = (slug) => unwrap(http.get(`/api/products/${encodeURIComponent(slug)}`))

// payload: { name, email?, phone?, message, website (honeypot, keep empty) }
export const sendContactMessage = (payload) => unwrap(http.post('/api/contact-messages', payload))
