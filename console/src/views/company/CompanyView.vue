<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { OfficeBuilding, Location } from '@element-plus/icons-vue'

import { getCompany, createCompany, updateCompany } from '@/api/company'
import { useAuthStore } from '@/stores/auth'
import { useBrandStore } from '@/stores/brand'
import MediaUploader from '@/components/MediaUploader.vue'
import CompanyGallery from './CompanyGallery.vue'

const { t } = useI18n()
const authStore = useAuthStore()
const brand = useBrandStore()

// Mirrors backend view/company.py.
const PHONE_RE = /^\+?[0-9][0-9\s()-]{3,48}$/

const loading = ref(false)
const loadError = ref(false)
const saving = ref(false)
// false until the company row exists; then the page only edits it.
const exists = ref(false)
// Create mode shows an empty state first instead of a blank form.
const creating = ref(false)

const formRef = ref()
const form = reactive({
  companyName: '',
  email: '',
  phone: '',
  address: '',
  latitude: null,
  longitude: null,
  description: '',
  logo: null,
  cover: null,
})

const canSave = computed(() => authStore.can(exists.value ? 'company.edit' : 'company.create'))
const readOnly = computed(() => !canSave.value)
const showForm = computed(() => exists.value || creating.value)

const hasCoordinates = computed(() => form.latitude !== null && form.longitude !== null)
const mapEmbedUrl = computed(() =>
  hasCoordinates.value ? `https://maps.google.com/maps?q=${form.latitude},${form.longitude}&z=16&output=embed` : '',
)
const mapLinkUrl = computed(() =>
  hasCoordinates.value ? `https://www.google.com/maps?q=${form.latitude},${form.longitude}` : '',
)

const rules = computed(() => ({
  companyName: [
    { required: true, message: t('company.nameRequired'), trigger: 'blur' },
    { max: 200, message: t('errors.company-name-invalid'), trigger: 'blur' },
  ],
  email: [{ type: 'email', message: t('errors.company-email-invalid'), trigger: 'blur' }],
  phone: [{ pattern: PHONE_RE, message: t('errors.company-phone-invalid'), trigger: 'blur' }],
  longitude: [
    {
      validator: (_rule, _value, callback) =>
        (form.latitude === null) !== (form.longitude === null)
          ? callback(new Error(t('errors.company-coordinates-invalid')))
          : callback(),
      trigger: 'change',
    },
  ],
}))

function fill(company) {
  Object.assign(form, {
    companyName: company?.['company-name'] ?? '',
    email: company?.email ?? '',
    phone: company?.phone ?? '',
    address: company?.address ?? '',
    latitude: company?.latitude ?? null,
    longitude: company?.longitude ?? null,
    description: company?.description ?? '',
    logo: company?.logo ?? null,
    cover: company?.cover ?? null,
  })
  formRef.value?.clearValidate()
}

