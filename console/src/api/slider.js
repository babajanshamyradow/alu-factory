import http from './http'

export const listSliderItems = (search) => http.get('/api/slider-items', { params: search ? { search } : {} })
export const getSliderItem = (id) => http.get(`/api/slider-items/${id}`)
export const createSliderItem = (payload) => http.post('/api/slider-items', payload)
export const updateSliderItem = (id, payload) => http.put(`/api/slider-items/${id}`, payload)
export const deleteSliderItem = (id) => http.delete(`/api/slider-items/${id}`)
