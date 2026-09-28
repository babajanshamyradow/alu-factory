<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { getProducts } from '@/api/site'
import AppIcon from '@/components/AppIcon.vue'
import PageHero from '@/components/PageHero.vue'
import ProductCard from '@/components/ProductCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import { ScrollTrigger } from '@/composables/motion'
import { useSiteStore } from '@/stores/site'

const PER_PAGE = 12
const SEARCH_DEBOUNCE_MS = 350

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const site = useSiteStore()

// Filters live in the URL (?category=&search=) so they survive reloads and can be shared.
const category = computed(() => (typeof route.query.category === 'string' ? route.query.category : ''))
const search = computed(() => (typeof route.query.search === 'string' ? route.query.search : ''))
const searchInput = ref(search.value)

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const loadingMore = ref(false)
const failed = ref(false)
let requestId = 0

const hasMore = computed(() => items.value.length < total.value)
const activeCategory = computed(() => site.categories.find((c) => c.slug === category.value) || null)

async function load(append = false) {
  const id = ++requestId
  failed.value = false
  if (append) loadingMore.value = true
  else loading.value = true
  try {
    const nextPage = append ? page.value + 1 : 1
    const result = await getProducts({
      category: category.value || undefined,
      search: search.value || undefined,
      page: nextPage,
      'per-page': PER_PAGE,
    })
    if (id !== requestId) return
    items.value = append ? [...items.value, ...result.items] : result.items
    total.value = result.total
    page.value = nextPage
  } catch {
    if (id === requestId) failed.value = true
  } finally {
    if (id === requestId) {
      loading.value = false
      loadingMore.value = false
      nextTick(() => ScrollTrigger.refresh())
    }
  }
}

function setQuery(patch) {
  const query = { ...route.query, ...patch }
  for (const key of Object.keys(query)) if (!query[key]) delete query[key]
  router.replace({ query })
}

let debounce = null
watch(searchInput, (value) => {
  clearTimeout(debounce)
  debounce = setTimeout(() => setQuery({ search: value.trim() }), SEARCH_DEBOUNCE_MS)
})
watch(search, (value) => {
  if (value !== searchInput.value.trim()) searchInput.value = value
})
watch([category, search], () => load())

function resetFilters() {
  searchInput.value = ''
  router.replace({ query: {} })
}

// Sliding highlight under the active category chip.
const chipsEl = ref(null)
const indicator = ref({ left: 0, width: 0, visible: false })
function moveIndicator() {
  const active = chipsEl.value?.querySelector('.chip.is-active')
  if (!active) return (indicator.value.visible = false)
  indicator.value = { left: active.offsetLeft, width: active.offsetWidth, visible: true }
  active.scrollIntoView?.({ block: 'nearest', inline: 'center', behavior: 'smooth' })
}
watch([category, () => site.categories, () => t('catalog.all')], () => nextTick(moveIndicator), { flush: 'post' })

onMounted(() => {
  load()
  nextTick(moveIndicator)
  window.addEventListener('resize', moveIndicator)
})
onBeforeUnmount(() => {
  clearTimeout(debounce)
  window.removeEventListener('resize', moveIndicator)
})
</script>

