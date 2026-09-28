<script setup>
// Endless running line of words (category names on the home page).
defineProps({
  items: { type: Array, default: () => [] },
  reverse: { type: Boolean, default: false },
})
</script>

<template>
  <div class="marquee" :class="{ 'marquee--reverse': reverse }" aria-hidden="true">
    <div v-for="copy in 2" :key="copy" class="marquee__track">
      <span v-for="(item, i) in items" :key="`${copy}-${i}`" class="marquee__item">
        {{ item }} <i class="marquee__star">✦</i>
      </span>
    </div>
  </div>
</template>

<style scoped>
.marquee {
  display: flex;
  overflow: hidden;
  user-select: none;
  mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent);
}

.marquee__track {
  display: flex;
  flex-shrink: 0;
  min-width: 100%;
  justify-content: space-around;
  animation: marquee 30s linear infinite;
}

.marquee--reverse .marquee__track {
  animation-direction: reverse;
}

.marquee:hover .marquee__track {
  animation-play-state: paused;
}

.marquee__item {
  display: inline-flex;
  align-items: center;
  gap: 32px;
  padding-right: 32px;
  font-family: var(--f-display);
  font-weight: 700;
  font-size: clamp(28px, 5vw, 64px);
  white-space: nowrap;
  color: transparent;
  -webkit-text-stroke: 1.5px rgba(26, 33, 56, 0.25);
  transition: color 0.4s;
}

.marquee__item:hover {
  color: var(--c-primary);
  -webkit-text-stroke-color: transparent;
}

.marquee__star {
  font-style: normal;
  font-size: 0.5em;
  color: var(--c-accent);
  -webkit-text-stroke: 0;
}

@keyframes marquee {
  to {
    transform: translateX(-100%);
  }
}
</style>
