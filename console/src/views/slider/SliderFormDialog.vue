<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

import { createSliderItem, updateSliderItem } from '@/api/slider'
import MediaUploader from '@/components/MediaUploader.vue'
import { parseUtc } from '@/utils/schedule'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // null → create mode, otherwise the slider item being edited.
  item: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const { t } = useI18n()

// Mirrors backend LINK_URL_RE: absolute http(s) URL or a site path.
const LINK_URL_RE = /^(https?:\/\/\S+|\/\S*)$/

const formRef = ref()
const saving = ref(false)
const form = reactive({
  media: null,
  title: '',
  subtitle: '',
  linkUrl: '',
  sortOrder: 0,
  isActive: true,
  startsAt: null,
  endsAt: null,
})

const isEdit = computed(() => !!props.item)

const rules = computed(() => ({
  media: [{ required: true, message: t('slider.mediaRequired'), trigger: 'change' }],
  title: [{ max: 200, message: t('errors.slider-title-invalid'), trigger: 'blur' }],
  subtitle: [{ max: 300, message: t('errors.slider-subtitle-invalid'), trigger: 'blur' }],
  linkUrl: [
    { max: 500, message: t('errors.slider-link-url-invalid'), trigger: 'blur' },
    { pattern: LINK_URL_RE, message: t('errors.slider-link-url-invalid'), trigger: 'blur' },
  ],
  endsAt: [
    {
      validator: (_rule, value, callback) =>
        value && form.startsAt && value <= form.startsAt
          ? callback(new Error(t('errors.slider-dates-order-invalid')))
          : callback(),
      trigger: 'change',
    },
  ],
}))

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, {
      media: props.item?.media ?? null,
      title: props.item?.title ?? '',
      subtitle: props.item?.subtitle ?? '',
      linkUrl: props.item?.['link-url'] ?? '',
      sortOrder: props.item?.['sort-order'] ?? 0,
      isActive: props.item?.['is-active'] ?? true,
      startsAt: parseUtc(props.item?.['starts-at']),
      endsAt: parseUtc(props.item?.['ends-at']),
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
      'media-id': form.media.id,
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
      ? await updateSliderItem(props.item.id, payload)
      : await createSliderItem(payload)

    if (data.status === 'SUCCESS') {
      ElMessage.success(t(isEdit.value ? 'slider.updated' : 'slider.created'))
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
    :title="isEdit ? t('slider.editTitle') : t('slider.addTitle')"
    width="min(600px, 94vw)"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item :label="t('slider.media')" prop="media">
        <MediaUploader v-model="form.media" allow-video />
      </el-form-item>
      <el-form-item :label="t('slider.titleField')" prop="title">
        <el-input v-model="form.title" maxlength="200" />
      </el-form-item>
      <el-form-item :label="t('slider.subtitle')" prop="subtitle">
        <el-input v-model="form.subtitle" type="textarea" :rows="2" maxlength="300" show-word-limit />
      </el-form-item>
      <el-form-item :label="t('slider.linkUrl')" prop="linkUrl">
        <el-input v-model="form.linkUrl" maxlength="500" placeholder="https://… /products/…" />
      </el-form-item>
      <div class="form-row">
        <el-form-item :label="t('slider.startsAt')" prop="startsAt">
          <el-date-picker v-model="form.startsAt" type="datetime" :placeholder="t('slider.noLimit')" />
        </el-form-item>
        <el-form-item :label="t('slider.endsAt')" prop="endsAt">
          <el-date-picker v-model="form.endsAt" type="datetime" :placeholder="t('slider.noLimit')" />
        </el-form-item>
      </div>
      <div class="form-row">
        <el-form-item :label="t('slider.sortOrder')" prop="sortOrder">
          <el-input-number v-model="form.sortOrder" :step="1" :step-strictly="true" controls-position="right" />
        </el-form-item>
        <el-form-item :label="t('slider.visibility')" prop="isActive">
          <el-switch
            v-model="form.isActive"
            :active-text="t('slider.statusActive')"
            :inactive-text="t('slider.statusHidden')"
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
</style>
