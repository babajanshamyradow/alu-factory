<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { UploadFilled, Delete, RefreshRight } from '@element-plus/icons-vue'

import { uploadMedia } from '@/api/media'
import { IMAGE_EXT, VIDEO_EXT, IMAGE_MAX_MB, VIDEO_MAX_MB, checkUploadFile, uploadErrorKey } from '@/utils/media'

// Uploads a file to /api/media right away and v-models the resulting media
// object ({ id, url, 'media-type', ... }); the parent form only sends its id.
const props = defineProps({
  modelValue: { type: Object, default: null },
  allowVideo: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const { t } = useI18n()

const uploading = ref(false)
const inputRef = ref()

const accept = [...IMAGE_EXT, ...(props.allowVideo ? VIDEO_EXT : [])].map((e) => '.' + e).join(',')

function pick() {
  if (!props.disabled && !uploading.value) inputRef.value.click()
}

async function onFileChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  const invalid = checkUploadFile(file, { allowVideo: props.allowVideo })
  if (invalid) {
    ElMessage.error(t(invalid))
    return
  }

  uploading.value = true
  try {
    const { data } = await uploadMedia(file)
    if (data.status === 'SUCCESS') {
      emit('update:modelValue', data.result)
    } else {
      ElMessage.error((data['error-msg'] || []).map((c) => t(`errors.${c}`, c)).join(', '))
    }
  } catch (e) {
    const key = uploadErrorKey(e)
    if (key) ElMessage.error(t(key))
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="media-uploader" :class="{ 'is-disabled': disabled }">
    <input ref="inputRef" type="file" :accept="accept" hidden @change="onFileChange" />

    <div v-if="modelValue" v-loading="uploading" class="media-uploader__preview">
      <video
        v-if="modelValue['media-type'] === 'video'"
        :src="modelValue.url"
        controls
        muted
        class="media-uploader__media"
      />
      <img v-else :src="modelValue.url" :alt="modelValue['alt-text'] || ''" class="media-uploader__media" />
      <div v-if="!disabled" class="media-uploader__actions">
        <el-button size="small" :icon="RefreshRight" @click="pick">{{ t('media.replace') }}</el-button>
        <el-button size="small" type="danger" plain :icon="Delete" @click="emit('update:modelValue', null)">
          {{ t('media.remove') }}
        </el-button>
      </div>
    </div>

    <button v-else v-loading="uploading" type="button" class="media-uploader__drop" :disabled="disabled" @click="pick">
      <el-icon :size="32"><UploadFilled /></el-icon>
      <span class="media-uploader__title">{{ t('media.choose') }}</span>
      <span class="media-uploader__hint">
        {{ allowVideo ? t('media.hintImageVideo', { image: IMAGE_MAX_MB, video: VIDEO_MAX_MB }) : t('media.hintImage', { image: IMAGE_MAX_MB }) }}
      </span>
    </button>
  </div>
</template>

<style scoped>
.media-uploader {
  width: 100%;
}
.media-uploader__drop {
  width: 100%;
  min-height: 150px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 16px;
  border: 1.5px dashed var(--el-border-color);
  border-radius: 12px;
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-secondary);
  font: inherit;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}
.media-uploader__drop:hover:not(:disabled) {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
.media-uploader__drop:disabled {
  cursor: not-allowed;
}
.media-uploader__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-regular);
}
.media-uploader__hint {
  font-size: 12px;
}
.media-uploader__preview {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.media-uploader__media {
  width: 100%;
  max-height: 240px;
  object-fit: contain;
  border-radius: 12px;
  background: var(--el-fill-color-light);
}
.media-uploader__actions {
  display: flex;
  gap: 8px;
}
</style>
