<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { LOCALE_LABELS, SUPPORTED_LOCALES, setLocale } from '@/i18n'
import AppIcon from './AppIcon.vue'

defineProps({
  // 'dropdown' in the header, 'inline' (a row of pills) in the mobile menu/footer.
  variant: { type: String, default: 'dropdown' },
})

const { locale, t } = useI18n()
const open = ref(false)
const root = ref(null)

function choose(code) {
  setLocale(code)
  open.value = false
}

function onDocClick(e) {
  if (root.value && !root.value.contains(e.target)) open.value = false
}

onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div v-if="variant === 'inline'" class="lang-inline" role="group" :aria-label="t('common.language')">
    <button
      v-for="code in SUPPORTED_LOCALES"
      :key="code"
      type="button"
      class="lang-inline__btn"
      :class="{ 'is-active': code === locale }"
      :title="LOCALE_LABELS[code]"
      @click="choose(code)"
    >
      {{ code.toUpperCase() }}
    </button>
  </div>

  <div v-else ref="root" class="lang" :class="{ 'is-open': open }" @keydown.esc="open = false">
    <button
      type="button"
      class="lang__toggle"
      :aria-label="t('common.language')"
      :aria-expanded="open"
      @click="open = !open"
    >
      <AppIcon name="globe" :size="18" />
      <span>{{ locale.toUpperCase() }}</span>
      <AppIcon name="chevron-down" :size="14" class="lang__chevron" />
    </button>
    <Transition name="lang-menu">
      <ul v-if="open" class="lang__menu" role="listbox">
        <li v-for="(code, i) in SUPPORTED_LOCALES" :key="code" :style="{ '--i': i }">
          <button
            type="button"
            role="option"
            :aria-selected="code === locale"
            :class="{ 'is-active': code === locale }"
            @click="choose(code)"
          >
            <span class="lang__code">{{ code.toUpperCase() }}</span>
            {{ LOCALE_LABELS[code] }}
          </button>
        </li>
      </ul>
    </Transition>
  </div>
</template>

<style scoped>
.lang {
  position: relative;
}

.lang__toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 42px;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.05em;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, currentColor 25%, transparent);
  transition: background 0.3s;
}

.lang__toggle:hover {
  background: color-mix(in srgb, currentColor 8%, transparent);
}

.lang__chevron {
  transition: transform 0.4s var(--ease-out);
}

.is-open .lang__chevron {
  transform: rotate(180deg);
}

.lang__menu {
  position: absolute;
  right: 0;
  top: calc(100% + 10px);
  min-width: 190px;
  margin: 0;
  padding: 8px;
  list-style: none;
  background: #fff;
  color: var(--c-text);
  border-radius: 16px;
  box-shadow: var(--shadow-lg);
  transform-origin: top right;
}

.lang__menu button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  text-align: left;
  transition: background 0.25s;
}

.lang__menu button:hover {
  background: var(--c-bg-soft);
}

.lang__menu button.is-active {
  background: color-mix(in srgb, var(--c-primary) 10%, transparent);
  color: var(--c-primary);
}

.lang__code {
  font-size: 11px;
  font-weight: 800;
  width: 28px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: var(--c-bg-soft);
}

.lang-menu-enter-active {
  transition:
    opacity 0.3s,
    transform 0.45s var(--ease-out);
}

.lang-menu-leave-active {
  transition:
    opacity 0.2s,
    transform 0.2s;
}

.lang-menu-enter-from,
.lang-menu-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

.lang-menu-enter-active li {
  animation: item-in 0.5s var(--ease-out) both;
  animation-delay: calc(var(--i) * 40ms);
}

@keyframes item-in {
  from {
    opacity: 0;
    transform: translateX(10px);
  }
}

.lang-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.lang-inline__btn {
  height: 38px;
  min-width: 48px;
  padding: 0 12px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 13px;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, currentColor 25%, transparent);
  transition:
    background 0.3s,
    color 0.3s;
}

.lang-inline__btn.is-active {
  background: var(--c-gradient);
  color: #fff;
  box-shadow: none;
}
</style>
