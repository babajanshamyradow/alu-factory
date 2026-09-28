<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { scrollToTop } from '@/composables/motion'
import { useSiteStore } from '@/stores/site'
import AppIcon from './AppIcon.vue'
import BrandLogo from './BrandLogo.vue'
import LangSwitcher from './LangSwitcher.vue'

const { t } = useI18n()
const site = useSiteStore()
const year = new Date().getFullYear()
const company = computed(() => site.company || {})
</script>

<template>
  <footer class="footer">
    <div class="footer__glow" />
    <div class="container">
      <div class="footer__top">
        <div class="footer__about" v-reveal>
          <RouterLink to="/" class="footer__brand">
            <BrandLogo :size="44" />
            <span>{{ site.companyName }}</span>
          </RouterLink>
          <p>{{ t('footer.tagline') }}</p>
          <LangSwitcher variant="inline" />
        </div>

        <div v-reveal="100">
          <h4 class="footer__title">{{ t('footer.navigation') }}</h4>
          <ul class="footer__list">
            <li><RouterLink to="/">{{ t('nav.home') }}</RouterLink></li>
            <li><RouterLink to="/products">{{ t('nav.catalog') }}</RouterLink></li>
            <li><RouterLink to="/about">{{ t('nav.about') }}</RouterLink></li>
            <li><RouterLink to="/contact">{{ t('nav.contact') }}</RouterLink></li>
          </ul>
        </div>

        <div v-if="site.categories.length" v-reveal="200">
          <h4 class="footer__title">{{ t('nav.catalog') }}</h4>
          <ul class="footer__list">
            <li v-for="c in site.categories.slice(0, 6)" :key="c.id">
              <RouterLink :to="{ path: '/products', query: { category: c.slug } }">{{ c.name }}</RouterLink>
            </li>
          </ul>
        </div>

        <div v-reveal="300">
          <h4 class="footer__title">{{ t('footer.contacts') }}</h4>
          <ul class="footer__list footer__contacts">
            <li v-if="company.phone">
              <AppIcon name="phone" :size="18" /><a :href="`tel:${company.phone}`">{{ company.phone }}</a>
            </li>
            <li v-if="company.email">
              <AppIcon name="mail" :size="18" /><a :href="`mailto:${company.email}`">{{ company.email }}</a>
            </li>
            <li v-if="company.address"><AppIcon name="pin" :size="18" /><span>{{ company.address }}</span></li>
            <li v-if="!company.phone && !company.email && !company.address">
              <RouterLink to="/contact" class="link-arrow">{{ t('nav.contact') }} <AppIcon name="arrow" :size="16" /></RouterLink>
            </li>
          </ul>
        </div>
      </div>

      <div class="footer__huge" aria-hidden="true">{{ site.companyName }}</div>

      <div class="footer__bottom">
        <span>© {{ year }} {{ site.companyName }}. {{ t('footer.rights') }}</span>
        <button v-magnetic type="button" class="footer__top-btn" :aria-label="t('common.backToTop')" @click="scrollToTop()">
          <AppIcon name="arrow-up" :size="20" />
        </button>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  position: relative;
  background: var(--c-ink);
  color: var(--c-on-dark);
  padding: clamp(64px, 8vw, 110px) 0 28px;
  overflow: hidden;
  isolation: isolate;
}

.footer__glow {
  position: absolute;
  left: -20%;
  top: -40%;
  width: 70vw;
  height: 70vw;
  background: radial-gradient(circle, rgba(58, 134, 255, 0.22), transparent 60%);
  z-index: -1;
}

.footer__top {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr 1.3fr;
  gap: 40px;
}

.footer__about {
  display: grid;
  gap: 18px;
  align-content: start;
}

.footer__about p {
  color: var(--c-on-dark-muted);
  max-width: 320px;
}

.footer__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-family: var(--f-display);
  font-weight: 700;
  font-size: 19px;
}

.footer__title {
  font-size: 14px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--c-on-dark-muted);
  margin-bottom: 18px;
  font-family: var(--f-body);
  font-weight: 800;
}

.footer__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 12px;
}

.footer__list a {
  position: relative;
  transition: color 0.3s;
}

.footer__list a:hover {
  color: var(--c-accent);
}

.footer__contacts li {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  color: var(--c-on-dark-muted);
  word-break: break-word;
}

.footer__contacts svg {
  flex-shrink: 0;
  margin-top: 3px;
  color: var(--c-accent);
}

.footer__huge {
  font-family: var(--f-display);
  font-weight: 800;
  font-size: clamp(48px, 13vw, 200px);
  line-height: 1;
  letter-spacing: -0.03em;
  margin: clamp(48px, 7vw, 96px) 0 24px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: clip;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.02));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.footer__bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 14px;
  color: var(--c-on-dark-muted);
}

.footer__top-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--c-gradient);
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 10px 30px rgba(67, 97, 238, 0.4);
}

@media (max-width: 900px) {
  .footer__top {
    grid-template-columns: 1fr 1fr;
  }

  .footer__about {
    grid-column: 1 / -1;
  }
}

@media (max-width: 520px) {
  .footer__top {
    grid-template-columns: 1fr;
  }
}
</style>
