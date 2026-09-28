<script setup>
import { useSiteStore } from '@/stores/site'
import AnimatedTitle from './AnimatedTitle.vue'

// Dark header band for inner pages (catalog, about, contact, product).
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  image: { type: Object, default: null }, // optional media_json background
  compact: { type: Boolean, default: false },
})

const site = useSiteStore()
</script>

<template>
  <section class="page-hero" :class="{ 'page-hero--compact': compact, 'page-hero--image': image }">
    <div v-if="image" class="page-hero__bg">
      <img v-parallax="0.35" :src="image.url" :alt="image['alt-text'] || ''" />
    </div>
    <div class="page-hero__glow" />
    <div class="page-hero__grid" />
    <div class="container">
      <slot name="top" />
      <template v-if="site.introDone">
        <p v-if="eyebrow" class="eyebrow page-hero__eyebrow">{{ eyebrow }}</p>
        <AnimatedTitle v-if="title" tag="h1" class="title-xl page-hero__title" :text="title" immediate :delay="150" />
        <p v-if="subtitle" class="lead page-hero__subtitle">{{ subtitle }}</p>
      </template>
      <slot />
    </div>
  </section>
</template>

<style scoped>
.page-hero--compact {
  padding-bottom: clamp(40px, 5vw, 64px);
}

.page-hero--compact .page-hero__title {
  font-size: clamp(28px, 4.2vw, 56px);
}

.page-hero__bg {
  position: absolute;
  inset: -15% 0;
  z-index: -2;
}

.page-hero__bg img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.page-hero--image::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  background: linear-gradient(90deg, rgba(11, 16, 32, 0.92), rgba(11, 16, 32, 0.55));
}

.page-hero__eyebrow {
  animation: rise 0.9s var(--ease-out) both;
}

.page-hero__title {
  max-width: 980px;
}

.page-hero__subtitle {
  margin-top: 22px;
  animation: rise 1s 0.45s var(--ease-out) both;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
}
</style>
