import http from './http'

// params: { search, 'category-id', status: 'active'|'hidden'|'featured', page, 'per-page' }
// → result: { items, total, page, 'per-page' }
export const listProducts = (params) => http.get('/api/products', { params })
export const getProduct = (id) => http.get(`/api/products/${id}`)
export const createProduct = (payload) => http.post('/api/products', payload)
// payload.version is required; omit payload.images to keep the images as they are.
export const updateProduct = (id, payload) => http.put(`/api/products/${id}`, payload)
export const deleteProduct = (id) => http.delete(`/api/products/${id}`)

// Short product list for pickers (e.g. the banner form); max 20 results.
export const lookupProducts = (search) => http.get('/api/products/lookup', { params: search ? { search } : {} })
