<script setup>
import { computed, onBeforeUnmount, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { setScrollLocked } from '@/composables/motion'
import AppIcon from './AppIcon.vue'

// Full-screen image viewer. v-model:index — null means closed.
const props = defineProps({
  images: { type: Array, default: () => [] }, // [{ url, 'alt-text'?, caption? }]
})
const index = defineModel('index', { type: Number, default: null })

const { t } = useI18n()
const open = computed(() => index.value !== null && props.images.length > 0)
const current = computed(() => (open.value ? props.images[index.value] : null))
let direction = 1

function go(step) {
  direction = step
  index.value = (index.value + step + props.images.length) % props.images.length
}

function onKey(e) {
  if (!open.value) return
  if (e.key === 'Escape') index.value = null
  else if (e.key === 'ArrowRight') go(1)
  else if (e.key === 'ArrowLeft') go(-1)
}

let touchX = null
const onTouchStart = (e) => (touchX = e.touches[0].clientX)
function onTouchEnd(e) {
  if (touchX === null) return
  const dx = e.changedTouches[0].clientX - touchX
  if (Math.abs(dx) > 50) go(dx < 0 ? 1 : -1)
  touchX = null
}

watch(open, (v) => setScrollLocked(v))
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  if (open.value) setScrollLocked(false)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="lightbox">
      <div v-if="open" class="lightbox" role="dialog" aria-modal="true" @click.self="index = null">
        <button type="button" class="lightbox__close" :aria-label="t('nav.close')" @click="index = null">
          <AppIcon name="close" :size="24" />
        </button>

        <div class="lightbox__stage" @click.self="index = null" @touchstart.passive="onTouchStart" @touchend="onTouchEnd">
          <Transition :name="direction > 0 ? 'slide-next' : 'slide-prev'" mode="out-in">
            <figure :key="index" class="lightbox__figure">
              <img :src="current.url" :alt="current['alt-text'] || current.caption || ''" />
              <figcaption v-if="current.caption">{{ current.caption }}</figcaption>
            </figure>
          </Transition>
        </div>

        <template v-if="images.length > 1">
          <button type="button" class="lightbox__arrow lightbox__arrow--prev" :aria-label="t('common.prev')" @click="go(-1)">
            <AppIcon name="chevron-left" :size="28" />
          </button>
          <button type="button" class="lightbox__arrow lightbox__arrow--next" :aria-label="t('common.next')" @click="go(1)">
            <AppIcon name="chevron-right" :size="28" />
          </button>
          <div class="lightbox__counter">{{ index + 1 }} / {{ images.length }}</div>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 500;
  background: rgba(6, 9, 20, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: grid;
  place-items: center;
  color: #fff;
}

.lightbox__stage {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  padding: 72px 16px;
}

.lightbox__figure {
  margin: 0;
  display: grid;
  gap: 14px;
  justify-items: center;
}

.lightbox__figure img {
  max-width: min(1200px, 92vw);
  max-height: 78vh;
  object-fit: contain;
  border-radius: 14px;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.5);
}

.lightbox__figure figcaption {
  color: var(--c-on-dark-muted);
  text-align: center;
}

.lightbox__close,
.lightbox__arrow {
  position: absolute;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.08);
  transition:
    background 0.3s,
    transform 0.4s var(--ease-out);
}

.lightbox__close:hover,
.lightbox__arrow:hover {
  background: rgba(255, 255, 255, 0.18);
  transform: scale(1.08);
}

.lightbox__close {
  top: 20px;
  right: 20px;
}

.lightbox__arrow--prev {
  left: 20px;
}

.lightbox__arrow--next {
  right: 20px;
}

.lightbox__counter {
  position: absolute;
  bottom: 24px;
  font-family: var(--f-display);
  font-size: 14px;
  color: var(--c-on-dark-muted);
}

@media (max-width: 700px) {
  .lightbox__arrow {
    display: none;
  }
}

.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.4s;
}

.lightbox-enter-active .lightbox__figure {
  transition: transform 0.6s var(--ease-out);
}

.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

.lightbox-enter-from .lightbox__figure {
  transform: scale(0.9);
}

.slide-next-enter-active,
.slide-next-leave-active,
.slide-prev-enter-active,
.slide-prev-leave-active {
  transition:
    opacity 0.35s,
    transform 0.45s var(--ease-out);
}

.slide-next-enter-from,
.slide-prev-leave-to {
  opacity: 0;
  transform: translateX(60px);
}

.slide-next-leave-to,
.slide-prev-enter-from {
  opacity: 0;
  transform: translateX(-60px);
}
</style>
