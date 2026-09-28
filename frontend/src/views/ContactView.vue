<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { getProduct, sendContactMessage } from '@/api/site'
import AppIcon from '@/components/AppIcon.vue'
import PageHero from '@/components/PageHero.vue'
import { useSiteStore } from '@/stores/site'

const { t } = useI18n()
const route = useRoute()
const site = useSiteStore()

const form = reactive({ name: '', email: '', phone: '', message: '', website: '' })
const errors = ref([])
const sending = ref(false)
const sent = ref(false)

// Backend error code -> field it belongs to (the rest are shown above the button).
const FIELD_ERRORS = {
  name: ['contact-name-invalid'],
  email: ['contact-email-invalid', 'contact-email-or-phone-required'],
  phone: ['contact-phone-invalid', 'contact-email-or-phone-required'],
  message: ['contact-message-invalid'],
}
const FIELD_CODES = new Set(Object.values(FIELD_ERRORS).flat())

const fieldError = (field) => {
  const code = errors.value.find((c) => FIELD_ERRORS[field].includes(c))
  return code ? t(`contact.errors.${code}`) : ''
}
const generalErrors = computed(() =>
  errors.value
    .filter((c) => !FIELD_CODES.has(c))
    .map((c) => (t(`contact.errors.${c}`) !== `contact.errors.${c}` ? t(`contact.errors.${c}`) : t('contact.errors.generic'))),
)

const company = computed(() => site.company || {})
const hasInfo = computed(() => Boolean(company.value.phone || company.value.email || company.value.address || hasCoords.value))
const hasCoords = computed(() => company.value.latitude != null && company.value.longitude != null)
const mapSrc = computed(() => {
  if (!hasCoords.value) return ''
  const { latitude: lat, longitude: lon } = company.value
  const d = 0.008
  return `https://www.openstreetmap.org/export/embed.html?bbox=${lon - d},${lat - d},${lon + d},${lat + d}&layer=mapnik&marker=${lat},${lon}`
})

async function submit() {
  errors.value = []
  sending.value = true
  try {
    await sendContactMessage({
      name: form.name.trim(),
      email: form.email.trim() || null,
      phone: form.phone.trim() || null,
      message: form.message.trim(),
      website: form.website,
    })
    sent.value = true
  } catch (e) {
    errors.value = e.codes?.length ? e.codes : ['generic']
  } finally {
    sending.value = false
  }
}

function reset() {
  Object.assign(form, { name: '', email: '', phone: '', message: '', website: '' })
  errors.value = []
  sent.value = false
}

onMounted(async () => {
  // "Request a quote" on a product page links here with ?product=<slug>.
  const slug = route.query.product
  if (typeof slug !== 'string' || !slug) return
  try {
    const product = await getProduct(slug)
    if (!form.message) form.message = t('product.quoteMessage', { name: product.name })
  } catch {
    // Unknown product — leave the message empty.
  }
})
</script>

