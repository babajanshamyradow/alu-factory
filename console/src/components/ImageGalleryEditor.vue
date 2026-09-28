<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Plus, Star, StarFilled, ArrowLeft, ArrowRight, Delete } from '@element-plus/icons-vue'

import { uploadMedia } from '@/api/media'
import { IMAGE_EXT, IMAGE_MAX_MB, checkUploadFile, uploadErrorKey } from '@/utils/media'

// Ordered image list for a gallery (e.g. product images). v-models
// [{ media, isPrimary }]; uploads go to /api/media immediately, the parent
// form sends only media ids. Exactly one item is primary while any exist.
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  max: { type: Number, default: 20 },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const { t } = useI18n()

const inputRef = ref()
const uploading = ref(0)

const accept = IMAGE_EXT.map((e) => '.' + e).join(',')

function update(items) {
  if (items.length && !items.some((i) => i.isPrimary)) items[0] = { ...items[0], isPrimary: true }
  emit('update:modelValue', items)
}

function pick() {
  if (!props.disabled && !uploading.value) inputRef.value.click()
}

async function onFileChange(event) {
  const files = [...(event.target.files || [])]
  event.target.value = ''
  if (!files.length) return

  const room = props.max - props.modelValue.length
  if (files.length > room) ElMessage.warning(t('media.maxImages', { max: props.max }))

  let items = [...props.modelValue]
  uploading.value = Math.min(files.length, room)
  // Sequential so the gallery order matches the picked order.
  for (const file of files.slice(0, room)) {
    const invalid = checkUploadFile(file)
    if (invalid) {
      ElMessage.error(`${file.name}: ${t(invalid)}`)
    } else {
      try {
        const { data } = await uploadMedia(file)
        if (data.status === 'SUCCESS') {
          items = [...items, { media: data.result, isPrimary: false }]
          update(items)
        } else {
          ElMessage.error(`${file.name}: ` + (data['error-msg'] || []).map((c) => t(`errors.${c}`, c)).join(', '))
        }
      } catch (e) {
        const key = uploadErrorKey(e)
        if (key) ElMessage.error(`${file.name}: ${t(key)}`)
      }
    }
    uploading.value -= 1
  }
  uploading.value = 0
}

function setPrimary(index) {
  update(props.modelValue.map((item, i) => ({ ...item, isPrimary: i === index })))
}

function move(index, delta) {
  const items = [...props.modelValue]
  const [item] = items.splice(index, 1)
  items.splice(index + delta, 0, item)
  update(items)
}

function remove(index) {
  update(props.modelValue.filter((_, i) => i !== index))
}
</script>

<template>
  <div class="gallery">
    <input ref="inputRef" type="file" :accept="accept" multiple hidden @change="onFileChange" />

    <div v-for="(item, index) in modelValue" :key="item.media.id" class="gallery__tile" :class="{ 'is-primary': item.isPrimary }">
      <el-image
        :src="item.media.url"
        :preview-src-list="modelValue.map((i) => i.media.url)"
        :initial-index="index"
        preview-teleported
        fit="cover"
        class="gallery__img"
      />
      <span v-if="item.isPrimary" class="gallery__badge">{{ t('media.primary') }}</span>
      <div v-if="!disabled" class="gallery__actions">
        <el-tooltip :content="t('media.makePrimary')" :disabled="item.isPrimary">
          <el-button
            link
            :type="item.isPrimary ? 'warning' : 'info'"
            :icon="item.isPrimary ? StarFilled : Star"
            @click="setPrimary(index)"
          />
        </el-tooltip>
        <el-button link type="info" :icon="ArrowLeft" :disabled="index === 0" @click="move(index, -1)" />
        <el-button link type="info" :icon="ArrowRight" :disabled="index === modelValue.length - 1" @click="move(index, 1)" />
        <el-tooltip :content="t('media.remove')">
          <el-button link type="danger" :icon="Delete" @click="remove(index)" />
        </el-tooltip>
      </div>
    </div>

    <button
      v-if="!disabled && modelValue.length < max"
      v-loading="uploading > 0"
      type="button"
      class="gallery__add"
      @click="pick"
    >
      <el-icon :size="24"><Plus /></el-icon>
      <span>{{ t('media.addImages') }}</span>
      <span class="gallery__hint">{{ t('media.hintImage', { image: IMAGE_MAX_MB }) }}</span>
    </button>
  </div>
</template>

<style scoped>
.gallery {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}
.gallery__tile {
  position: relative;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  overflow: hidden;
  background: var(--el-bg-color);
}
.gallery__tile.is-primary {
  border-color: var(--el-color-warning);
  box-shadow: 0 0 0 1px var(--el-color-warning);
}
.gallery__img {
  width: 100%;
  aspect-ratio: 4 / 3;
  display: block;
  background: var(--el-fill-color-light);
}
.gallery__badge {
  position: absolute;
  top: 6px;
  left: 6px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--el-color-warning);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}
.gallery__actions {
  display: flex;
  justify-content: space-between;
  padding: 4px 8px;
}
.gallery__actions .el-button + .el-button {
  margin-left: 0;
}
.gallery__add {
  min-height: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px;
  border: 1.5px dashed var(--el-border-color);
  border-radius: 12px;
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-regular);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}
.gallery__add:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
.gallery__hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--el-text-color-secondary);
  text-align: center;
}
</style>
