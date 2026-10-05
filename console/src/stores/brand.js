import { defineStore } from 'pinia'

import { getCompanyBrand } from '@/api/company'

export const DEFAULT_BRAND_NAME = 'Alu-Factory'

// Company name + logo shown in the console chrome. Loaded on boot and
// reloaded after the company is saved, so a new logo shows up everywhere.
export const useBrandStore = defineStore('brand', {
  state: () => ({
    name: null,
    logo: null,
  }),
  getters: {
    displayName: (state) => state.name || DEFAULT_BRAND_NAME,
    logoUrl: (state) => state.logo?.url || null,
  },
  actions: {
    async load() {
      try {
        const { data } = await getCompanyBrand()
        if (data.status !== 'SUCCESS') return
        this.name = data.result?.['company-name'] || null
        this.logo = data.result?.logo || null
      } catch {
        // Non-fatal: the console still works with the default name.
      }
    },
    // Called with the saved company (CompanyView) to skip a round trip.
    set(company) {
      this.name = company?.['company-name'] || null
      this.logo = company?.logo || null
    },
  },
})
