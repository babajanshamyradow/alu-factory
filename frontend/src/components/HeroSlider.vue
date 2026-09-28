<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Swiper from 'swiper'
import { Autoplay, EffectFade, Keyboard, A11y } from 'swiper/modules'

import { prefersReducedMotion, scrollToEl } from '@/composables/motion'
import { useSiteStore } from '@/stores/site'
import AnimatedTitle from './AnimatedTitle.vue'
import AppIcon from './AppIcon.vue'

// Full-screen hero driven by /api/slider. Without slides it falls back to
// an animated brand hero with the i18n tagline.
const props = defineProps({
  slides: { type: Array, default: () => [] },
  companyName: { type: String, default: '' },
})

const AUTOPLAY_MS = 6500
const { t } = useI18n()
const site = useSiteStore()
const root = ref(null)
const swiperEl = ref(null)
const active = ref(0)
const progress = ref(0)
let swiper = null

const count = computed(() => props.slides.length)
const pad = (n) => String(n).padStart(2, '0')
const isExternal = (url) => /^https?:\/\//.test(url || '')

function init() {
  swiper?.destroy(true, true)
  swiper = null
  if (count.value < 1 || !swiperEl.value) return
  swiper = new Swiper(swiperEl.value, {
    modules: [Autoplay, EffectFade, Keyboard, A11y],
    effect: 'fade',
    fadeEffect: { crossFade: true },
    speed: 1400,
    loop: count.value > 1,
    keyboard: { enabled: true },
    allowTouchMove: count.value > 1,
    autoplay:
      count.value > 1 && !prefersReducedMotion()
        ? { delay: AUTOPLAY_MS, disableOnInteraction: false, pauseOnMouseEnter: false }
        : false,
    on: {
      slideChange: (s) => (active.value = s.realIndex),
      autoplayTimeLeft: (_s, _time, ratio) => (progress.value = 1 - ratio),
    },
  })
}

watch(
  () => props.slides,
  async () => {
    await nextTick()
    init()
  },
  { immediate: true, flush: 'post' },
)

onBeforeUnmount(() => swiper?.destroy(true, true))

const next = () => swiper?.slideNext()
const prev = () => swiper?.slidePrev()
const goTo = (i) => swiper?.slideToLoop(i)
const scrollDown = () => scrollToEl(root.value?.nextElementSibling, -60)
</script>

