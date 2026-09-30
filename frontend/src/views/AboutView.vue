<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import AnimatedTitle from '@/components/AnimatedTitle.vue'
import AppIcon from '@/components/AppIcon.vue'
import CtaSection from '@/components/CtaSection.vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import MediaImg from '@/components/MediaImg.vue'
import PageHero from '@/components/PageHero.vue'
import { useSiteStore } from '@/stores/site'

const VALUES = [
  { key: 'quality', icon: 'quality' },
  { key: 'innovation', icon: 'innovation' },
  { key: 'partnership', icon: 'partnership' },
]

const { t } = useI18n()
const site = useSiteStore()
const lightbox = ref(null)

const company = computed(() => site.company || {})
const gallery = computed(() => (company.value.gallery || []).filter((g) => g.media))
const lightboxImages = computed(() => gallery.value.map((g) => ({ ...g.media, caption: g.caption })))
const storyImage = computed(() => gallery.value[0]?.media || company.value.cover || null)
const description = computed(() => company.value.description || t('home.aboutFallback'))
</script>

<template>
  <div class="about-page">
    <PageHero :eyebrow="t('about.eyebrow')" :title="site.companyName" :image="company.cover" />

    <!-- Story -->
    <section class="section">
      <div class="container story">
        <div class="story__text">
          <p v-reveal class="eyebrow">{{ t('about.story') }}</p>
          <AnimatedTitle tag="h2" class="title-lg" :text="t('about.title')" />
          <p v-reveal="150" class="prose story__prose">{{ description }}</p>
          <div v-if="site.categories.length" v-reveal="250" class="story__stats">
            <div>
              <strong v-count-up="site.productsTotal" />
              <span>{{ t('home.statProducts') }}</span>
            </div>
            <div>
              <strong v-count-up="site.categories.length" />
              <span>{{ t('home.statCategories') }}</span>
            </div>
          </div>
        </div>
        <div v-if="storyImage" class="story__visual">
          <div v-reveal:clip class="story__img">
            <MediaImg v-parallax="0.1" :media="storyImage" :alt="site.companyName" />
          </div>
          <div v-if="company.logo" v-reveal:zoom="400" class="story__logo">
            <img :src="company.logo.url" :alt="site.companyName" />
          </div>
        </div>
      </div>
    </section>

    <!-- Brand & quality -->
    <section class="section section--soft">
      <div class="container brand">
        <div>
          <p v-reveal class="eyebrow">{{ t('brand.eyebrow') }}</p>
          <AnimatedTitle tag="h2" class="title-lg" :text="t('brand.title')" />
        </div>
        <div class="brand__body">
          <p v-reveal="100" class="prose">{{ t('brand.p1') }}</p>
          <p v-reveal="200" class="prose">{{ t('brand.p2') }}</p>
          <p v-reveal="300" class="brand__cta">{{ t('brand.cta') }}</p>
          <p v-reveal="400" class="brand__slogan text-gradient">{{ t('brand.slogan') }}</p>
        </div>
      </div>
    </section>

    <!-- Values -->
    <section class="section section--dark values">
      <div class="values__glow" />
      <div class="container">
        <div class="section-head">
          <AnimatedTitle tag="h2" class="title-lg" :text="t('about.valuesTitle')" />
        </div>
        <div class="values__grid">
          <article v-for="(v, i) in VALUES" :key="v.key" v-reveal="i * 130" class="value">
            <span class="value__icon"><AppIcon :name="v.icon" :size="30" /></span>
            <h3>{{ t(`about.values.${v.key}.title`) }}</h3>
            <p>{{ t(`about.values.${v.key}.text`) }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- Gallery -->
    <section v-if="gallery.length" class="section">
      <div class="container">
        <div class="section-head">
          <AnimatedTitle tag="h2" class="title-lg" :text="t('about.gallery')" />
        </div>
        <div class="masonry">
          <button
            v-for="(g, i) in gallery"
            :key="g.id"
            v-reveal:zoom="(i % 3) * 110"
            type="button"
            class="masonry__item"
            @click="lightbox = i"
          >
            <MediaImg :media="g.media" :alt="g.caption || site.companyName" />
            <span class="masonry__overlay">
              <AppIcon name="zoom" :size="26" />
              <span v-if="g.caption">{{ g.caption }}</span>
            </span>
          </button>
        </div>
        <ImageLightbox v-model:index="lightbox" :images="lightboxImages" />
      </div>
    </section>

    <!-- Contacts strip -->
    <section v-if="company.phone || company.email || company.address" class="section section--soft">
      <div class="container">
        <div class="section-head">
          <AnimatedTitle tag="h2" class="title-lg" :text="t('about.contactsTitle')" />
        </div>
        <div class="contacts">
          <a v-if="company.phone" v-reveal :href="`tel:${company.phone}`" class="contact-tile">
            <AppIcon name="phone" :size="26" /><small>{{ t('contact.phone') }}</small>{{ company.phone }}
          </a>
          <a v-if="company.email" v-reveal="100" :href="`mailto:${company.email}`" class="contact-tile">
            <AppIcon name="mail" :size="26" /><small>{{ t('contact.email') }}</small>{{ company.email }}
          </a>
          <RouterLink v-if="company.address" v-reveal="200" to="/contact" class="contact-tile">
            <AppIcon name="pin" :size="26" /><small>{{ t('contact.address') }}</small>{{ company.address }}
          </RouterLink>
        </div>
      </div>
    </section>

    <CtaSection class="about-cta" />
  </div>
</template>

<style scoped>
.story {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(32px, 6vw, 100px);
  align-items: center;
}

.story__prose {
  margin-top: 24px;
}

.story__stats {
  display: flex;
  gap: 48px;
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid var(--c-line);
}

.story__stats div {
  display: grid;
}

.story__stats strong {
  font-family: var(--f-display);
  font-size: clamp(36px, 4vw, 56px);
  line-height: 1.1;
  background: var(--c-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.story__stats span {
  color: var(--c-muted);
  font-weight: 600;
}

.story__visual {
  position: relative;
}

.story__img {
  border-radius: var(--radius-lg);
  overflow: hidden;
  aspect-ratio: 4 / 5;
}

.story__img :deep(.media-img) {
  width: 100%;
  height: 120%;
  margin-top: -10%;
}

.story__logo {
  position: absolute;
  left: -32px;
  bottom: -32px;
  width: 132px;
  height: 132px;
  border-radius: 28px;
  background: #fff;
  box-shadow: var(--shadow-lg);
  padding: 20px;
  display: grid;
  place-items: center;
}

.story__logo img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* Brand & quality */
.brand {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: clamp(32px, 6vw, 100px);
  align-items: start;
}

.brand__body {
  display: grid;
  gap: 20px;
}

.brand__cta {
  margin-top: 12px;
  padding-top: 28px;
  border-top: 1px solid var(--c-line);
  font-size: clamp(18px, 1.6vw, 22px);
  font-weight: 700;
}

.brand__slogan {
  font-family: var(--f-display);
  font-size: clamp(20px, 2vw, 28px);
  line-height: 1.3;
}

/* Values */
.values {
  overflow: hidden;
  isolation: isolate;
}

.values__glow {
  position: absolute;
  left: -20%;
  bottom: -40%;
  width: 70vw;
  height: 70vw;
  background: radial-gradient(circle, rgba(76, 201, 240, 0.22), transparent 60%);
  z-index: -1;
}

.values__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.value {
  padding: 40px 32px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.01));
  transition:
    translate 0.6s var(--ease-out),
    border-color 0.5s;
}

.value:hover {
  translate: 0 -10px;
  border-color: rgba(76, 201, 240, 0.5);
}

.value__icon {
  width: 68px;
  height: 68px;
  border-radius: 20px;
  display: grid;
  place-items: center;
  background: var(--c-gradient);
  color: #fff;
  margin-bottom: 28px;
  box-shadow: 0 14px 34px rgba(67, 97, 238, 0.4);
  transition: transform 0.7s var(--ease-out);
}

.value:hover .value__icon {
  transform: rotate(360deg);
}

.value h3 {
  font-size: 22px;
  color: #fff;
  margin-bottom: 12px;
}

.value p {
  color: var(--c-on-dark-muted);
}

/* Gallery */
.masonry {
  columns: 3 280px;
  column-gap: 18px;
}

.masonry__item {
  position: relative;
  display: block;
  width: 100%;
  margin-bottom: 18px;
  border-radius: var(--radius);
  overflow: hidden;
  break-inside: avoid;
  cursor: zoom-in;
}

.masonry__item :deep(img) {
  height: auto;
  transition:
    transform 1.2s var(--ease-out),
    opacity 0.9s,
    filter 0.9s !important;
}

.masonry__item:hover :deep(img) {
  transform: scale(1.07);
}

.masonry__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  color: #fff;
  font-weight: 700;
  text-align: center;
  background: linear-gradient(0deg, rgba(11, 16, 32, 0.75), rgba(67, 97, 238, 0.35));
  opacity: 0;
  transition: opacity 0.5s;
}

.masonry__item:hover .masonry__overlay {
  opacity: 1;
}

/* Contacts */
.contacts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr));
  gap: 18px;
}

.contact-tile {
  display: grid;
  gap: 6px;
  padding: 32px;
  border-radius: var(--radius-lg);
  background: #fff;
  border: 1px solid var(--c-line);
  font-weight: 700;
  font-size: 18px;
  word-break: break-word;
  transition:
    translate 0.5s var(--ease-out),
    box-shadow 0.5s;
}

.contact-tile svg {
  color: var(--c-primary);
  margin-bottom: 14px;
}

.contact-tile small {
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--c-muted);
}

.contact-tile:hover {
  translate: 0 -6px;
  box-shadow: var(--shadow-lg);
}

.about-cta {
  padding-top: clamp(72px, 10vw, 140px);
}

@media (max-width: 900px) {
  .story,
  .brand {
    grid-template-columns: 1fr;
  }

  .values__grid {
    grid-template-columns: 1fr;
  }

  .story__logo {
    left: 16px;
    bottom: -24px;
    width: 104px;
    height: 104px;
  }
}
</style>
