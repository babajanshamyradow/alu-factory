import http from './http'

export const listCategories = (search) => http.get('/api/categories', { params: search ? { search } : {} })
export const getCategory = (id) => http.get(`/api/categories/${id}`)
export const createCategory = (payload) => http.post('/api/categories', payload)
export const updateCategory = (id, payload) => http.put(`/api/categories/${id}`, payload)
export const deleteCategory = (id) => http.delete(`/api/categories/${id}`)
