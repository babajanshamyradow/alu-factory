<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { setScrollLocked } from '@/composables/motion'
import { useSiteStore } from '@/stores/site'
import AppIcon from './AppIcon.vue'
import BrandLogo from './BrandLogo.vue'
import LangSwitcher from './LangSwitcher.vue'

const { t } = useI18n()
const route = useRoute()
const site = useSiteStore()

const NAV = [
  { name: 'home', to: '/', label: 'nav.home' },
  { name: 'catalog', to: '/products', label: 'nav.catalog' },
  { name: 'about', to: '/about', label: 'nav.about' },
  { name: 'contact', to: '/contact', label: 'nav.contact' },
]

const scrolled = ref(false)
const hidden = ref(false)
const menuOpen = ref(false)
let lastY = 0

function onScroll() {
  const y = window.scrollY
  scrolled.value = y > 30
  // Hide while scrolling down, show again as soon as the visitor scrolls up.
  hidden.value = !menuOpen.value && y > 240 && y > lastY
  lastY = y
}

function isActive(item) {
  if (item.name === 'home') return route.name === 'home'
  if (item.name === 'catalog') return route.path.startsWith('/products')
  return route.name === item.name
}

watch(menuOpen, (open) => setScrollLocked(open))
watch(
  () => route.fullPath,
  () => (menuOpen.value = false),
)

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <header class="header" :class="{ 'is-scrolled': scrolled, 'is-hidden': hidden, 'is-menu': menuOpen }">
    <div class="container header__inner">
      <RouterLink to="/" class="header__brand" :aria-label="site.companyName">
        <BrandLogo :size="40" />
        <span class="header__name">{{ site.companyName }}</span>
      </RouterLink>

      <nav class="header__nav" aria-label="Main">
        <RouterLink
          v-for="item in NAV"
          :key="item.name"
          :to="item.to"
          class="header__link"
          :class="{ 'is-active': isActive(item) }"
        >
          <span class="header__link-text" :data-text="t(item.label)">{{ t(item.label) }}</span>
        </RouterLink>
      </nav>

      <div class="header__actions">
        <LangSwitcher class="header__lang" />
        <RouterLink v-magnetic to="/contact" class="btn header__cta">
          {{ t('common.requestQuote') }}
        </RouterLink>
        <button
          type="button"
          class="header__burger"
          :aria-label="menuOpen ? t('nav.close') : t('nav.menu')"
          :aria-expanded="menuOpen"
          @click="menuOpen = !menuOpen"
        >
          <span /><span />
        </button>
      </div>
    </div>
  </header>

  <Transition name="menu">
    <div v-if="menuOpen" class="mobile-menu">
      <nav class="mobile-menu__nav">
        <RouterLink
          v-for="(item, i) in NAV"
          :key="item.name"
          :to="item.to"
          class="mobile-menu__link"
          :class="{ 'is-active': isActive(item) }"
          :style="{ '--i': i }"
        >
          <span class="mobile-menu__num">0{{ i + 1 }}</span>
          {{ t(item.label) }}
        </RouterLink>
      </nav>
      <div class="mobile-menu__foot">
        <LangSwitcher variant="inline" />
        <a v-if="site.company?.phone" :href="`tel:${site.company.phone}`" class="mobile-menu__contact">
          <AppIcon name="phone" :size="18" /> {{ site.company.phone }}
        </a>
        <a v-if="site.company?.email" :href="`mailto:${site.company.email}`" class="mobile-menu__contact">
          <AppIcon name="mail" :size="18" /> {{ site.company.email }}
        </a>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.header {
  position: fixed;
  inset: 0 0 auto;
  z-index: 100;
  height: var(--header-h);
  color: #fff;
  transition:
    transform 0.6s var(--ease-out),
    background 0.4s,
    box-shadow 0.4s,
    height 0.4s var(--ease-out);
}

.header.is-scrolled {
  --header-h: 68px;
  background: rgba(11, 16, 32, 0.72);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06);
}

.header.is-hidden {
  transform: translateY(-100%);
}

.header.is-menu {
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.header__inner {
  height: 100%;
  display: flex;
  align-items: center;
  gap: 24px;
}

.header__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  margin-right: auto;
}

