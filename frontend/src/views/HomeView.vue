<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { getBanners, getProducts, getSlider } from '@/api/site'
import AnimatedTitle from '@/components/AnimatedTitle.vue'
import AppIcon from '@/components/AppIcon.vue'
import BannerShowcase from '@/components/BannerShowcase.vue'
import CtaSection from '@/components/CtaSection.vue'
import HeroSlider from '@/components/HeroSlider.vue'
import MediaImg from '@/components/MediaImg.vue'
import ProductCard from '@/components/ProductCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import TextMarquee from '@/components/TextMarquee.vue'
import { useSiteStore } from '@/stores/site'

const PRODUCTS_ON_HOME = 8
const FEATURES = [
  { key: 'precision', icon: 'precision' },
  { key: 'quality', icon: 'quality' },
  { key: 'delivery', icon: 'truck' },
  { key: 'support', icon: 'support' },
]

const { t } = useI18n()
const site = useSiteStore()

const slides = ref([])
const banners = ref([])
const products = ref([])
const productsAreFeatured = ref(true)
const productsLoading = ref(true)

const categoriesWithProducts = computed(() => site.categories.filter((c) => c['products-count'] > 0))
const aboutText = computed(() => site.company?.description || t('home.aboutFallback'))
const aboutImage = computed(() => site.company?.cover || site.company?.gallery?.[0]?.media || null)

async function loadProducts() {
  productsLoading.value = true
  try {
    const featured = await getProducts({ featured: 1, 'per-page': PRODUCTS_ON_HOME })
    if (featured.items.length) {
      products.value = featured.items
    } else {
      // No featured products yet — show the first ones from the catalog.
      productsAreFeatured.value = false
      products.value = (await getProducts({ 'per-page': PRODUCTS_ON_HOME })).items
    }
  } catch {
    products.value = []
  } finally {
    productsLoading.value = false
  }
}

onMounted(() => {
  getSlider().then((v) => (slides.value = v)).catch(() => {})
  getBanners().then((v) => (banners.value = v)).catch(() => {})
  loadProducts()
})
</script>

