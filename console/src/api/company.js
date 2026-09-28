import http from './http'

// Single company row: getCompany() has no `result` until it is created,
// createCompany() works only once, afterwards updateCompany() edits it.
export const getCompany = () => http.get('/api/company')
export const createCompany = (payload) => http.post('/api/company', payload)
export const updateCompany = (payload) => http.put('/api/company', payload)

// Company gallery (tbl_company_image). Every change is saved immediately.
export const listCompanyImages = () => http.get('/api/company/images')
// payload: { 'media-id', caption?, 'is-active'?, 'sort-order'? } — no sort-order appends to the end.
export const createCompanyImage = (payload) => http.post('/api/company/images', payload)
export const updateCompanyImage = (id, payload) => http.put(`/api/company/images/${id}`, payload)
// ids: every gallery image id in the new order.
export const reorderCompanyImages = (ids) => http.put('/api/company/images/order', { ids })
export const deleteCompanyImage = (id) => http.delete(`/api/company/images/${id}`)
