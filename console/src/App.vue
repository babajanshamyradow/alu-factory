<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { elementPlusLocales } from '@/i18n'

const { locale } = useI18n()
const elLocale = computed(() => elementPlusLocales[locale.value])
</script>

<template>
  <el-config-provider :locale="elLocale">
    <router-view />
  </el-config-provider>
</template>
