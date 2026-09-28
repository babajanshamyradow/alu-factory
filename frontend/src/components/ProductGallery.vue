<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import Swiper from 'swiper'
import { EffectFade, Keyboard, Thumbs } from 'swiper/modules'

import AppIcon from './AppIcon.vue'
import ImageLightbox from './ImageLightbox.vue'
import MediaImg from './MediaImg.vue'

// Product photos: main slider + thumbnails; click opens the lightbox.
const props = defineProps({
  images: { type: Array, default: () => [] }, // media_json list
  alt: { type: String, default: '' },
})

const mainEl = ref(null)
const thumbsEl = ref(null)
const active = ref(0)
const lightbox = ref(null)
let main = null
let thumbs = null

function destroy() {
  main?.destroy(true, true)
  thumbs?.destroy(true, true)
  main = thumbs = null
}

async function init() {
  destroy()
  active.value = 0
  await nextTick()
  if (!mainEl.value || props.images.length === 0) return
  if (thumbsEl.value) {
    thumbs = new Swiper(thumbsEl.value, {
      slidesPerView: 'auto',
      spaceBetween: 12,
      watchSlidesProgress: true,
    })
  }
  main = new Swiper(mainEl.value, {
    modules: [EffectFade, Keyboard, Thumbs],
    effect: 'fade',
    fadeEffect: { crossFade: true },
    speed: 700,
    keyboard: { enabled: true },
    thumbs: thumbs ? { swiper: thumbs } : undefined,
    on: { slideChange: (s) => (active.value = s.activeIndex) },
  })
}

watch(() => props.images, init, { immediate: true, flush: 'post' })
onBeforeUnmount(destroy)
</script>

<template>
  <div class="gallery">
    <div v-if="images.length" class="gallery__main-wrap">
      <div ref="mainEl" class="swiper gallery__main">
        <div class="swiper-wrapper">
          <div v-for="(img, i) in images" :key="img.id" class="swiper-slide">
            <button type="button" class="gallery__open" :aria-label="alt" @click="lightbox = i">
              <MediaImg :media="img" :alt="alt" :eager="i === 0" />
              <span class="gallery__zoom"><AppIcon name="zoom" :size="22" /></span>
            </button>
          </div>
        </div>
      </div>
      <template v-if="images.length > 1">
        <button type="button" class="gallery__arrow gallery__arrow--prev" aria-label="prev" @click="main?.slidePrev()">
          <AppIcon name="chevron-left" />
        </button>
        <button type="button" class="gallery__arrow gallery__arrow--next" aria-label="next" @click="main?.slideNext()">
          <AppIcon name="chevron-right" />
        </button>
        <span class="gallery__count">{{ active + 1 }} / {{ images.length }}</span>
      </template>
    </div>
    <div v-else class="gallery__empty"><AppIcon name="image" :size="64" /></div>

    <div v-if="images.length > 1" ref="thumbsEl" class="swiper gallery__thumbs">
      <div class="swiper-wrapper">
        <div v-for="img in images" :key="img.id" class="swiper-slide gallery__thumb">
          <img :src="img.url" alt="" loading="lazy" />
        </div>
      </div>
    </div>

    <ImageLightbox v-model:index="lightbox" :images="images" />
  </div>
</template>

<style scoped>
.gallery {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.gallery__main-wrap {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--c-bg-soft);
}

.gallery__main {
  aspect-ratio: 1 / 1;
}

.gallery__open {
  display: block;
  width: 100%;
  height: 100%;
  position: relative;
  cursor: zoom-in;
}

.gallery__open :deep(.media-img) {
  width: 100%;
  height: 100%;
}

.gallery__zoom {
  position: absolute;
  right: 18px;
  top: 18px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.9);
  color: var(--c-ink);
  opacity: 0;
  transform: scale(0.7);
  transition:
    opacity 0.3s,
    transform 0.5s var(--ease-out);
}

.gallery__main-wrap:hover .gallery__zoom {
  opacity: 1;
  transform: none;
}

.gallery__arrow {
  position: absolute;
  top: 50%;
  z-index: 2;
  width: 48px;
  height: 48px;
  margin-top: -24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.9);
  color: var(--c-ink);
  box-shadow: var(--shadow);
  opacity: 0;
  transition:
    opacity 0.3s,
    transform 0.5s var(--ease-out);
}

.gallery__arrow--prev {
  left: 16px;
  transform: translateX(-10px);
}

.gallery__arrow--next {
  right: 16px;
  transform: translateX(10px);
}

.gallery__main-wrap:hover .gallery__arrow {
  opacity: 1;
  transform: none;
}

.gallery__count {
  position: absolute;
  left: 18px;
  bottom: 16px;
  z-index: 2;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  background: rgba(11, 16, 32, 0.6);
  backdrop-filter: blur(6px);
}

.gallery__empty {
  aspect-ratio: 1 / 1;
  border-radius: var(--radius-lg);
  background: var(--c-bg-soft);
  display: grid;
  place-items: center;
  color: #b5bfd6;
}

.gallery__thumbs {
  width: 100%;
}

.gallery__thumb {
  width: 88px !important;
  height: 88px;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  opacity: 0.5;
  box-shadow: inset 0 0 0 2px transparent;
  transition:
    opacity 0.3s,
    transform 0.4s var(--ease-out);
}

.gallery__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery__thumb:hover {
  opacity: 0.85;
}

.gallery__thumb.swiper-slide-thumb-active {
  opacity: 1;
  outline: 2px solid var(--c-primary);
  outline-offset: -2px;
}

@media (hover: none) {
  .gallery__arrow,
  .gallery__zoom {
    opacity: 1;
    transform: none;
  }
}
</style>
