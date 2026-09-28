<script setup>
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'

const { t } = useI18n()
</script>

<template>
  <section class="not-found">
    <div class="page-hero__glow" />
    <div class="page-hero__grid" />
    <div class="container not-found__inner">
      <p class="not-found__code" aria-hidden="true">404</p>
      <h1 class="title-lg">{{ t('notFound.title') }}</h1>
      <p class="lead">{{ t('notFound.text') }}</p>
      <RouterLink v-magnetic to="/" class="btn">{{ t('notFound.home') }} <AppIcon name="arrow" class="arrow" /></RouterLink>
    </div>
  </section>
</template>

<style scoped>
.not-found {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  background: var(--c-ink);
  color: #fff;
  overflow: hidden;
  isolation: isolate;
  padding: var(--header-h) 0 40px;
}

.not-found__inner {
  display: grid;
  justify-items: center;
  gap: 20px;
  text-align: center;
}

.not-found .lead {
  color: var(--c-on-dark-muted);
}

.not-found__code {
  font-family: var(--f-display);
  font-weight: 800;
  font-size: clamp(120px, 26vw, 300px);
  line-height: 0.9;
  background: var(--c-gradient);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation:
    glitch 4s ease-in-out infinite,
    shift 6s ease infinite;
}

@keyframes glitch {
  0%,
  100% {
    transform: translateY(0) rotate(0);
  }
  50% {
    transform: translateY(-14px) rotate(-2deg);
  }
}

@keyframes shift {
  50% {
    background-position: 100% 50%;
  }
}
</style>
