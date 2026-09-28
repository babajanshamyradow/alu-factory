// Keep in sync with backend media_access.ALLOWED_TYPES / config.ini limits.
export const IMAGE_EXT = ['jpg', 'jpeg', 'png', 'webp', 'gif']
export const VIDEO_EXT = ['mp4', 'webm']
export const IMAGE_MAX_MB = 5
export const VIDEO_MAX_MB = 50

export const fileExt = (name) => name.split('.').pop().toLowerCase()

// Returns an i18n error key, or null when the file may be uploaded.
export function checkUploadFile(file, { allowVideo = false } = {}) {
  const ext = fileExt(file.name)
  const isVideo = VIDEO_EXT.includes(ext)
  if (!IMAGE_EXT.includes(ext) && !(allowVideo && isVideo)) return 'errors.file-type-not-allowed'
  if (file.size > (isVideo ? VIDEO_MAX_MB : IMAGE_MAX_MB) * 1024 * 1024) return 'errors.file-too-large'
  return null
}

// Error key for a failed /api/media call (401/403 are handled by http.js).
export function uploadErrorKey(error) {
  const status = error.response?.status
  if (status === 413) return 'errors.file-too-large'
  return [401, 403].includes(status) ? null : 'errors.internal-server-error'
}
