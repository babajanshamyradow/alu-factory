import axios from 'axios'

const http = axios.create({
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

/** Error carrying the backend's `error-msg` codes (e.g. `contact-name-invalid`). */
export class ApiError extends Error {
  constructor(codes) {
    super(codes.join(', ') || 'request-failed')
    this.codes = codes
  }
}

// Backend envelope: { status, result?, 'error-msg'? }. An empty list/object
// comes back without `result`, so callers pass the fallback they expect.
export async function unwrap(request, fallback = null) {
  let response
  try {
    response = await request
  } catch {
    throw new ApiError(['network-error'])
  }
  const data = response.data || {}
  if (data.status !== 'SUCCESS') throw new ApiError(data['error-msg'] || [])
  return data.result ?? fallback
}

export default http
