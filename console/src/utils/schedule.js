// The backend stores schedule dates as naive UTC and returns them without an
// offset ('2026-09-28T10:00:00.000000'); parse them as UTC, not local time.
export function parseUtc(value) {
  if (!value) return null
  return new Date(value.slice(0, 23) + 'Z')
}

// 'hidden' | 'scheduled' | 'expired' | 'live' — what the website shows now
// for a scheduled display block (slider item, banner).
export function displayStatus(item, now = new Date()) {
  if (!item['is-active']) return 'hidden'
  const startsAt = parseUtc(item['starts-at'])
  const endsAt = parseUtc(item['ends-at'])
  if (startsAt && startsAt > now) return 'scheduled'
  if (endsAt && endsAt <= now) return 'expired'
  return 'live'
}

// Short localized date+time for a backend (naive UTC) timestamp, or null.
export function formatDateTime(value, locale) {
  const date = parseUtc(value)
  if (!date) return null
  try {
    return new Intl.DateTimeFormat(locale, { dateStyle: 'short', timeStyle: 'short' }).format(date)
  } catch {
    // e.g. 'tm' is not a BCP 47 tag Intl knows.
    return date.toLocaleString()
  }
}
