<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { User, Key, ChatDotRound, Grid } from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'

const { t, locale } = useI18n()
const authStore = useAuthStore()

const displayName = computed(() => authStore.user?.fullname || authStore.user?.username)

const greetingKey = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'dashboard.goodMorning'
  if (hour < 18) return 'dashboard.goodAfternoon'
  return 'dashboard.goodEvening'
})

const today = computed(() =>
  new Intl.DateTimeFormat(locale.value === 'tm' ? 'tk' : locale.value, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date()),
)

const profileItems = computed(() => [
  { icon: User, label: t('dashboard.username'), value: authStore.user?.username },
  { icon: Key, label: t('dashboard.role'), value: authStore.role },
  { icon: ChatDotRound, label: t('dashboard.language'), value: authStore.lang?.toUpperCase() },
])
</script>

<template>
  <div class="dashboard">
    <section class="hero">
      <div class="hero__pattern" />
      <div class="hero__content">
        <span class="hero__date">{{ today }}</span>
        <h1 class="hero__title">{{ t(greetingKey, { name: displayName }) }}</h1>
        <p class="hero__subtitle">{{ t('dashboard.subtitle') }}</p>
      </div>
    </section>

    <div class="grid">
      <section class="af-card panel">
        <header class="panel__header">
          <h3>{{ t('dashboard.profile') }}</h3>
        </header>
        <ul class="profile-list">
          <li v-for="item in profileItems" :key="item.label" class="profile-list__item">
            <span class="profile-list__icon">
              <el-icon :size="18"><component :is="item.icon" /></el-icon>
            </span>
            <span class="profile-list__label">{{ item.label }}</span>
            <span class="profile-list__value">{{ item.value || '—' }}</span>
          </li>
        </ul>
      </section>

      <section class="af-card panel panel--wide">
        <header class="panel__header">
          <h3>{{ t('dashboard.modules') }}</h3>
        </header>
        <div class="modules-empty">
          <div class="modules-empty__icon">
            <el-icon :size="28"><Grid /></el-icon>
          </div>
          <p class="modules-empty__title">{{ t('dashboard.modulesEmptyTitle') }}</p>
          <p class="modules-empty__text">{{ t('dashboard.modulesEmptyText') }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ---------- Hero ---------- */
.hero {
  position: relative;
  overflow: hidden;
  padding: 36px 40px;
  border-radius: 20px;
  color: #fff;
  background: var(--af-gradient);
  box-shadow: 0 16px 40px rgba(67, 97, 238, 0.28);
}
.hero__pattern {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 85% 20%, rgba(255, 255, 255, 0.25) 0, transparent 30%),
    radial-gradient(circle at 100% 100%, rgba(255, 255, 255, 0.18) 0, transparent 35%);
}
.hero__pattern::after {
  content: '';
  position: absolute;
  right: -40px;
  top: 50%;
  width: 260px;
  height: 260px;
  transform: translateY(-50%) rotate(12deg);
  border: 28px solid rgba(255, 255, 255, 0.1);
  border-radius: 48px;
}
.hero__content {
  position: relative;
  max-width: 640px;
}
.hero__date {
  display: inline-block;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
  backdrop-filter: blur(6px);
}
.hero__title {
  margin: 16px 0 8px;
  font-size: clamp(24px, 3vw, 34px);
  font-weight: 800;
  line-height: 1.15;
}
.hero__subtitle {
  margin: 0;
  font-size: 15px;
  opacity: 0.85;
}

/* ---------- Panels ---------- */
.grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 2fr);
  gap: 24px;
}
.panel {
  padding: 22px 24px;
}
.panel__header h3 {
  margin: 0 0 16px;
  font-size: 15px;
  font-weight: 700;
}

.profile-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.profile-list__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-top: 1px dashed var(--el-border-color-lighter);
}
.profile-list__item:first-child {
  border-top: 0;
  padding-top: 0;
}
.profile-list__icon {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.profile-list__label {
  flex: 1;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.profile-list__value {
  font-size: 14px;
  font-weight: 600;
}

.modules-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 180px;
  padding: 24px;
  border: 1.5px dashed var(--el-border-color);
  border-radius: 14px;
  background: var(--el-fill-color-lighter);
}
.modules-empty__icon {
  width: 56px;
  height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  margin-bottom: 14px;
}
.modules-empty__title {
  margin: 0 0 6px;
  font-weight: 700;
}
.modules-empty__text {
  margin: 0;
  max-width: 380px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--el-text-color-secondary);
}

@media (max-width: 992px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 600px) {
  .hero {
    padding: 28px 22px;
  }
}
</style>
