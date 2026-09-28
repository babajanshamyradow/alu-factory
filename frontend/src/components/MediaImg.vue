<script setup>
import { ref, watch } from 'vue'

// Lazy image that fades/zooms in once loaded; shows a shimmer until then.
const props = defineProps({
  media: { type: Object, default: null },
  alt: { type: String, default: '' },
  eager: { type: Boolean, default: false },
})

const loaded = ref(false)
watch(
  () => props.media?.url,
  () => (loaded.value = false),
)
</script>

<template>
  <div class="media-img" :class="{ 'is-loaded': loaded, 'is-empty': !media }">
    <img
      v-if="media"
      :src="media.url"
      :alt="media['alt-text'] || alt"
      :width="media.width || undefined"
      :height="media.height || undefined"
      :loading="eager ? 'eager' : 'lazy'"
      decoding="async"
      @load="loaded = true"
      @error="loaded = true"
    />
    <slot v-else name="empty" />
  </div>
</template>

<style scoped>
.media-img {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #e7ebf4, #f6f8fc);
}

.media-img:not(.is-loaded):not(.is-empty)::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.7), transparent);
  animation: shimmer 1.4s infinite;
}

.media-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transform: scale(1.06);
  filter: blur(10px);
  transition:
    opacity 0.9s var(--ease-out),
    transform 1.4s var(--ease-out),
    filter 0.9s var(--ease-out);
}

.media-img.is-loaded img {
  opacity: 1;
  transform: scale(1);
  filter: none;
}
</style>