<template>
  <div class="contact-page">
    <PageHero :eyebrow="t('contact.eyebrow')" :title="t('contact.title')" :subtitle="t('contact.subtitle')" />

    <section class="section contact">
      <div class="container contact__grid" :class="{ 'contact__grid--single': !hasInfo }">
        <!-- Form -->
        <div v-reveal:up class="contact__card">
          <Transition name="swap" mode="out-in">
            <div v-if="sent" key="done" class="success">
              <svg class="success__check" viewBox="0 0 80 80" aria-hidden="true">
                <circle cx="40" cy="40" r="36" />
                <path d="M24 41l11 11 21-23" />
              </svg>
              <h2 class="title-md">{{ t('contact.successTitle') }}</h2>
              <p>{{ t('contact.successText') }}</p>
              <button type="button" class="btn" @click="reset">{{ t('contact.sendAnother') }}</button>
            </div>

            <form v-else key="form" class="form" novalidate @submit.prevent="submit">
              <div class="field" :class="{ 'has-error': fieldError('name') }">
                <input id="c-name" v-model="form.name" type="text" autocomplete="name" maxlength="150" placeholder=" " />
                <label for="c-name">{{ t('contact.name') }} *</label>
                <span class="field__line" />
                <Transition name="err"><small v-if="fieldError('name')">{{ fieldError('name') }}</small></Transition>
              </div>

              <div class="form__row">
                <div class="field" :class="{ 'has-error': fieldError('email') }">
                  <input id="c-email" v-model="form.email" type="email" autocomplete="email" maxlength="255" placeholder=" " />
                  <label for="c-email">{{ t('contact.email') }}</label>
                  <span class="field__line" />
                  <Transition name="err"><small v-if="fieldError('email')">{{ fieldError('email') }}</small></Transition>
                </div>
                <div class="field" :class="{ 'has-error': fieldError('phone') }">
                  <input id="c-phone" v-model="form.phone" type="tel" autocomplete="tel" maxlength="50" placeholder=" " />
                  <label for="c-phone">{{ t('contact.phone') }}</label>
                  <span class="field__line" />
                  <Transition name="err">
                    <small v-if="fieldError('phone') && !fieldError('email')">{{ fieldError('phone') }}</small>
                  </Transition>
                </div>
              </div>
              <p class="form__hint">{{ t('contact.hint') }}</p>

              <div class="field field--area" :class="{ 'has-error': fieldError('message') }">
                <textarea id="c-message" v-model="form.message" rows="5" maxlength="5000" placeholder=" " />
                <label for="c-message">{{ t('contact.message') }} *</label>
                <span class="field__line" />
                <span class="field__counter">{{ form.message.length }} / 5000</span>
                <Transition name="err"><small v-if="fieldError('message')">{{ fieldError('message') }}</small></Transition>
              </div>

              <!-- Honeypot: hidden from people, bots fill it in. -->
              <div class="hp" aria-hidden="true">
                <label for="c-website">Website</label>
                <input id="c-website" v-model="form.website" type="text" tabindex="-1" autocomplete="off" />
              </div>

              <Transition name="err">
                <p v-if="generalErrors.length" class="form__error" role="alert">{{ generalErrors.join(' ') }}</p>
              </Transition>

              <button v-magnetic="0.2" type="submit" class="btn form__submit" :disabled="sending">
                <span v-if="sending" class="spinner" />
                {{ sending ? t('contact.sending') : t('contact.send') }}
                <AppIcon v-if="!sending" name="arrow" class="arrow" />
              </button>
            </form>
          </Transition>
        </div>

        <!-- Info -->
        <aside v-if="hasInfo" class="contact__info">
          <h2 v-reveal class="title-md">{{ t('contact.infoTitle') }}</h2>
          <a v-if="company.phone" v-reveal="100" :href="`tel:${company.phone}`" class="info-card">
            <span class="info-card__icon"><AppIcon name="phone" :size="22" /></span>
            <span><small>{{ t('contact.phone') }}</small>{{ company.phone }}</span>
          </a>
          <a v-if="company.email" v-reveal="200" :href="`mailto:${company.email}`" class="info-card">
            <span class="info-card__icon"><AppIcon name="mail" :size="22" /></span>
            <span><small>{{ t('contact.email') }}</small>{{ company.email }}</span>
          </a>
          <div v-if="company.address" v-reveal="300" class="info-card">
            <span class="info-card__icon"><AppIcon name="pin" :size="22" /></span>
            <span><small>{{ t('contact.address') }}</small>{{ company.address }}</span>
          </div>
          <div v-if="hasCoords" v-reveal:clip="350" class="map">
            <iframe :src="mapSrc" :title="t('contact.map')" loading="lazy" referrerpolicy="no-referrer" />
          </div>
        </aside>
      </div>
    </section>
  </div>
</template>

<style scoped>
.contact {
  padding-top: 0;
}

.contact__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
  gap: clamp(28px, 4vw, 64px);
  align-items: start;
  margin-top: clamp(-80px, -6vw, -40px);
  position: relative;
  z-index: 2;
}

.contact__grid--single {
  grid-template-columns: minmax(0, 820px);
}

.contact__card {
  background: #fff;
  border-radius: calc(var(--radius-lg) + 4px);
  box-shadow: var(--shadow-lg);
  padding: clamp(24px, 4vw, 52px);
}

.form {
  display: grid;
  gap: 22px;
}

.form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
}

.form__hint {
  margin-top: -10px;
  font-size: 13px;
  color: var(--c-muted);
}

/* Floating-label fields */
.field {
  position: relative;
}

.field input,
.field textarea {
  width: 100%;
  border: 0;
  outline: 0;
  font: inherit;
  font-size: 16px;
  font-weight: 600;
  color: var(--c-text);
  background: var(--c-bg-soft);
  border-radius: 14px 14px 4px 4px;
  padding: 26px 18px 10px;
  transition: background 0.3s;
}

.field textarea {
  resize: vertical;
  min-height: 150px;
  padding-bottom: 28px;
}

