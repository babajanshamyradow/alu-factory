<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { prefersReducedMotion } from '@/composables/motion'

// Splits the text into words that slide up from behind a mask, one after
// another. Re-plays when the text changes (e.g. switching language).
const props = defineProps({
  text: { type: String, default: '' },
  tag: { type: String, default: 'h2' },
  // Play right away instead of waiting to scroll into view (heroes).
  immediate: { type: Boolean, default: false },
  delay: { type: Number, default: 0 },
  stagger: { type: Number, default: 70 },
})

const root = ref(null)
const visible = ref(false)
const playKey = ref(0)
const words = computed(() => (props.text || '').split(/\s+/).filter(Boolean))

let observer = null

function play() {
  visible.value = false
  playKey.value++
  requestAnimationFrame(() => requestAnimationFrame(() => (visible.value = true)))
}

onMounted(() => {
  if (props.immediate || prefersReducedMotion()) {
    play()
    return
  }
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        play()
        observer.disconnect()
      }
    },
    { threshold: 0.2 },
  )
  observer.observe(root.value)
})

onBeforeUnmount(() => observer?.disconnect())

watch(
  () => props.text,
  () => {
    if (visible.value) play()
  },
)
</script>

<template>
  <component :is="tag" ref="root" class="animated-title" :class="{ 'is-visible': visible }" :aria-label="text">
    <span :key="playKey" class="animated-title__inner" aria-hidden="true">
      <span v-for="(word, i) in words" :key="i" class="animated-title__mask">
        <span class="animated-title__word" :style="{ transitionDelay: `${delay + i * stagger}ms` }">{{ word }}</span>
      </span>
    </span>
  </component>
</template>

<style scoped>
.animated-title__mask {
  display: inline-block;
  overflow: hidden;
  vertical-align: top;
  padding-bottom: 0.08em;
  margin-bottom: -0.08em;
}

.animated-title__mask:not(:last-child) {
  margin-right: 0.26em;
}

.animated-title__word {
  display: inline-block;
  transform: translateY(110%) rotate(4deg);
  transform-origin: left bottom;
  transition: transform 1s var(--ease-out);
}

.is-visible .animated-title__word {
  transform: none;
}
</style>