.header__brand :deep(svg) {
  transition: transform 0.6s var(--ease-out);
}

.header__brand:hover :deep(svg) {
  transform: rotate(-8deg) scale(1.06);
}

.header__name {
  font-family: var(--f-display);
  font-weight: 700;
  font-size: 17px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header__nav {
  display: flex;
  gap: 6px;
}

.header__link {
  position: relative;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.78);
  transition: color 0.3s;
}

/* Text rolls up on hover. */
.header__link-text {
  position: relative;
  display: inline-block;
  overflow: hidden;
  vertical-align: top;
  line-height: 1.4;
}

.header__link-text::after {
  content: attr(data-text);
  position: absolute;
  left: 0;
  top: 100%;
  color: #fff;
}

.header__link-text,
.header__link-text::after {
  transition: transform 0.5s var(--ease-out);
}

.header__link:hover .header__link-text {
  transform: translateY(-100%);
}

.header__link:hover .header__link-text::after {
  transform: none;
}

.header__link::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 2px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-accent);
  transform: translateX(-50%) scale(0);
  transition: transform 0.5s var(--ease-out);
}

.header__link.is-active {
  color: #fff;
}

.header__link.is-active::after {
  transform: translateX(-50%) scale(1);
}

.header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header__cta {
  height: 44px;
  padding: 0 22px;
  font-size: 14px;
}

.header__burger {
  display: none;
  position: relative;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
}

.header__burger span {
  position: absolute;
  left: 14px;
  right: 14px;
  height: 2px;
  border-radius: 2px;
  background: currentColor;
  transition:
    transform 0.5s var(--ease-out),
    top 0.5s var(--ease-out);
}

.header__burger span:first-child {
  top: 18px;
}

.header__burger span:last-child {
  top: 26px;
}

.is-menu .header__burger span:first-child {
  top: 22px;
  transform: rotate(45deg);
}

.is-menu .header__burger span:last-child {
  top: 22px;
  transform: rotate(-45deg);
}

@media (max-width: 1100px) {
  .header__cta {
    display: none;
  }
}

@media (max-width: 900px) {
  .header__nav,
  .header__lang {
    display: none;
  }

  .header__burger {
    display: block;
  }
}

/* ---------- Mobile menu ---------- */
.mobile-menu {
  position: fixed;
  inset: 0;
  z-index: 99;
  background: var(--c-ink);
  color: #fff;
  padding: calc(var(--header-h) + 32px) var(--gutter) 32px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 32px;
  overflow-y: auto;
  clip-path: circle(150% at calc(100% - 44px) 38px);
}

.mobile-menu::before {
  content: '';
  position: absolute;
  inset: auto -30% -30% auto;
  width: 90vw;
  height: 90vw;
  background: radial-gradient(circle, rgba(67, 97, 238, 0.4), transparent 60%);
  pointer-events: none;
}

.mobile-menu__nav {
  display: grid;
  gap: 6px;
}

.mobile-menu__link {
  display: flex;
  align-items: baseline;
  gap: 16px;
  font-family: var(--f-display);
  font-size: clamp(30px, 9vw, 48px);
  font-weight: 700;
  padding: 6px 0;
  color: rgba(255, 255, 255, 0.85);
  animation: menu-link 0.8s var(--ease-out) both;
  animation-delay: calc(0.15s + var(--i) * 70ms);
}

.mobile-menu__link.is-active {
  color: transparent;
  background: var(--c-gradient);
  -webkit-background-clip: text;
  background-clip: text;
}

.mobile-menu__num {
  font-family: var(--f-body);
  font-size: 13px;
  color: var(--c-on-dark-muted);
  -webkit-text-fill-color: var(--c-on-dark-muted);
}

.mobile-menu__foot {
  display: grid;
  gap: 16px;
  position: relative;
  animation: menu-link 0.8s 0.45s var(--ease-out) both;
}

.mobile-menu__contact {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--c-on-dark-muted);
}

@keyframes menu-link {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
}

.menu-enter-active,
.menu-leave-active {
  transition: clip-path 0.8s var(--ease-in-out);
}

.menu-enter-from,
.menu-leave-to {
  clip-path: circle(0% at calc(100% - 44px) 38px);
}
</style>
