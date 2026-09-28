<script setup>
// Same mark as console/src/components/BrandLogo.vue.
defineProps({
  size: { type: Number, default: 40 },
})
const gradientId = `site-logo-${Math.random().toString(36).slice(2, 8)}`
</script>

<template>
  <svg class="brand-logo" :width="size" :height="size" viewBox="0 0 40 40" fill="none" aria-hidden="true">
    <defs>
      <linearGradient :id="gradientId" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
        <stop stop-color="#4361ee" />
        <stop offset="0.55" stop-color="#3a86ff" />
        <stop offset="1" stop-color="#4cc9f0" />
      </linearGradient>
    </defs>
    <rect width="40" height="40" rx="11" :fill="`url(#${gradientId})`" />
    <path class="brand-logo__a" d="M11 29 L20 10 L29 29" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" />
    <path class="brand-logo__bar" d="M15 22.5 H25" stroke="#fff" stroke-width="3.2" stroke-linecap="round" opacity="0.7" />
  </svg>
</template>

<style scoped>
.brand-logo {
  flex-shrink: 0;
  display: block;
}
</style>