.field input:focus,
.field textarea:focus {
  background: #eef1fa;
}

.field label {
  position: absolute;
  left: 18px;
  top: 18px;
  font-weight: 600;
  color: var(--c-muted);
  pointer-events: none;
  transform-origin: left top;
  transition:
    transform 0.35s var(--ease-out),
    color 0.3s;
}

.field input:focus + label,
.field input:not(:placeholder-shown) + label,
.field textarea:focus + label,
.field textarea:not(:placeholder-shown) + label {
  transform: translateY(-11px) scale(0.76);
  color: var(--c-primary);
}

.field__line {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  bottom: 0;
  background: var(--c-line);
  overflow: hidden;
}

.field--area .field__line {
  bottom: 6px;
}

.field__line::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--c-gradient);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.6s var(--ease-out);
}

.field:focus-within .field__line::after {
  transform: scaleX(1);
}

.field.has-error .field__line {
  background: var(--c-danger);
}

.field.has-error label {
  color: var(--c-danger) !important;
}

.field.has-error {
  animation: shake 0.45s;
}

.field small {
  display: block;
  margin-top: 8px;
  color: var(--c-danger);
  font-weight: 600;
  font-size: 13px;
}

.field__counter {
  position: absolute;
  right: 14px;
  bottom: 16px;
  font-size: 12px;
  color: var(--c-muted);
}

.hp {
  position: absolute;
  left: -9999px;
  width: 1px;
  height: 1px;
  overflow: hidden;
}

.form__error {
  padding: 14px 18px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--c-danger) 10%, transparent);
  color: var(--c-danger);
  font-weight: 600;
}

.form__submit {
  justify-self: start;
  height: 58px;
  padding: 0 34px;
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

@keyframes shake {
  20%,
  60% {
    transform: translateX(-6px);
  }
  40%,
  80% {
    transform: translateX(6px);
  }
}

/* Success */
.success {
  text-align: center;
  padding: 32px 0;
  display: grid;
  justify-items: center;
  gap: 16px;
}

.success p {
  color: var(--c-muted);
  max-width: 380px;
}

.success .btn {
  margin-top: 12px;
}

.success__check {
  width: 110px;
  height: 110px;
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.success__check circle {
  stroke: var(--c-success);
  stroke-dasharray: 230;
  stroke-dashoffset: 230;
  animation: draw 0.9s var(--ease-out) forwards;
  transform-origin: center;
}

.success__check path {
  stroke: var(--c-success);
  stroke-dasharray: 60;
  stroke-dashoffset: 60;
  animation: draw 0.6s 0.6s var(--ease-out) forwards;
}

@keyframes draw {
  to {
    stroke-dashoffset: 0;
  }
}

.swap-enter-active,
.swap-leave-active {
  transition:
    opacity 0.4s,
    transform 0.5s var(--ease-out);
}

.swap-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.swap-leave-to {
  opacity: 0;
  transform: translateY(-16px);
}

.err-enter-active,
.err-leave-active {
  transition:
    opacity 0.3s,
    transform 0.3s;
}

.err-enter-from,
.err-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* Info */
.contact__info {
  display: grid;
  gap: 16px;
  padding-top: clamp(40px, 6vw, 96px);
}

.contact__info h2 {
  margin-bottom: 8px;
}

.info-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  border-radius: var(--radius);
  background: var(--c-bg-soft);
  border: 1px solid var(--c-line);
  font-weight: 700;
  word-break: break-word;
  transition:
    transform 0.5s var(--ease-out),
    box-shadow 0.5s,
    background 0.3s;
}

a.info-card:hover {
  transform: translateX(8px);
  background: #fff;
  box-shadow: var(--shadow);
}

.info-card small {
  display: block;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--c-muted);
  margin-bottom: 2px;
}

.info-card__icon {
  width: 50px;
  height: 50px;
  flex-shrink: 0;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--c-gradient);
  color: #fff;
}

.map {
  border-radius: var(--radius-lg);
  overflow: hidden;
  aspect-ratio: 4 / 3;
  border: 1px solid var(--c-line);
}

.map iframe {
  width: 100%;
  height: 100%;
  border: 0;
  filter: grayscale(0.3) contrast(1.05);
}

@media (max-width: 900px) {
  .contact__grid {
    grid-template-columns: 1fr;
  }

  .contact__info {
    padding-top: 0;
  }
}

@media (max-width: 560px) {
  .form__row {
    grid-template-columns: 1fr;
  }

  .form__submit {
    justify-self: stretch;
  }
}
</style>
