<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { HomeFilled } from '@element-plus/icons-vue'

const { t } = useI18n()
const router = useRouter()
</script>

<template>
  <div class="not-found">
    <div class="not-found__glow" />
    <div class="not-found__inner">
      <div class="not-found__code">404</div>
      <h1>{{ t('notFound.title') }}</h1>
      <p>{{ t('notFound.subtitle') }}</p>
      <el-button type="primary" size="large" :icon="HomeFilled" @click="router.push('/')">
        {{ t('notFound.back') }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overflow: hidden;
  text-align: center;
}
.not-found__glow {
  position: absolute;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  background: var(--el-color-primary);
  opacity: 0.12;
  filter: blur(100px);
}
.not-found__inner {
  position: relative;
}
.not-found__code {
  font-size: clamp(96px, 18vw, 160px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.06em;
  background: var(--af-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
h1 {
  margin: 12px 0 8px;
  font-size: 24px;
}
p {
  margin: 0 0 28px;
  color: var(--el-text-color-secondary);
}
</style>
