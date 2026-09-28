import http from './http'

export const listBanners = (search) => http.get('/api/banners', { params: search ? { search } : {} })
export const getBanner = (id) => http.get(`/api/banners/${id}`)
export const createBanner = (payload) => http.post('/api/banners', payload)
export const updateBanner = (id, payload) => http.put(`/api/banners/${id}`, payload)
export const deleteBanner = (id) => http.delete(`/api/banners/${id}`)
