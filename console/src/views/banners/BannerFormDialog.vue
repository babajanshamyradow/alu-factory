<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

import { createBanner, updateBanner } from '@/api/banners'
import { lookupProducts } from '@/api/products'
import MediaUploader from '@/components/MediaUploader.vue'
import { parseUtc } from '@/utils/schedule'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // null → create mode, otherwise the banner being edited.
  banner: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const { t } = useI18n()

// Mirrors backend validation.LINK_URL_RE: absolute http(s) URL or a site path.
const LINK_URL_RE = /^(https?:\/\/\S+|\/\S*)$/

const formRef = ref()
const saving = ref(false)
const form = reactive({
  media: null,
  productId: null,
  title: '',
  subtitle: '',
  linkUrl: '',
  sortOrder: 0,
  isActive: true,
  startsAt: null,
  endsAt: null,
})

const productOptions = ref([])
const productsLoading = ref(false)

const isEdit = computed(() => !!props.banner)

const rules = computed(() => ({
  media: [{ required: true, message: t('banners.mediaRequired'), trigger: 'change' }],
  title: [{ max: 200, message: t('errors.banner-title-invalid'), trigger: 'blur' }],
  subtitle: [{ max: 300, message: t('errors.banner-subtitle-invalid'), trigger: 'blur' }],
  linkUrl: [
    { max: 500, message: t('errors.banner-link-url-invalid'), trigger: 'blur' },
    { pattern: LINK_URL_RE, message: t('errors.banner-link-url-invalid'), trigger: 'blur' },
  ],
  endsAt: [
    {
      validator: (_rule, value, callback) =>
        value && form.startsAt && value <= form.startsAt
          ? callback(new Error(t('errors.banner-dates-order-invalid')))
          : callback(),
      trigger: 'change',
    },
  ],
}))

async function searchProducts(query) {
  productsLoading.value = true
  try {
    const { data } = await lookupProducts((query || '').trim())
    if (data.status === 'SUCCESS') {
      const found = data.result || []
      // Keep the selected product visible even when the search hides it.
      const selected = productOptions.value.find((p) => p.id === form.productId)
      productOptions.value = selected && !found.some((p) => p.id === selected.id) ? [selected, ...found] : found
    }
  } catch {
    // The picker just stays empty; saving still reports real errors.
  } finally {
    productsLoading.value = false
  }
}

// Picking a product fills the texts that are still empty, so the banner
// advertises it without retyping; anything already typed is kept.
function onProductChange(productId) {
  const product = productOptions.value.find((p) => p.id === productId)
  if (!product) return
  if (!form.title.trim()) form.title = product.name
  if (!form.subtitle.trim() && product['short-description']) form.subtitle = product['short-description']
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, {
      media: props.banner?.media ?? null,
      productId: props.banner?.['product-id'] ?? null,
      title: props.banner?.title ?? '',
      subtitle: props.banner?.subtitle ?? '',
      linkUrl: props.banner?.['link-url'] ?? '',
      sortOrder: props.banner?.['sort-order'] ?? 0,
      isActive: props.banner?.['is-active'] ?? true,
      startsAt: parseUtc(props.banner?.['starts-at']),
      endsAt: parseUtc(props.banner?.['ends-at']),
    })
    productOptions.value = props.banner?.product ? [props.banner.product] : []
    searchProducts('')
    formRef.value?.clearValidate()
  },
)

function close() {
  emit('update:modelValue', false)
}

async function submit() {
  if (!(await formRef.value.validate().catch(() => false))) return

  saving.value = true
  try {
    const payload = {
      'media-id': form.media.id,
      'product-id': form.productId ?? null,
      title: form.title.trim() || null,
      subtitle: form.subtitle.trim() || null,
      'link-url': form.linkUrl.trim() || null,
      'sort-order': form.sortOrder,
      'is-active': form.isActive,
      // toISOString() is UTC — the backend stores UTC.
      'starts-at': form.startsAt ? form.startsAt.toISOString() : null,
      'ends-at': form.endsAt ? form.endsAt.toISOString() : null,
    }
    const { data } = isEdit.value
      ? await updateBanner(props.banner.id, payload)
      : await createBanner(payload)

    if (data.status === 'SUCCESS') {
      ElMessage.success(t(isEdit.value ? 'banners.updated' : 'banners.created'))
      emit('saved', data.result)
      close()
    } else {
      ElMessage.error((data['error-msg'] || []).map((c) => t(`errors.${c}`, c)).join(', '))
    }
  } catch (e) {
    // 401/403 are already surfaced by the axios interceptor.
    if (![401, 403].includes(e.response?.status)) ElMessage.error(t('errors.internal-server-error'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? t('banners.editTitle') : t('banners.addTitle')"
    width="min(600px, 94vw)"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item :label="t('banners.media')" prop="media">
        <MediaUploader v-model="form.media" allow-video />
      </el-form-item>
      <el-form-item :label="t('banners.product')" prop="productId">
        <el-select
          v-model="form.productId"
          filterable
          remote
          clearable
          :remote-method="searchProducts"
          :loading="productsLoading"
          :placeholder="t('banners.productPlaceholder')"
          :no-data-text="t('banners.noProducts')"
          style="width: 100%"
          @change="onProductChange"
        >
          <el-option v-for="p in productOptions" :key="p.id" :value="p.id" :label="p.name">
            <span>{{ p.name }}</span>
            <el-tag v-if="!p['is-active']" size="small" type="info" class="product-hidden">
              {{ t('banners.productHidden') }}
            </el-tag>
          </el-option>
        </el-select>
        <div class="form-hint">{{ t('banners.productHint') }}</div>
      </el-form-item>
      <el-form-item :label="t('banners.titleField')" prop="title">
        <el-input v-model="form.title" maxlength="200" />
      </el-form-item>
      <el-form-item :label="t('banners.subtitle')" prop="subtitle">
        <el-input v-model="form.subtitle" type="textarea" :rows="2" maxlength="300" show-word-limit />
      </el-form-item>
      <el-form-item :label="t('banners.linkUrl')" prop="linkUrl">
        <el-input v-model="form.linkUrl" maxlength="500" placeholder="https://… /products/…" />
      </el-form-item>
      <div class="form-row">
        <el-form-item :label="t('banners.startsAt')" prop="startsAt">
          <el-date-picker v-model="form.startsAt" type="datetime" :placeholder="t('banners.noLimit')" />
        </el-form-item>
        <el-form-item :label="t('banners.endsAt')" prop="endsAt">
          <el-date-picker v-model="form.endsAt" type="datetime" :placeholder="t('banners.noLimit')" />
        </el-form-item>
      </div>
      <div class="form-row">
        <el-form-item :label="t('banners.sortOrder')" prop="sortOrder">
          <el-input-number v-model="form.sortOrder" :step="1" :step-strictly="true" controls-position="right" />
        </el-form-item>
        <el-form-item :label="t('banners.visibility')" prop="isActive">
          <el-switch
            v-model="form.isActive"
            :active-text="t('banners.statusActive')"
            :inactive-text="t('banners.statusHidden')"
          />
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="close">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="saving" @click="submit">{{ t('common.save') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.form-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.form-hint {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--el-text-color-secondary);
}
.product-hidden {
  margin-left: 8px;
}
</style>
