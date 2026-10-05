<script setup>
import { computed, ref, watch } from 'vue'

import { useSiteStore } from '@/stores/site'

// The logo uploaded in the console (Company → logo); renders nothing until
// one is set.
defineProps({
  size: { type: Number, default: 40 },
})
const site = useSiteStore()

const logoUrl = computed(() => site.company?.logo?.url || null)
const failed = ref(false)
watch(logoUrl, () => (failed.value = false))
</script>

<template>
  <img
    v-if="logoUrl && !failed"
    class="brand-logo"
    :src="logoUrl"
    :width="size"
    :height="size"
    alt=""
    aria-hidden="true"
    @error="failed = true"
  />
</template>

<style scoped>
.brand-logo {
  flex-shrink: 0;
  display: block;
  object-fit: contain;
}
</style>