<template>
  <div class="catalog">
    <PageHero
      :eyebrow="t('catalog.eyebrow')"
      :title="activeCategory ? activeCategory.name : t('catalog.title')"
      :subtitle="activeCategory?.description || t('catalog.subtitle')"
    />

    <div class="filters">
      <div class="container filters__inner">
        <div ref="chipsEl" class="chips" role="tablist">
          <span
            class="chips__indicator"
            :style="{ transform: `translateX(${indicator.left}px)`, width: `${indicator.width}px`, opacity: indicator.visible ? 1 : 0 }"
          />
          <button
            type="button"
            role="tab"
            class="chip"
            :class="{ 'is-active': !category }"
            :aria-selected="!category"
            @click="setQuery({ category: '' })"
          >
            {{ t('catalog.all') }}
            <span class="chip__count">{{ site.productsTotal }}</span>
          </button>
          <button
            v-for="c in site.categories"
            :key="c.id"
            type="button"
            role="tab"
            class="chip"
            :class="{ 'is-active': category === c.slug }"
            :aria-selected="category === c.slug"
            @click="setQuery({ category: c.slug })"
          >
            {{ c.name }}
            <span class="chip__count">{{ c['products-count'] }}</span>
          </button>
        </div>

        <label class="search">
          <AppIcon name="search" :size="18" />
          <input v-model="searchInput" type="search" :placeholder="t('catalog.search')" :aria-label="t('catalog.search')" />
          <button v-if="searchInput" type="button" class="search__clear" :aria-label="t('nav.close')" @click="searchInput = ''">
            <AppIcon name="close" :size="16" />
          </button>
        </label>
      </div>
    </div>

    <section class="section catalog__body">
      <div class="container">
        <p class="catalog__found">
          <Transition name="fade" mode="out-in">
            <span :key="loading ? 'l' : total">{{ loading ? '…' : t('catalog.found', total) }}</span>
          </Transition>
        </p>

        <div v-if="loading" class="grid-cards">
          <SkeletonCard v-for="n in 8" :key="n" />
        </div>

        <div v-else-if="failed" class="state-box">
          <h3>{{ t('common.error') }}</h3>
          <button type="button" class="btn" @click="load()">{{ t('common.retry') }}</button>
        </div>

        <div v-else-if="!items.length" class="state-box empty">
          <div class="empty__icon"><AppIcon name="search" :size="40" /></div>
          <h3>{{ t('catalog.empty') }}</h3>
          <p>{{ t('catalog.emptyText') }}</p>
          <button type="button" class="btn" @click="resetFilters">{{ t('catalog.reset') }}</button>
        </div>

        <TransitionGroup v-else tag="div" name="grid" class="grid-cards" appear>
          <div v-for="(p, i) in items" :key="p.id" class="grid-item" :style="{ '--i': i % PER_PAGE }">
            <ProductCard :product="p" />
          </div>
        </TransitionGroup>

        <div v-if="!loading && hasMore" class="catalog__more">
          <button v-magnetic type="button" class="btn btn--ghost" :disabled="loadingMore" @click="load(true)">
            <span v-if="loadingMore" class="spinner" />
            {{ t('catalog.loadMore') }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.filters {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  border-bottom: 1px solid var(--c-line);
}

.filters__inner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding-top: 14px;
  padding-bottom: 14px;
}

.chips {
  position: relative;
  display: flex;
  gap: 6px;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: none;
  padding: 4px;
  background: var(--c-bg-soft);
  border-radius: 999px;
}

.chips::-webkit-scrollbar {
  display: none;
}

.chips__indicator {
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  border-radius: 999px;
  background: var(--c-ink);
  transition:
    transform 0.6s var(--ease-out),
    width 0.6s var(--ease-out),
    opacity 0.3s;
  box-shadow: 0 6px 18px rgba(11, 16, 32, 0.25);
}

.chip {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 18px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 14px;
  white-space: nowrap;
  color: var(--c-muted);
  transition: color 0.4s;
}

.chip:hover {
  color: var(--c-text);
}

.chip.is-active {
  color: #fff;
}

.chip__count {
  font-size: 11px;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(93, 103, 132, 0.12);
  transition: background 0.4s;
}

.chip.is-active .chip__count {
  background: rgba(255, 255, 255, 0.18);
}

.search {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 300px;
  flex-shrink: 0;
  height: 50px;
  padding: 0 16px;
  border-radius: 999px;
  background: var(--c-bg-soft);
  color: var(--c-muted);
  box-shadow: inset 0 0 0 1.5px transparent;
  transition:
    box-shadow 0.3s,
    background 0.3s,
    width 0.5s var(--ease-out);
}

.search:focus-within {
  background: #fff;
  box-shadow:
    inset 0 0 0 1.5px var(--c-primary),
    0 8px 24px rgba(67, 97, 238, 0.15);
  color: var(--c-primary);
}

.search input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: none;
  font: inherit;
  font-weight: 600;
  color: var(--c-text);
}

.search input::-webkit-search-cancel-button {
  display: none;
}

.search__clear {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--c-line);
  color: var(--c-muted);
}

.catalog__body {
  padding-top: 40px;
  min-height: 60vh;
}

.catalog__found {
  font-weight: 700;
  color: var(--c-muted);
  margin-bottom: 24px;
}

.catalog__more {
  display: flex;
  justify-content: center;
  margin-top: 56px;
}

.catalog__more .btn {
  color: var(--c-ink);
}

.empty__icon {
  width: 96px;
  height: 96px;
  margin: 0 auto 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--c-bg-soft);
  color: var(--c-primary);
  animation: bob 3s ease-in-out infinite;
}

@keyframes bob {
  50% {
    transform: translateY(-10px);
  }
}

.spinner {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-right-color: transparent;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Grid items: staggered entrance, FLIP on reorder */
.grid-enter-active {
  transition:
    opacity 0.7s var(--ease-out),
    transform 0.8s var(--ease-out);
  transition-delay: calc(var(--i) * 60ms);
}

.grid-enter-from {
  opacity: 0;
  transform: translateY(40px) scale(0.96);
}

.grid-move {
  transition: transform 0.7s var(--ease-out);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 800px) {
  .filters__inner {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .search {
    width: 100%;
  }

  .chips {
    flex: none;
  }
}
</style>