<template>
  <section ref="root" class="hero" :class="{ 'hero--empty': !count }">
    <!-- Slides from the admin panel -->
    <div v-if="count" ref="swiperEl" class="swiper hero__swiper">
      <div class="swiper-wrapper">
        <div v-for="(slide, i) in slides" :key="slide.id" class="swiper-slide hero__slide">
          <div class="hero__media">
            <img
              v-if="slide.media"
              :src="slide.media.url"
              :alt="slide.media['alt-text'] || slide.title || ''"
              :loading="i === 0 ? 'eager' : 'lazy'"
            />
          </div>
          <div class="hero__shade" />
          <div v-if="site.introDone" class="container hero__content">
            <p class="hero__kicker"><span>{{ pad(i + 1) }}</span> {{ companyName }}</p>
            <AnimatedTitle
              v-if="active === i"
              :key="`t-${active}`"
              tag="h1"
              class="title-xl hero__title"
              :text="slide.title || t('home.heroTitle')"
              immediate
              :delay="250"
            />
            <p v-if="active === i" :key="`s-${active}`" class="hero__subtitle">
              {{ slide.subtitle || t('home.heroSubtitle') }}
            </p>
            <div v-if="active === i" :key="`a-${active}`" class="hero__actions">
              <a v-if="isExternal(slide['link-url'])" v-magnetic :href="slide['link-url']" class="btn" target="_blank" rel="noopener">
                {{ t('common.learnMore') }} <AppIcon name="arrow" class="arrow" />
              </a>
              <RouterLink v-else v-magnetic :to="slide['link-url'] || '/products'" class="btn">
                {{ slide['link-url'] ? t('common.learnMore') : t('home.exploreCatalog') }}
                <AppIcon name="arrow" class="arrow" />
              </RouterLink>
              <RouterLink to="/contact" class="btn btn--ghost">{{ t('home.contactUs') }}</RouterLink>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Fallback brand hero -->
    <div v-else class="hero__fallback">
      <div class="hero__orb hero__orb--1" />
      <div class="hero__orb hero__orb--2" />
      <div class="hero__grid" />
      <div v-if="site.introDone" class="container hero__content">
        <p class="hero__kicker">{{ companyName }}</p>
        <AnimatedTitle tag="h1" class="title-xl hero__title" :text="t('home.heroTitle')" immediate :delay="300" />
        <p class="hero__subtitle">{{ t('home.heroSubtitle') }}</p>
        <div class="hero__actions">
          <RouterLink v-magnetic to="/products" class="btn">
            {{ t('home.exploreCatalog') }} <AppIcon name="arrow" class="arrow" />
          </RouterLink>
          <RouterLink to="/contact" class="btn btn--ghost">{{ t('home.contactUs') }}</RouterLink>
        </div>
      </div>
    </div>

    <!-- Controls -->
    <div class="container hero__controls">
      <button type="button" class="hero__scroll" @click="scrollDown">
        <span class="hero__mouse"><span /></span>
        {{ t('home.scroll') }}
      </button>

      <div v-if="count > 1" class="hero__nav">
        <div class="hero__counter">
          <span class="hero__counter-current">
            <Transition name="count" mode="out-in"><span :key="active">{{ pad(active + 1) }}</span></Transition>
          </span>
          <span class="hero__counter-line"><span :style="{ transform: `scaleX(${progress})` }" /></span>
          <span>{{ pad(count) }}</span>
        </div>
        <div class="hero__dots">
          <button
            v-for="(s, i) in slides"
            :key="s.id"
            type="button"
            :class="{ 'is-active': i === active }"
            :aria-label="`${i + 1}`"
            @click="goTo(i)"
          />
        </div>
        <button type="button" class="hero__arrow" :aria-label="t('common.prev')" @click="prev">
          <AppIcon name="arrow-left" />
        </button>
        <button type="button" class="hero__arrow" :aria-label="t('common.next')" @click="next">
          <AppIcon name="arrow" />
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  height: 100vh;
  height: 100svh;
  min-height: 600px;
  background: var(--c-ink);
  color: #fff;
  overflow: hidden;
  isolation: isolate;
}

.hero__swiper,
.hero__slide,
.hero__fallback {
  height: 100%;
}

.hero__slide {
  position: relative;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero__media {
  position: absolute;
  inset: 0;
  z-index: -2;
}

.hero__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.18);
  transition: transform 8s linear;
}

/* Ken Burns zoom on the visible slide */
.swiper-slide-active .hero__media img {
  transform: scale(1);
}

.hero__shade {
  position: absolute;
  inset: 0;
  z-index: -1;
  background:
    linear-gradient(90deg, rgba(11, 16, 32, 0.88) 0%, rgba(11, 16, 32, 0.55) 45%, rgba(11, 16, 32, 0.15) 100%),
    linear-gradient(0deg, rgba(11, 16, 32, 0.8) 0%, transparent 40%);
}

.hero__content {
  position: relative;
  padding-top: var(--header-h);
}

.hero__fallback {
  position: relative;
  display: flex;
  align-items: center;
}

.hero__kicker {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--c-accent);
  margin-bottom: 24px;
  animation: fade-up 1s 0.1s var(--ease-out) both;
}

.hero__kicker span {
  font-family: var(--f-display);
  color: #fff;
  padding-right: 14px;
  border-right: 1px solid rgba(255, 255, 255, 0.3);
}

