<script setup>
import { useI18n } from 'vue-i18n'

import AppIcon from './AppIcon.vue'

// Promo banners from /api/banners: the first one is wide, the rest share a row.
defineProps({
  banners: { type: Array, default: () => [] },
})

const { t } = useI18n()
const isExternal = (url) => /^https?:\/\//.test(url || '')

function linkOf(banner) {
  if (banner.product) return { to: `/products/${banner.product.slug}` }
  if (banner['link-url']) return isExternal(banner['link-url']) ? { href: banner['link-url'] } : { to: banner['link-url'] }
  return null
}
</script>

<template>
  <div class="banners">
    <component
      :is="linkOf(b)?.href ? 'a' : linkOf(b) ? 'RouterLink' : 'div'"
      v-for="(b, i) in banners"
      :key="b.id"
      v-reveal:clip="i % 2 ? 150 : 0"
      :to="linkOf(b)?.to"
      :href="linkOf(b)?.href"
      :target="linkOf(b)?.href ? '_blank' : undefined"
      :rel="linkOf(b)?.href ? 'noopener' : undefined"
      class="banner"
      :class="{ 'banner--wide': i === 0 || (i === banners.length - 1 && i % 2 === 1), 'is-link': linkOf(b) }"
    >
      <div class="banner__media">
        <img v-if="b.media" v-parallax="0.18" :src="b.media.url" :alt="b.media['alt-text'] || b.title || ''" loading="lazy" />
      </div>
      <div class="banner__shade" />
      <div class="banner__content">
        <h3 v-if="b.title" class="banner__title">{{ b.title }}</h3>
        <p v-if="b.subtitle" class="banner__subtitle">{{ b.subtitle }}</p>
        <span v-if="linkOf(b)" class="banner__cta">
          {{ b.product ? b.product.name : t('common.learnMore') }}
          <span class="banner__cta-icon"><AppIcon name="arrow" :size="18" /></span>
        </span>
      </div>
    </component>
  </div>
</template>

<style scoped>
.banners {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: clamp(16px, 2vw, 28px);
}

.banner {
  position: relative;
  min-height: clamp(320px, 38vw, 460px);
  border-radius: var(--radius-lg);
  overflow: hidden;
  isolation: isolate;
  color: #fff;
  display: flex;
  align-items: flex-end;
  background: var(--c-ink-2);
}

.banner--wide {
  grid-column: 1 / -1;
  min-height: clamp(360px, 44vw, 560px);
}

.banner__media {
  position: absolute;
  inset: -12% 0;
  z-index: -2;
}

.banner__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: scale 1.4s var(--ease-out);
}

.banner.is-link:hover .banner__media img {
  scale: 1.06;
}

.banner__shade {
  position: absolute;
  inset: 0;
  z-index: -1;
  background: linear-gradient(0deg, rgba(11, 16, 32, 0.9) 0%, rgba(11, 16, 32, 0.25) 55%, rgba(11, 16, 32, 0.05) 100%);
}

.banner__content {
  padding: clamp(24px, 4vw, 52px);
  max-width: 720px;
}

.banner__title {
  font-size: clamp(24px, 3.2vw, 44px);
  margin-bottom: 12px;
}

.banner__subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: clamp(15px, 1.3vw, 18px);
}

.banner__cta {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  margin-top: 24px;
  font-weight: 700;
}

.banner__cta-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #fff;
  color: var(--c-ink);
  transition:
    transform 0.5s var(--ease-out),
    background 0.3s,
    color 0.3s;
}

.banner.is-link:hover .banner__cta-icon {
  transform: rotate(-45deg);
  background: var(--c-accent);
  color: #fff;
}

@media (max-width: 760px) {
  .banners {
    grid-template-columns: 1fr;
  }
}
</style>
