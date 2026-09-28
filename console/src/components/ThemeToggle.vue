<script setup>
import { useI18n } from 'vue-i18n'
import { Moon, Sunny } from '@element-plus/icons-vue'

import { useTheme } from '@/composables/useTheme'

const { t } = useI18n()
const { theme, toggleTheme } = useTheme()
</script>

<template>
  <el-tooltip :content="theme === 'dark' ? t('theme.light') : t('theme.dark')" placement="bottom">
    <button type="button" class="theme-toggle" @click="toggleTheme">
      <el-icon :size="18">
        <Sunny v-if="theme === 'dark'" />
        <Moon v-else />
      </el-icon>
    </button>
  </el-tooltip>
</template>

<style scoped>
.theme-toggle {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}
.theme-toggle:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}
</style>