.hero__title {
  max-width: 960px;
  margin-bottom: 26px;
}

.hero__subtitle {
  max-width: 560px;
  font-size: clamp(16px, 1.5vw, 20px);
  color: rgba(255, 255, 255, 0.78);
  margin-bottom: 40px;
  animation: fade-up 1.1s 0.7s var(--ease-out) both;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  animation: fade-up 1.1s 0.9s var(--ease-out) both;
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
}

/* Fallback visuals */
.hero__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  z-index: -1;
}

.hero__orb--1 {
  width: 60vw;
  height: 60vw;
  right: -15vw;
  top: -15vw;
  background: radial-gradient(circle, rgba(67, 97, 238, 0.65), transparent 65%);
  animation: orb 14s ease-in-out infinite alternate;
}

.hero__orb--2 {
  width: 45vw;
  height: 45vw;
  right: 10vw;
  bottom: -20vw;
  background: radial-gradient(circle, rgba(76, 201, 240, 0.45), transparent 65%);
  animation: orb 11s ease-in-out infinite alternate-reverse;
}

.hero__grid {
  position: absolute;
  inset: 0;
  z-index: -1;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: radial-gradient(ellipse at 70% 40%, #000 10%, transparent 70%);
  animation: grid-move 20s linear infinite;
}

@keyframes orb {
  to {
    transform: translate(-10vw, 8vw) scale(1.2);
  }
}

@keyframes grid-move {
  to {
    background-position: 72px 72px;
  }
}

/* Controls */
.hero__controls {
  position: absolute;
  left: 0;
  right: 0;
  bottom: clamp(24px, 4vw, 44px);
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.hero__scroll {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.7);
}

.hero__mouse {
  width: 24px;
  height: 38px;
  border-radius: 14px;
  border: 1.5px solid rgba(255, 255, 255, 0.5);
  display: flex;
  justify-content: center;
  padding-top: 7px;
}

.hero__mouse span {
  width: 3px;
  height: 7px;
  border-radius: 2px;
  background: #fff;
  animation: wheel 1.8s var(--ease-in-out) infinite;
}

@keyframes wheel {
  0% {
    transform: translateY(0);
    opacity: 1;
  }
  70% {
    transform: translateY(12px);
    opacity: 0;
  }
  100% {
    opacity: 0;
  }
}

.hero__nav {
  display: flex;
  align-items: center;
  gap: 14px;
}

.hero__counter {
  display: flex;
  align-items: center;
  gap: 14px;
  font-family: var(--f-display);
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.hero__counter-current {
  color: #fff;
  font-size: 22px;
  display: inline-block;
  overflow: hidden;
  height: 1.2em;
  line-height: 1.2;
}

.hero__counter-current > span {
  display: inline-block;
}

.hero__counter-line {
  width: 90px;
  height: 2px;
  background: rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.hero__counter-line span {
  display: block;
  height: 100%;
  background: var(--c-gradient);
  transform-origin: left;
}

.hero__dots {
  display: none;
  gap: 8px;
}

.hero__dots button {
  width: 8px;
  height: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.35);
  transition:
    width 0.5s var(--ease-out),
    background 0.3s;
}

.hero__dots button.is-active {
  width: 26px;
  background: #fff;
}

.hero__arrow {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.3);
  transition:
    background 0.3s,
    transform 0.4s var(--ease-out);
}

.hero__arrow:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: scale(1.08);
}

.count-enter-active,
.count-leave-active {
  transition: transform 0.5s var(--ease-out);
}

.count-enter-from {
  transform: translateY(100%);
}

.count-leave-to {
  transform: translateY(-100%);
}

@media (max-width: 700px) {
  .hero__scroll,
  .hero__counter,
  .hero__arrow {
    display: none;
  }

  .hero__dots {
    display: flex;
  }

  .hero__controls {
    justify-content: center;
  }
}
</style>
