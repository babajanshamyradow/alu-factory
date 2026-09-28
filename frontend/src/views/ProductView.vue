<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { getProduct } from '@/api/site'
import AnimatedTitle from '@/components/AnimatedTitle.vue'
import AppIcon from '@/components/AppIcon.vue'
import PageHero from '@/components/PageHero.vue'
import ProductCard from '@/components/ProductCard.vue'
import ProductGallery from '@/components/ProductGallery.vue'
import { usePageTitle } from '@/composables/usePageTitle'
import { useSiteStore } from '@/stores/site'

const { t } = useI18n()
const route = useRoute()
const site = useSiteStore()

const product = ref(null)
const loading = ref(true)
const notFound = ref(false)
const failed = ref(false)

usePageTitle(() => (product.value ? product.value.name : notFound.value ? t('product.notFound') : ''))

const quoteLink = computed(() => ({
  path: '/contact',
  query: { product: product.value?.slug },
}))

async function load() {
  loading.value = true
  notFound.value = failed.value = false
  try {
    product.value = await getProduct(route.params.slug)
  } catch (e) {
    product.value = null
    if (e.codes?.includes('product-not-found')) notFound.value = true
    else failed.value = true
  } finally {
    loading.value = false
  }
}

watch(() => route.params.slug, load, { immediate: true })
</script>

<template>
  <div class="product-page">
    <PageHero compact>
      <nav v-if="site.introDone" class="crumbs" aria-label="Breadcrumb">
        <RouterLink to="/">{{ t('product.home') }}</RouterLink>
        <AppIcon name="chevron-right" :size="14" />
        <RouterLink to="/products">{{ t('nav.catalog') }}</RouterLink>
        <template v-if="product?.category">
          <AppIcon name="chevron-right" :size="14" />
          <RouterLink :to="{ path: '/products', query: { category: product.category.slug } }">{{ product.category.name }}</RouterLink>
        </template>
      </nav>
    </PageHero>

    <!-- Loading -->
    <section v-if="loading" class="section product">
      <div class="container product__grid">
        <div class="skeleton" style="aspect-ratio: 1 / 1; border-radius: var(--radius-lg)" />
        <div class="product__skeleton">
          <div class="skeleton" style="height: 18px; width: 30%" />
          <div class="skeleton" style="height: 44px; width: 85%" />
          <div class="skeleton" style="height: 16px; width: 100%" />
          <div class="skeleton" style="height: 16px; width: 70%" />
          <div class="skeleton" style="height: 54px; width: 220px; border-radius: 999px" />
        </div>
      </div>
    </section>

    <!-- Not found / error -->
    <section v-else-if="notFound || failed" class="section">
      <div class="container state-box">
        <h3>{{ notFound ? t('product.notFound') : t('common.error') }}</h3>
        <p v-if="notFound">{{ t('product.notFoundText') }}</p>
        <RouterLink v-if="notFound" to="/products" class="btn">{{ t('common.backToCatalog') }}</RouterLink>
        <button v-else type="button" class="btn" @click="load">{{ t('common.retry') }}</button>
      </div>
    </section>

    <template v-else-if="product">
      <section class="section product">
        <div class="container product__grid">
          <div v-reveal:left class="product__gallery">
            <ProductGallery :images="product.images" :alt="product.name" />
          </div>

          <div class="product__info">
            <RouterLink
              v-if="product.category"
              v-reveal
              :to="{ path: '/products', query: { category: product.category.slug } }"
              class="product__category"
            >
              {{ product.category.name }}
            </RouterLink>
            <AnimatedTitle tag="h1" class="title-lg product__name" :text="product.name" immediate :delay="100" />
            <p v-if="product['short-description']" v-reveal="200" class="lead product__short">
              {{ product['short-description'] }}
            </p>

            <div v-reveal="300" class="product__actions">
              <RouterLink v-magnetic :to="quoteLink" class="btn">
                {{ t('common.requestQuote') }} <AppIcon name="arrow" class="arrow" />
              </RouterLink>
              <RouterLink to="/products" class="btn btn--ghost product__back">
                <AppIcon name="arrow-left" :size="18" /> {{ t('common.backToCatalog') }}
              </RouterLink>
            </div>

            <div v-reveal="400" class="product__ask">
              <span class="product__ask-icon"><AppIcon name="support" :size="24" /></span>
              <div>
                <strong>{{ t('product.askTitle') }}</strong>
                <p>{{ t('product.askText') }}</p>
                <a v-if="site.company?.phone" :href="`tel:${site.company.phone}`" class="link-arrow">
                  <AppIcon name="phone" :size="16" /> {{ site.company.phone }}
                </a>
              </div>
            </div>
          </div>
        </div>

        <div v-if="product.description" class="container">
          <div class="product__desc">
            <h2 v-reveal class="title-md">{{ t('product.description') }}</h2>
            <p v-reveal="120" class="prose">{{ product.description }}</p>
          </div>
        </div>
      </section>

      <section v-if="product.related?.length" class="section section--soft">
        <div class="container">
          <div class="section-head">
            <AnimatedTitle tag="h2" class="title-lg" :text="t('product.related')" />
            <RouterLink
              v-if="product.category"
              v-reveal
              :to="{ path: '/products', query: { category: product.category.slug } }"
              class="link-arrow"
            >
              {{ t('common.viewAll') }} <AppIcon name="arrow" :size="18" />
            </RouterLink>
          </div>
          <div class="grid-cards">
            <div v-for="(p, i) in product.related" :key="p.id" v-reveal="i * 100">
              <ProductCard :product="p" />
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.crumbs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 14px;
  color: var(--c-on-dark-muted);
  animation: rise 0.8s var(--ease-out) both;
}

.crumbs a {
  transition: color 0.3s;
}

.crumbs a:hover,
.crumbs a:last-child {
  color: #fff;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
}

.product {
  padding-top: clamp(40px, 5vw, 72px);
}

.product__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  gap: clamp(32px, 5vw, 80px);
  align-items: start;
}

.product__gallery {
  position: sticky;
  top: 100px;
}

.product__skeleton {
  display: grid;
  gap: 18px;
  align-content: start;
}

.product__category {
  display: inline-flex;
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--c-primary);
  background: color-mix(in srgb, var(--c-primary) 9%, transparent);
  margin-bottom: 20px;
  transition:
    background 0.3s,
    color 0.3s;
}

.product__category:hover {
  background: var(--c-primary);
  color: #fff;
}

.product__name {
  word-break: break-word;
}

.product__short {
  margin-top: 22px;
}

.product__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 36px 0;
}

.product__back {
  color: var(--c-ink);
}

.product__ask {
  display: flex;
  gap: 18px;
  padding: 24px;
  border-radius: var(--radius-lg);
  background: var(--c-bg-soft);
  border: 1px solid var(--c-line);
}

.product__ask p {
  color: var(--c-muted);
  margin: 6px 0 10px;
  font-size: 15px;
}

.product__ask-icon {
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: var(--c-gradient);
  color: #fff;
}

.product__desc {
  margin-top: clamp(56px, 8vw, 110px);
  max-width: 860px;
  padding-top: clamp(40px, 5vw, 64px);
  border-top: 1px solid var(--c-line);
}

.product__desc .prose {
  margin-top: 20px;
}

@media (max-width: 900px) {
  .product__grid {
    grid-template-columns: 1fr;
  }

  .product__gallery {
    position: static;
  }
}
</style>
