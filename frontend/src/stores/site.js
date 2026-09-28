import { defineStore } from 'pinia'

import { getCategories, getCompany } from '@/api/site'

export const DEFAULT_COMPANY_NAME = 'Alu Factory'

// Company info and categories are shown on almost every page (header,
// footer, catalog filters), so they are loaded once per visit.
export const useSiteStore = defineStore('site', {
  state: () => ({
    company: null,
    categories: [],
    loaded: false,
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
      const [company, categories] = await Promise.allSettled([getCompany(), getCategories()])
      if (company.status === 'fulfilled') this.company = company.value
      if (categories.status === 'fulfilled') this.categories = categories.value
      this.loaded = true
    },
  },
})
