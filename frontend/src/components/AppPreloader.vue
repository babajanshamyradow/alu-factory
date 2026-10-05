<script setup>
import BrandLogo from './BrandLogo.vue'

defineProps({
  name: { type: String, default: '' },
})
</script>

<template>
  <div class="preloader" role="status" aria-live="polite">
    <div class="preloader__panel preloader__panel--back" />
    <div class="preloader__panel">
      <div class="preloader__content">
        <BrandLogo :size="64" class="preloader__logo" />
        <div class="preloader__bar"><span /></div>
        <p class="preloader__name">{{ name }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.preloader {
  position: fixed;
  inset: 0;
  z-index: 1000;
  pointer-events: none;
}

.preloader__panel {
  position: absolute;
  inset: 0;
  background: var(--c-ink);
  display: grid;
  place-items: center;
  transition: transform 1s var(--ease-in-out);
}

.preloader__panel--back {
  background: var(--c-gradient);
  transition-delay: 0.12s;
}

.preloader__content {
  display: grid;
  justify-items: center;
  gap: 22px;
  transition: opacity 0.4s ease;
}

.preloader__logo {
  animation: logo-pop 1.2s var(--ease-out) both;
}

.preloader__bar {
  width: 160px;
  height: 3px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.12);
  overflow: hidden;
}

.preloader__bar span {
  display: block;
  height: 100%;
  width: 40%;
  background: var(--c-gradient);
  border-radius: inherit;
  animation: loading 1.1s var(--ease-in-out) infinite;
}

.preloader__name {
  font-family: var(--f-display);
  font-size: 13px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--c-on-dark-muted);
  min-height: 1em;
}

@keyframes logo-pop {
  from {
    transform: scale(0.6) rotate(-12deg);
    opacity: 0;
  }
}

@keyframes loading {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(260%);
  }
}

/* Leaving: panels slide up one after another (see <Transition name="preloader"> in App.vue). */
.preloader-leave-active {
  transition: opacity 0.01s 1.2s;
}

.preloader-leave-active .preloader__content {
  opacity: 0;
}

.preloader-leave-to .preloader__panel {
  transform: translateY(-100%);
}
</style>
