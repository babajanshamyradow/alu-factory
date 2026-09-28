import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// Set lazily to avoid a circular import between the auth store and this
// module (the store imports api/auth.js, which imports this file).
let onUnauthorized = null
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      onUnauthorized?.()
    } else if (status === 403) {
      ElMessage.error('Permission denied')
    }
    return Promise.reject(error)
  },
)

export default http
