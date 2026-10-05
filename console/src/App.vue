<script setup>
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { elementPlusLocales } from '@/i18n'
import { useBrandStore } from '@/stores/brand'

const { locale } = useI18n()
const elLocale = computed(() => elementPlusLocales[locale.value])

// Company name + logo for the login page, sidebar and the tab (favicon/title).
const brand = useBrandStore()
brand.load()
watch(
  () => [brand.logoUrl, brand.displayName],
  ([logoUrl, name]) => {
    document.title = `${name} Admin`
    let link = document.querySelector('link[rel="icon"]')
    if (!logoUrl) return link?.remove()
    if (!link) {
      link = document.createElement('link')
      link.rel = 'icon'
      document.head.appendChild(link)
    }
    link.href = logoUrl
  },
  { immediate: true },
)
</script>

<template>
  <el-config-provider :locale="elLocale">
    <router-view />
  </el-config-provider>
</template>
