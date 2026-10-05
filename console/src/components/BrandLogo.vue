<script setup>
import { ref, watch } from 'vue'

import { useBrandStore } from '@/stores/brand'

// The company logo uploaded in Company; renders nothing until one is set.
defineProps({
  size: { type: Number, default: 36 },
})
const brand = useBrandStore()
const failed = ref(false)
watch(() => brand.logoUrl, () => (failed.value = false))
</script>

<template>
  <img
    v-if="brand.logoUrl && !failed"
    class="brand-logo"
    :src="brand.logoUrl"
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