<template>
  <div class="home">
    <HeroSlider :slides="slides" :company-name="site.companyName" />

    <!-- Intro + real numbers -->
    <section class="section intro">
      <div class="container intro__grid">
        <div>
          <p v-reveal class="eyebrow">{{ t('home.aboutEyebrow') }}</p>
          <AnimatedTitle tag="h2" class="title-lg" :text="site.companyName" />
          <p v-reveal="150" class="lead intro__text">{{ aboutText }}</p>
          <RouterLink v-reveal="250" to="/about" class="link-arrow intro__link">
            {{ t('common.learnMore') }} <AppIcon name="arrow" :size="18" />
          </RouterLink>
        </div>
        <div class="intro__stats">
          <div v-reveal:zoom class="stat">
            <span class="stat__num"><span v-count-up="site.productsTotal" />+</span>
            <span class="stat__label">{{ t('home.statProducts') }}</span>
          </div>
          <div v-reveal:zoom="120" class="stat stat--accent">
            <span class="stat__num"><span v-count-up="site.categories.length" /></span>
            <span class="stat__label">{{ t('home.statCategories') }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Running category names -->
    <TextMarquee v-if="categoriesWithProducts.length" class="home__marquee" :items="categoriesWithProducts.map((c) => c.name)" />

    <!-- Features -->
    <section class="section section--dark features">
      <div class="features__glow" />
      <div class="container">
        <div class="section-head">
          <div>
            <p v-reveal class="eyebrow">{{ t('home.featuresEyebrow') }}</p>
            <AnimatedTitle tag="h2" class="title-lg" :text="t('home.featuresTitle')" />
          </div>
        </div>
        <div class="features__grid">
          <article v-for="(f, i) in FEATURES" :key="f.key" v-reveal="i * 110" class="feature">
            <span class="feature__num">0{{ i + 1 }}</span>
            <span class="feature__icon"><AppIcon :name="f.icon" :size="28" /></span>
            <h3 class="feature__title">{{ t(`home.features.${f.key}.title`) }}</h3>
            <p class="feature__text">{{ t(`home.features.${f.key}.text`) }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- Categories -->
    <section v-if="site.categories.length" class="section">
      <div class="container">
        <div class="section-head">
          <div>
            <p v-reveal class="eyebrow">{{ t('home.categoriesEyebrow') }}</p>
            <AnimatedTitle tag="h2" class="title-lg" :text="t('home.categoriesTitle')" />
          </div>
          <RouterLink v-reveal to="/products" class="link-arrow">{{ t('common.viewAll') }} <AppIcon name="arrow" :size="18" /></RouterLink>
        </div>
        <div class="cats">
          <RouterLink
            v-for="(c, i) in site.categories"
            :key="c.id"
            v-reveal="(i % 4) * 90"
            :to="{ path: '/products', query: { category: c.slug } }"
            class="cat"
          >
            <span class="cat__index">{{ String(i + 1).padStart(2, '0') }}</span>
            <h3 class="cat__name">{{ c.name }}</h3>
            <p v-if="c.description" class="cat__desc">{{ c.description }}</p>
            <span class="cat__foot">
              <span>{{ t('catalog.productsCount', c['products-count']) }}</span>
              <span class="cat__arrow"><AppIcon name="arrow" :size="18" /></span>
            </span>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Featured / latest products -->
    <section v-if="productsLoading || products.length" class="section section--soft">
      <div class="container">
        <div class="section-head">
          <div>
            <p v-reveal class="eyebrow">{{ productsAreFeatured ? t('home.featuredEyebrow') : t('home.categoriesEyebrow') }}</p>
            <AnimatedTitle tag="h2" class="title-lg" :text="productsAreFeatured ? t('home.featuredTitle') : t('home.latestTitle')" />
          </div>
          <RouterLink v-reveal to="/products" class="link-arrow">{{ t('common.viewAll') }} <AppIcon name="arrow" :size="18" /></RouterLink>
        </div>
        <div class="grid-cards">
          <template v-if="productsLoading">
            <SkeletonCard v-for="n in 4" :key="n" />
          </template>
          <template v-else>
            <div v-for="(p, i) in products" :key="p.id" v-reveal="(i % 4) * 100">
              <ProductCard :product="p" />
            </div>
          </template>
        </div>
      </div>
    </section>

    <!-- Promo banners -->
    <section v-if="banners.length" class="section">
      <div class="container">
        <BannerShowcase :banners="banners" />
      </div>
    </section>

    <!-- About preview -->
    <section v-if="aboutImage" class="section about-preview" :class="{ 'section--soft': !banners.length }">
      <div class="container about-preview__grid">
        <div v-reveal:clip class="about-preview__media">
          <MediaImg v-parallax="0.12" :media="aboutImage" :alt="site.companyName" />
        </div>
        <div>
          <p v-reveal class="eyebrow">{{ t('home.aboutEyebrow') }}</p>
          <AnimatedTitle tag="h2" class="title-lg" :text="t('about.title')" />
          <p v-reveal="150" class="prose about-preview__text">{{ aboutText }}</p>
          <RouterLink v-reveal="250" v-magnetic to="/about" class="btn">
            {{ t('common.learnMore') }} <AppIcon name="arrow" class="arrow" />
          </RouterLink>
        </div>
      </div>
    </section>

    <CtaSection :class="{ 'cta-gap': !aboutImage }" />
  </div>
</template>

<style scoped>
/* Intro */
.intro__grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: clamp(32px, 6vw, 96px);
  align-items: center;
}

.intro__text {
  margin-top: 24px;
  white-space: pre-line;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.intro__link {
  margin-top: 28px;
}

.intro__stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.stat {
  padding: clamp(24px, 3vw, 40px);
  border-radius: var(--radius-lg);
  background: var(--c-bg-soft);
  display: grid;
  gap: 6px;
}

.stat--accent {
  background: var(--c-gradient);
  color: #fff;
  margin-top: 40px;
}

.stat__num {
  font-family: var(--f-display);
  font-weight: 800;
  font-size: clamp(40px, 5vw, 72px);
  line-height: 1;
}

.stat__label {
  font-weight: 600;
  opacity: 0.75;
}

.home__marquee {
  padding-bottom: clamp(40px, 6vw, 80px);
}

/* Features */
.features {
  overflow: hidden;
  isolation: isolate;
}

.features__glow {
  position: absolute;
  right: -20%;
  top: -30%;
  width: 70vw;
  height: 70vw;
  background: radial-gradient(circle, rgba(67, 97, 238, 0.3), transparent 60%);
  z-index: -1;
}

.features__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.feature {
  position: relative;
  padding: 34px 28px;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
  transition:
    background 0.5s,
    border-color 0.5s,
    translate 0.6s var(--ease-out);
}

.feature::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--c-gradient);
  opacity: 0;
  transition: opacity 0.6s var(--ease-out);
  z-index: -1;
}

