import { defineStore } from 'pinia'

import { getCategories, getCompany } from '@/api/site'

export const DEFAULT_COMPANY_NAME = 'Alu Factory'

// Minimum gap between background refreshes (see refresh()).
const REFRESH_INTERVAL_MS = 60 * 1000

// Company info and categories are shown on almost every page (header,
// footer, catalog filters), so they are loaded once per visit and refreshed
// when the visitor comes back to the tab, so console edits (logo, name,
// contacts) show up without a hard reload.
export const useSiteStore = defineStore('site', {
  state: () => ({
    company: null,
    categories: [],
    loaded: false,
    fetchedAt: 0,
    // Set when the preloader starts leaving, so hero animations play in view.
    introDone: false,
  }),
  getters: {
    companyName: (state) => state.company?.['company-name'] || DEFAULT_COMPANY_NAME,
    productsTotal: (state) => state.categories.reduce((sum, c) => sum + (c['products-count'] || 0), 0),
  },
  actions: {
    async load() {
      if (this.loaded) return
      await this.fetch()
      this.loaded = true
    },
    async refresh() {
      if (!this.loaded || Date.now() - this.fetchedAt < REFRESH_INTERVAL_MS) return
      await this.fetch()
    },
    async fetch() {
      this.fetchedAt = Date.now()
      const [company, categories] = await Promise.allSettled([getCompany(), getCategories()])
      if (company.status === 'fulfilled') this.company = company.value
      if (categories.status === 'fulfilled') this.categories = categories.value
    },
  },
})
