import { watchEffect } from 'vue'

import { useSiteStore } from '@/stores/site'

/** Keeps document.title as "<page> — <company>"; `getTitle` may be reactive. */
export function usePageTitle(getTitle) {
  const site = useSiteStore()
  watchEffect(() => {
    const page = getTitle()
    document.title = page ? `${page} — ${site.companyName}` : site.companyName
  })
}