.feature:hover {
  translate: 0 -8px;
  border-color: transparent;
}

.feature:hover::before {
  opacity: 1;
}

.feature__num {
  position: absolute;
  right: 22px;
  top: 18px;
  font-family: var(--f-display);
  font-size: 40px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.06);
  transition: color 0.5s;
}

.feature:hover .feature__num {
  color: rgba(255, 255, 255, 0.25);
}

.feature__icon {
  width: 60px;
  height: 60px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: rgba(76, 201, 240, 0.12);
  color: var(--c-accent);
  margin-bottom: 26px;
  transition:
    background 0.5s,
    color 0.5s,
    transform 0.6s var(--ease-out);
}

.feature:hover .feature__icon {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  transform: rotate(-10deg) scale(1.08);
}

.feature__title {
  font-size: 19px;
  margin-bottom: 12px;
  color: #fff;
}

.feature__text {
  color: var(--c-on-dark-muted);
  font-size: 15px;
  transition: color 0.5s;
}

.feature:hover .feature__text {
  color: rgba(255, 255, 255, 0.9);
}

/* Categories */
.cats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr));
  gap: 18px;
}

.cat {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 230px;
  padding: 28px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--c-line);
  background: #fff;
  overflow: hidden;
  isolation: isolate;
  transition:
    color 0.5s,
    border-color 0.5s,
    box-shadow 0.5s;
}

.cat::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--c-ink);
  clip-path: circle(0% at 100% 100%);
  transition: clip-path 0.8s var(--ease-in-out);
  z-index: -1;
}

.cat:hover {
  color: #fff;
  border-color: transparent;
  box-shadow: var(--shadow-lg);
}

.cat:hover::before {
  clip-path: circle(150% at 100% 100%);
}

.cat__index {
  font-family: var(--f-display);
  font-weight: 700;
  font-size: 14px;
  color: var(--c-primary);
}

.cat:hover .cat__index {
  color: var(--c-accent);
}

.cat__name {
  font-size: 22px;
}

.cat__desc {
  font-size: 14px;
  color: var(--c-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.5s;
}

.cat:hover .cat__desc {
  color: var(--c-on-dark-muted);
}

.cat__foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
  font-size: 14px;
}

.cat__arrow {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--c-bg-soft);
  color: var(--c-ink);
  transition:
    transform 0.6s var(--ease-out),
    background 0.4s,
    color 0.4s;
}

.cat:hover .cat__arrow {
  background: var(--c-gradient);
  color: #fff;
  transform: rotate(-45deg);
}

/* About preview */
.about-preview__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(32px, 6vw, 96px);
  align-items: center;
}

.about-preview__media {
  border-radius: var(--radius-lg);
  overflow: hidden;
  aspect-ratio: 4 / 4.4;
}

.about-preview__media :deep(.media-img) {
  width: 100%;
  height: 120%;
  margin-top: -10%;
}

.about-preview__text {
  margin: 24px 0 36px;
  display: -webkit-box;
  -webkit-line-clamp: 7;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cta-gap {
  padding-top: clamp(72px, 10vw, 140px);
}

@media (max-width: 1000px) {
  .features__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .intro__grid,
  .about-preview__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 520px) {
  .features__grid {
    grid-template-columns: 1fr;
  }

  .intro__stats {
    grid-template-columns: 1fr;
  }

  .stat--accent {
    margin-top: 0;
  }
}
</style>
