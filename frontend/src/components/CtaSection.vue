<script setup>
import { useI18n } from 'vue-i18n'

import AnimatedTitle from './AnimatedTitle.vue'
import AppIcon from './AppIcon.vue'

defineProps({
  title: { type: String, default: '' },
  text: { type: String, default: '' },
  to: { type: [String, Object], default: '/contact' },
  button: { type: String, default: '' },
})

const { t } = useI18n()
</script>

<template>
  <section class="section cta-wrap">
    <div class="container">
      <div v-reveal:zoom class="cta">
        <div class="cta__rings" aria-hidden="true"><span /><span /><span /></div>
        <div class="cta__content">
          <AnimatedTitle tag="h2" class="title-lg" :text="title || t('home.ctaTitle')" />
          <p class="cta__text">{{ text || t('home.ctaText') }}</p>
        </div>
        <RouterLink v-magnetic="0.4" :to="to" class="btn btn--light cta__btn">
          {{ button || t('home.contactUs') }} <AppIcon name="arrow" class="arrow" />
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.cta-wrap {
  padding-top: 0;
}

.cta {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  border-radius: calc(var(--radius-lg) + 8px);
  padding: clamp(40px, 6vw, 88px);
  background: var(--c-gradient);
  background-size: 200% 200%;
  animation: gradient-shift 10s ease infinite;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  flex-wrap: wrap;
}

.cta__content {
  max-width: 640px;
}

.cta__text {
  margin-top: 16px;
  font-size: 18px;
  opacity: 0.9;
}

.cta__btn {
  height: 62px;
  padding: 0 34px;
}

.cta__rings {
  position: absolute;
  right: -120px;
  top: 50%;
  z-index: -1;
}

.cta__rings span {
  position: absolute;
  left: 50%;
  top: 50%;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.25);
  transform: translate(-50%, -50%);
  animation: ring 6s linear infinite;
}

.cta__rings span:nth-child(1) {
  width: 300px;
  height: 300px;
}

.cta__rings span:nth-child(2) {
  width: 500px;
  height: 500px;
  animation-delay: -2s;
}

.cta__rings span:nth-child(3) {
  width: 700px;
  height: 700px;
  animation-delay: -4s;
}

@keyframes ring {
  0% {
    transform: translate(-50%, -50%) scale(0.7);
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.2);
    opacity: 0;
  }
}

@keyframes gradient-shift {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}
</style>
