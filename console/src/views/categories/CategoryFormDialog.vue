<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

import { createCategory, updateCategory } from '@/api/categories'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // null → create mode, otherwise the category being edited.
  category: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const { t } = useI18n()

const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

const formRef = ref()
const saving = ref(false)
const form = reactive({ name: '', slug: '', description: '', sortOrder: 0, isActive: true })

const isEdit = computed(() => !!props.category)

const rules = computed(() => ({
  name: [
    { required: true, message: t('categories.nameRequired'), trigger: 'blur' },
    { max: 128, message: t('errors.category-name-invalid'), trigger: 'blur' },
  ],
  // Optional: left empty, the backend generates it from the name.
  slug: [
    { pattern: SLUG_RE, message: t('errors.category-slug-invalid'), trigger: 'blur' },
    { max: 160, message: t('errors.category-slug-invalid'), trigger: 'blur' },
  ],
}))

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, {
      name: props.category?.name ?? '',
      slug: props.category?.slug ?? '',
      description: props.category?.description ?? '',
      sortOrder: props.category?.['sort-order'] ?? 0,
      isActive: props.category?.['is-active'] ?? true,
    })
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
      name: form.name.trim(),
      slug: form.slug.trim(),
      description: form.description.trim() || null,
      'sort-order': form.sortOrder,
      'is-active': form.isActive,
    }
    const { data } = isEdit.value
      ? await updateCategory(props.category.id, payload)
      : await createCategory(payload)

    if (data.status === 'SUCCESS') {
      ElMessage.success(t(isEdit.value ? 'categories.updated' : 'categories.created'))
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
    :title="isEdit ? t('categories.editTitle') : t('categories.addTitle')"
    width="min(520px, 92vw)"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item :label="t('categories.name')" prop="name">
        <el-input v-model="form.name" maxlength="128" />
      </el-form-item>
      <el-form-item :label="t('categories.slug')" prop="slug">
        <el-input v-model="form.slug" maxlength="160" :placeholder="t('categories.slugPlaceholder')" />
        <div class="form-hint">{{ t('categories.slugHint') }}</div>
      </el-form-item>
      <el-form-item :label="t('categories.description')" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>
      <div class="form-row">
        <el-form-item :label="t('categories.sortOrder')" prop="sortOrder">
          <el-input-number v-model="form.sortOrder" :step="1" :step-strictly="true" controls-position="right" />
        </el-form-item>
        <el-form-item :label="t('categories.status')" prop="isActive">
          <el-switch
            v-model="form.isActive"
            :active-text="t('categories.statusActive')"
            :inactive-text="t('categories.statusInactive')"
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
.form-hint {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--el-text-color-secondary);
}
.form-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
</style>