async function load() {
  loading.value = true
  loadError.value = false
  try {
    const { data } = await getCompany()
    if (data.status === 'SUCCESS') {
      exists.value = !!data.result
      fill(data.result ?? null)
    } else {
      loadError.value = true
    }
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

// Google Maps copies coordinates as "37.960123, 58.326100" — pasting that
// into either field fills both.
function onCoordinatesPaste(event) {
  const text = event.clipboardData?.getData('text') || ''
  const match = text.match(/^\s*(-?\d+(?:\.\d+)?)\s*[,;\s]\s*(-?\d+(?:\.\d+)?)\s*$/)
  if (!match) return
  event.preventDefault()
  form.latitude = Number(match[1])
  form.longitude = Number(match[2])
}

async function submit() {
  if (!(await formRef.value.validate().catch(() => false))) return

  saving.value = true
  try {
    const payload = {
      'company-name': form.companyName.trim(),
      email: form.email.trim() || null,
      phone: form.phone.trim() || null,
      address: form.address.trim() || null,
      latitude: form.latitude,
      longitude: form.longitude,
      description: form.description.trim() || null,
      'logo-media-id': form.logo?.id ?? null,
      'cover-media-id': form.cover?.id ?? null,
    }
    const wasCreate = !exists.value
    const { data } = wasCreate ? await createCompany(payload) : await updateCompany(payload)

    if (data.status === 'SUCCESS') {
      ElMessage.success(t(wasCreate ? 'company.created' : 'company.updated'))
      exists.value = true
      creating.value = false
      fill(data.result)
      brand.set(data.result)
    } else {
      const codes = data['error-msg'] || []
      ElMessage.error(codes.map((c) => t(`errors.${c}`, c)).join(', '))
      // Someone created it meanwhile — switch to editing their row.
      if (codes.includes('company-exists') || codes.includes('company-not-found')) load()
    }
  } catch (e) {
    // 401/403 are already surfaced by the axios interceptor.
    if (![401, 403].includes(e.response?.status)) ElMessage.error(t('errors.internal-server-error'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <section v-loading="loading" class="af-card company">
      <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

      <el-empty v-else-if="!loading && !showForm" :description="t('company.emptyText')">
        <template #image>
          <el-icon :size="64" class="company__empty-icon"><OfficeBuilding /></el-icon>
        </template>
        <el-button v-if="authStore.can('company.create')" type="primary" @click="creating = true">
          {{ t('company.create') }}
        </el-button>
      </el-empty>

      <el-form
        v-else-if="showForm"
        ref="formRef"
        :model="form"
        :rules="rules"
        :disabled="readOnly"
        label-position="top"
        class="company__form"
        @submit.prevent="submit"
      >
        <el-alert
          v-if="!exists"
          :title="t('company.createNotice')"
          type="info"
          show-icon
          :closable="false"
          class="company__notice"
        />

        <div class="company__grid">
          <div class="company__col">
            <h3 class="company__section">{{ t('company.sectionMain') }}</h3>
            <el-form-item :label="t('company.name')" prop="companyName">
              <el-input v-model="form.companyName" maxlength="200" />
            </el-form-item>
            <div class="company__row">
              <el-form-item :label="t('company.email')" prop="email">
                <el-input v-model="form.email" type="email" maxlength="255" />
              </el-form-item>
              <el-form-item :label="t('company.phone')" prop="phone">
                <el-input v-model="form.phone" maxlength="50" placeholder="+993 12 34-56-78" />
              </el-form-item>
            </div>
            <el-form-item :label="t('company.description')" prop="description">
              <el-input v-model="form.description" type="textarea" :rows="7" />
            </el-form-item>

            <h3 class="company__section">{{ t('company.sectionLocation') }}</h3>
            <el-form-item :label="t('company.address')" prop="address">
              <el-input v-model="form.address" type="textarea" :rows="2" maxlength="2000" />
            </el-form-item>
            <div class="company__row">
              <el-form-item :label="t('company.latitude')" prop="latitude">
                <el-input-number
                  v-model="form.latitude"
                  :min="-90"
                  :max="90"
                  :precision="6"
                  :step="0.0001"
                  :value-on-clear="null"
                  controls-position="right"
                  class="company__coord"
                  @paste.capture="onCoordinatesPaste"
                />
              </el-form-item>
              <el-form-item :label="t('company.longitude')" prop="longitude">
                <el-input-number
                  v-model="form.longitude"
                  :min="-180"
                  :max="180"
                  :precision="6"
                  :step="0.0001"
                  :value-on-clear="null"
                  controls-position="right"
                  class="company__coord"
                  @paste.capture="onCoordinatesPaste"
                />
              </el-form-item>
            </div>
            <div class="form-hint">{{ t('company.coordinatesHint') }}</div>
            <div v-if="hasCoordinates" class="company__map">
              <iframe :src="mapEmbedUrl" loading="lazy" referrerpolicy="no-referrer-when-downgrade" :title="t('company.map')" />
              <a :href="mapLinkUrl" target="_blank" rel="noopener" class="company__map-link">
                <el-icon><Location /></el-icon>
                {{ t('company.openInMaps') }}
              </a>
            </div>
          </div>

          <div class="company__col">
            <h3 class="company__section">{{ t('company.sectionImages') }}</h3>
            <el-form-item :label="t('company.logo')" prop="logo">
              <MediaUploader v-model="form.logo" :disabled="readOnly" />
            </el-form-item>
            <el-form-item :label="t('company.cover')" prop="cover">
              <MediaUploader v-model="form.cover" :disabled="readOnly" />
            </el-form-item>
          </div>
        </div>

        <footer v-if="canSave" class="company__footer">
          <el-button v-if="!exists" @click="creating = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" :loading="saving" @click="submit">
            {{ exists ? t('common.save') : t('company.create') }}
          </el-button>
        </footer>
      </el-form>
    </section>

    <!-- The gallery belongs to the company page, so it appears once the company exists. -->
    <CompanyGallery v-if="exists" />
  </div>
</template>

<style scoped>
.company {
  padding: 22px 24px;
  min-height: 240px;
}
.company__empty-icon {
  color: var(--el-color-primary-light-3);
}
.company__notice {
  margin-bottom: 18px;
}
.company__grid {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  gap: 32px;
}
.company__section {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 700;
}
.company__section:not(:first-child) {
  margin-top: 10px;
}
.company__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}
.company__coord {
  width: 100%;
}
.form-hint {
  margin: -8px 0 14px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--el-text-color-secondary);
}
.company__map {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.company__map iframe {
  width: 100%;
  height: 260px;
  border: 0;
  border-radius: 12px;
  background: var(--el-fill-color-light);
}
.company__map-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--el-color-primary);
  text-decoration: none;
}
.company__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}
@media (max-width: 900px) {
  .company__grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 560px) {
  .company__row {
    grid-template-columns: 1fr;
  }
}
</style>
