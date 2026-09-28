<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

import { getProduct, createProduct, updateProduct } from '@/api/products'
import ImageGalleryEditor from '@/components/ImageGalleryEditor.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // null → create mode, otherwise the id of the product being edited.
  productId: { type: Number, default: null },
  // [{ id, name }] for the category select, loaded once by the list view.
  categories: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const { t } = useI18n()

const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const MAX_IMAGES = 20

const formRef = ref()
const loading = ref(false)
const loadError = ref(false)
const saving = ref(false)
const version = ref(null)
const form = reactive({
  images: [],
  name: '',
  slug: '',
  categoryId: null,
  shortDescription: '',
  description: '',
  sortOrder: 0,
  isActive: true,
  isFeatured: false,
})

const isEdit = computed(() => props.productId !== null)

const rules = computed(() => ({
  name: [
    { required: true, message: t('products.nameRequired'), trigger: 'blur' },
    { max: 200, message: t('errors.product-name-invalid'), trigger: 'blur' },
  ],
  // Optional: left empty, the backend generates it from the name.
  slug: [
    { pattern: SLUG_RE, message: t('errors.product-slug-invalid'), trigger: 'blur' },
    { max: 220, message: t('errors.product-slug-invalid'), trigger: 'blur' },
  ],
  categoryId: [{ required: true, message: t('products.categoryRequired'), trigger: 'change' }],
  shortDescription: [{ max: 500, message: t('errors.product-short-description-invalid'), trigger: 'blur' }],
}))

function fill(product) {
  version.value = product?.version ?? null
  Object.assign(form, {
    images: (product?.images || []).map((i) => ({ media: i.media, isPrimary: i['is-primary'] })),
    name: product?.name ?? '',
    slug: product?.slug ?? '',
    categoryId: product?.['category-id'] ?? null,
    shortDescription: product?.['short-description'] ?? '',
    description: product?.description ?? '',
    sortOrder: product?.['sort-order'] ?? 0,
    isActive: product?.['is-active'] ?? true,
    isFeatured: product?.['is-featured'] ?? false,
  })
  formRef.value?.clearValidate()
}

// The list only carries the cover image, so edit mode loads the full product.
async function load() {
  loading.value = true
  loadError.value = false
  try {
    const { data } = await getProduct(props.productId)
    if (data.status === 'SUCCESS') fill(data.result)
    else loadError.value = true
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    fill(null)
    if (isEdit.value) load()
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
      name: form.name.trim(),
      slug: form.slug.trim(),
      'category-id': form.categoryId,
      'short-description': form.shortDescription.trim() || null,
      description: form.description.trim() || null,
      'sort-order': form.sortOrder,
      'is-active': form.isActive,
      'is-featured': form.isFeatured,
      images: form.images.map((i) => ({ 'media-id': i.media.id, 'is-primary': i.isPrimary })),
    }
    const { data } = isEdit.value
      ? await updateProduct(props.productId, { ...payload, version: version.value })
      : await createProduct(payload)

    if (data.status === 'SUCCESS') {
      ElMessage.success(t(isEdit.value ? 'products.updated' : 'products.created'))
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
    :title="isEdit ? t('products.editTitle') : t('products.addTitle')"
    width="min(760px, 94vw)"
    top="5vh"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <el-form
      v-else
      ref="formRef"
      v-loading="loading"
      :model="form"
      :rules="rules"
      label-position="top"
      @submit.prevent="submit"
    >
      <el-form-item :label="t('products.images')" prop="images">
        <ImageGalleryEditor v-model="form.images" :max="MAX_IMAGES" />
      </el-form-item>

      <div class="form-grid">
        <el-form-item :label="t('products.name')" prop="name">
          <el-input v-model="form.name" maxlength="200" />
        </el-form-item>
        <el-form-item :label="t('products.category')" prop="categoryId">
          <el-select v-model="form.categoryId" filterable :placeholder="t('products.categoryPlaceholder')" style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :value="c.id" :label="c.name" />
          </el-select>
        </el-form-item>
      </div>

      <el-form-item :label="t('products.slug')" prop="slug">
        <el-input v-model="form.slug" maxlength="220" :placeholder="t('products.slugPlaceholder')" />
        <div class="form-hint">{{ t('products.slugHint') }}</div>
      </el-form-item>
      <el-form-item :label="t('products.shortDescription')" prop="shortDescription">
        <el-input v-model="form.shortDescription" type="textarea" :rows="2" maxlength="500" show-word-limit />
      </el-form-item>
      <el-form-item :label="t('products.description')" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="6" />
      </el-form-item>

      <div class="form-row">
        <el-form-item :label="t('products.sortOrder')" prop="sortOrder">
          <el-input-number v-model="form.sortOrder" :step="1" :step-strictly="true" controls-position="right" />
        </el-form-item>
        <el-form-item :label="t('products.visibility')" prop="isActive">
          <el-switch
            v-model="form.isActive"
            :active-text="t('products.statusActive')"
            :inactive-text="t('products.statusHidden')"
          />
        </el-form-item>
        <el-form-item :label="t('products.featured')" prop="isFeatured">
          <el-switch v-model="form.isFeatured" />
          <div class="form-hint">{{ t('products.featuredHint') }}</div>
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="close">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="saving" :disabled="loading || loadError" @click="submit">
        {{ t('common.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 20px;
}
.form-row {
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
}
.form-row .el-form-item {
  max-width: 260px;
}
.form-hint {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--el-text-color-secondary);
}
@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
