<script setup>
import { useI18n } from 'vue-i18n'
import { ArrowDown, Check } from '@element-plus/icons-vue'

import { SUPPORTED_LOCALES, setStoredLocale } from '@/i18n'

const LANG_LABELS = {
  en: 'English',
  ru: 'Русский',
  tm: 'Türkmençe',
  tr: 'Türkçe',
  de: 'Deutsch',
}

const props = defineProps({
  modelValue: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue'])

const { locale } = useI18n()

function selectLang(code) {
  locale.value = code
  setStoredLocale(code)
  emit('update:modelValue', code)
}
</script>

<template>
  <el-dropdown trigger="click" @command="selectLang">
    <button type="button" class="lang-switcher">
      <span class="lang-switcher__code">{{ locale.toUpperCase() }}</span>
      <span class="lang-switcher__label">{{ LANG_LABELS[locale] }}</span>
      <el-icon class="lang-switcher__arrow"><ArrowDown /></el-icon>
    </button>
    <template #dropdown>
      <el-dropdown-menu class="lang-menu">
        <el-dropdown-item
          v-for="code in SUPPORTED_LOCALES"
          :key="code"
          :command="code"
          :class="{ 'is-active': code === locale }"
        >
          <span class="lang-menu__code">{{ code.toUpperCase() }}</span>
          <span class="lang-menu__label">{{ LANG_LABELS[code] }}</span>
          <el-icon v-if="code === locale" class="lang-menu__check"><Check /></el-icon>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<style scoped>
.lang-switcher {
  height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px 0 6px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.lang-switcher:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}
.lang-switcher__code {
  padding: 3px 6px;
  border-radius: 6px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.lang-switcher__arrow {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.lang-menu__code {
  width: 28px;
  font-size: 11px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
}
.lang-menu__label {
  min-width: 96px;
}
.lang-menu__check {
  margin-left: 8px;
  color: var(--el-color-primary);
}
.is-active {
  font-weight: 600;
  color: var(--el-color-primary);
}

@media (max-width: 600px) {
  .lang-switcher__label {
    display: none;
  }
}
</style>
