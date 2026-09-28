<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import AppFooter from '@/components/AppFooter.vue'
import AppHeader from '@/components/AppHeader.vue'
import AppPreloader from '@/components/AppPreloader.vue'
import { ScrollTrigger, scrollToTop, startLenis } from '@/composables/motion'
import { usePageTitle } from '@/composables/usePageTitle'
import { useSiteStore } from '@/stores/site'

const MIN_PRELOADER_MS = 900
const MAX_PRELOADER_MS = 2500

const route = useRoute()
const { t } = useI18n()
const site = useSiteStore()
const loading = ref(true)

// Product pages set their own title (the product name).
usePageTitle(() => (route.meta.titleKey ? t(route.meta.titleKey) : ''))

// Scroll to the top once the old page has faded out, then let ScrollTrigger
// measure the new page.
function onAfterLeave() {
  scrollToTop(true)
}

function onAfterEnter() {
  ScrollTrigger.refresh()
}

onMounted(async () => {
  startLenis()
  const started = Date.now()
  await Promise.race([site.load(), new Promise((r) => setTimeout(r, MAX_PRELOADER_MS))])
  const wait = Math.max(0, MIN_PRELOADER_MS - (Date.now() - started))
  setTimeout(() => {
    loading.value = false
    // Hero content mounts while the curtain slides away, so its entrance
    // animation is what the visitor sees first.
    site.introDone = true
  }, wait)
})
</script>

<template>
  <Transition name="preloader" :duration="{ enter: 0, leave: 1300 }">
    <AppPreloader v-if="loading" :name="site.companyName" />
  </Transition>

  <AppHeader />

  <main class="main">
    <RouterView v-slot="{ Component, route: r }">
      <Transition name="page" mode="out-in" @after-leave="onAfterLeave" @after-enter="onAfterEnter">
        <component :is="Component" :key="r.path" />
      </Transition>
    </RouterView>
  </main>

  <AppFooter />
</template>

<style>
.main {
  min-height: 100vh;
}
</style>
