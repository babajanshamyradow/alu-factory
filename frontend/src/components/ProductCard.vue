<script setup>
import { useI18n } from 'vue-i18n'

import AppIcon from './AppIcon.vue'
import MediaImg from './MediaImg.vue'

defineProps({
  product: { type: Object, required: true },
})

const { t } = useI18n()
</script>

<template>
  <RouterLink v-tilt="6" :to="`/products/${product.slug}`" class="card">
    <div class="card__media">
      <MediaImg :media="product.cover" :alt="product.name">
        <template #empty>
          <div class="card__placeholder"><AppIcon name="box" :size="48" /></div>
        </template>
      </MediaImg>
      <span v-if="product.category" class="card__badge">{{ product.category.name }}</span>
      <span class="card__zoom"><AppIcon name="arrow" :size="22" /></span>
    </div>
    <div class="card__body">
      <h3 class="card__title">{{ product.name }}</h3>
      <p v-if="product['short-description']" class="card__text">{{ product['short-description'] }}</p>
      <span class="card__more">{{ t('common.details') }} <AppIcon name="arrow" :size="16" /></span>
    </div>
    <span class="card__shine" />
  </RouterLink>
</template>

<style scoped>
.card {
  --mx: 50%;
  --my: 50%;
  position: relative;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--c-line);
  overflow: hidden;
  transform-style: preserve-3d;
  will-change: transform;
  transition:
    box-shadow 0.5s var(--ease-out),
    border-color 0.5s;
  height: 100%;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  border-color: transparent;
}

.card__media {
  position: relative;
  aspect-ratio: 4 / 3.2;
  overflow: hidden;
}

.card__media :deep(.media-img) {
  width: 100%;
  height: 100%;
}

.card__media :deep(img) {
  transition:
    transform 1.2s var(--ease-out),
    opacity 0.9s,
    filter 0.9s !important;
}

.card:hover .card__media :deep(img) {
  transform: scale(1.08);
}

.card__placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: #b5bfd6;
}

.card__badge {
  position: absolute;
  left: 14px;
  top: 14px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: var(--c-ink);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.card__zoom {
  position: absolute;
  right: 14px;
  bottom: 14px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--c-gradient);
  transform: scale(0) rotate(-45deg);
  transition: transform 0.6s var(--ease-out);
  box-shadow: 0 10px 24px rgba(67, 97, 238, 0.45);
}

.card:hover .card__zoom {
  transform: scale(1) rotate(0);
}

.card__body {
  padding: 22px 24px 26px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  transform: translateZ(30px);
}

.card__title {
  font-size: 19px;
  line-height: 1.3;
  transition: color 0.3s;
}

.card:hover .card__title {
  color: var(--c-primary);
}

.card__text {
  color: var(--c-muted);
  font-size: 15px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card__more {
  margin-top: auto;
  padding-top: 6px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 14px;
  color: var(--c-primary);
}

.card__more svg {
  transition: transform 0.4s var(--ease-out);
}

.card:hover .card__more svg {
  transform: translateX(5px);
}

/* Light spot following the pointer (set by v-tilt) */
.card__shine {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(500px circle at var(--mx) var(--my), rgba(76, 201, 240, 0.14), transparent 40%);
  opacity: 0;
  transition: opacity 0.4s;
}

.card:hover .card__shine {
  opacity: 1;
}
</style>
