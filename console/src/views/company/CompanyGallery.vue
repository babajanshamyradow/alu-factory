<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft, ArrowRight, Delete, EditPen, RefreshRight, View, Hide } from '@element-plus/icons-vue'

import {
  listCompanyImages, createCompanyImage, updateCompanyImage, reorderCompanyImages, deleteCompanyImage,
} from '@/api/company'
import { uploadMedia } from '@/api/media'
import { useAuthStore } from '@/stores/auth'
import { IMAGE_EXT, IMAGE_MAX_MB, checkUploadFile, uploadErrorKey } from '@/utils/media'

// "About us" photo gallery. Unlike the product form, nothing is buffered:
// every upload / caption / visibility / order change is saved right away.
const { t } = useI18n()
const authStore = useAuthStore()

const images = ref([])
const loading = ref(false)
const loadError = ref(false)
const uploading = ref(0)
// Image ids with a request in flight; a reorder locks the whole grid.
const busy = ref(new Set())
const reordering = ref(false)

const addInputRef = ref()
const replaceInputRef = ref()
let replaceTarget = null

const canEdit = computed(() => authStore.can('company.edit'))
const accept = IMAGE_EXT.map((e) => '.' + e).join(',')
const previewList = computed(() => images.value.map((i) => i.media?.url))

function errorText(data) {
  return (data['error-msg'] || []).map((c) => t(`errors.${c}`, c)).join(', ')
}

function handleRequestError(e) {
  const key = uploadErrorKey(e)
  if (key) ElMessage.error(t(key))
}

async function load() {
  loading.value = true
  loadError.value = false
  try {
    const { data } = await listCompanyImages()
    if (data.status === 'SUCCESS') images.value = data.result || []
    else loadError.value = true
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function pickNew() {
  if (!uploading.value) addInputRef.value.click()
}

async function onAddFiles(event) {
  const files = [...(event.target.files || [])]
  event.target.value = ''
  uploading.value = files.length
  // Sequential so the gallery order matches the picked order.
  for (const file of files) {
    try {
      const invalid = checkUploadFile(file)
      if (invalid) {
        ElMessage.error(`${file.name}: ${t(invalid)}`)
        continue
      }
      const { data: up } = await uploadMedia(file)
      if (up.status !== 'SUCCESS') {
        ElMessage.error(`${file.name}: ${errorText(up)}`)
        continue
      }
      const { data } = await createCompanyImage({ 'media-id': up.result.id })
      if (data.status === 'SUCCESS') images.value.push(data.result)
      else ElMessage.error(`${file.name}: ${errorText(data)}`)
    } catch (e) {
      handleRequestError(e)
    } finally {
      uploading.value -= 1
    }
  }
}

// PUT is a full update — send the image with the changed fields merged in.
async function save(image, changes, successKey = 'company.gallery.updated') {
  busy.value.add(image.id)
  try {
    const { data } = await updateCompanyImage(image.id, {
      'media-id': image['media-id'],
      caption: image.caption,
      'is-active': image['is-active'],
      'sort-order': image['sort-order'],
      ...changes,
    })
    if (data.status === 'SUCCESS') {
      Object.assign(image, data.result)
      ElMessage.success(t(successKey))
    } else {
      ElMessage.error(errorText(data))
      if ((data['error-msg'] || []).includes('company-image-not-found')) load()
    }
  } catch (e) {
    handleRequestError(e)
  } finally {
    busy.value.delete(image.id)
  }
}

async function editCaption(image) {
  let caption
  try {
    ;({ value: caption } = await ElMessageBox.prompt(t('company.gallery.captionPrompt'), t('company.gallery.caption'), {
      inputValue: image.caption || '',
      inputValidator: (v) => (v || '').trim().length <= 255 || t('errors.company-image-caption-invalid'),
      confirmButtonText: t('common.save'),
      cancelButtonText: t('common.cancel'),
    }))
  } catch {
    return
  }
  await save(image, { caption: (caption || '').trim() || null })
}

function pickReplacement(image) {
  replaceTarget = image
  replaceInputRef.value.click()
}

async function onReplaceFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  const image = replaceTarget
  replaceTarget = null
  if (!file || !image) return

  const invalid = checkUploadFile(file)
  if (invalid) {
    ElMessage.error(t(invalid))
    return
  }
  busy.value.add(image.id)
  try {
    const { data: up } = await uploadMedia(file)
    if (up.status !== 'SUCCESS') {
      ElMessage.error(errorText(up))
      return
    }
    await save(image, { 'media-id': up.result.id })
  } catch (e) {
    handleRequestError(e)
  } finally {
    busy.value.delete(image.id)
  }
}

async function move(index, delta) {
  const reordered = [...images.value]
  const [item] = reordered.splice(index, 1)
  reordered.splice(index + delta, 0, item)

  reordering.value = true
  try {
    const { data } = await reorderCompanyImages(reordered.map((i) => i.id))
    if (data.status === 'SUCCESS') {
      images.value = data.result || []
    } else {
      ElMessage.error(errorText(data))
      load()
    }
  } catch (e) {
    handleRequestError(e)
  } finally {
    reordering.value = false
  }
}

async function remove(image) {
  try {
    await ElMessageBox.confirm(t('company.gallery.deleteConfirm'), t('common.delete'), {
      type: 'warning',
      confirmButtonText: t('common.delete'),
      cancelButtonText: t('common.cancel'),
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  busy.value.add(image.id)
  try {
    const { data } = await deleteCompanyImage(image.id)
    if (data.status === 'SUCCESS') {
      images.value = images.value.filter((i) => i.id !== image.id)
      ElMessage.success(t('company.gallery.deleted'))
    } else {
      ElMessage.error(errorText(data))
      load()
    }
  } catch (e) {
    handleRequestError(e)
  } finally {
    busy.value.delete(image.id)
  }
}

onMounted(load)
</script>

<template>
  <section class="af-card gallery-card">
    <header class="gallery-card__header">
      <div>
        <h3 class="gallery-card__title">{{ t('company.gallery.title') }}</h3>
        <p class="gallery-card__subtitle">{{ t('company.gallery.subtitle') }}</p>
      </div>
      <span class="gallery-card__count">{{ images.length }}</span>
    </header>

    <input ref="addInputRef" type="file" :accept="accept" multiple hidden @change="onAddFiles" />
    <input ref="replaceInputRef" type="file" :accept="accept" hidden @change="onReplaceFile" />

    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <div v-else v-loading="loading || reordering" class="gallery-card__grid">
      <div
        v-for="(image, index) in images"
        :key="image.id"
        v-loading="busy.has(image.id)"
        class="tile"
        :class="{ 'is-hidden': !image['is-active'] }"
      >
        <el-image
          :src="image.media?.url"
          :preview-src-list="previewList"
          :initial-index="index"
          preview-teleported
          fit="cover"
          class="tile__img"
        />
        <span v-if="!image['is-active']" class="tile__badge">{{ t('company.gallery.hidden') }}</span>
        <p class="tile__caption" :class="{ 'is-empty': !image.caption }">
          {{ image.caption || t('company.gallery.noCaption') }}
        </p>
        <div v-if="canEdit" class="tile__actions">
          <el-tooltip :content="t('company.gallery.caption')">
            <el-button link type="primary" :icon="EditPen" @click="editCaption(image)" />
          </el-tooltip>
          <el-tooltip :content="image['is-active'] ? t('company.gallery.hide') : t('company.gallery.show')">
            <el-button
              link
              :type="image['is-active'] ? 'info' : 'success'"
              :icon="image['is-active'] ? Hide : View"
              @click="save(image, { 'is-active': !image['is-active'] })"
            />
          </el-tooltip>
          <el-tooltip :content="t('company.gallery.replace')">
            <el-button link type="info" :icon="RefreshRight" @click="pickReplacement(image)" />
          </el-tooltip>
          <el-button link type="info" :icon="ArrowLeft" :disabled="index === 0" @click="move(index, -1)" />
          <el-button link type="info" :icon="ArrowRight" :disabled="index === images.length - 1" @click="move(index, 1)" />
          <el-tooltip :content="t('common.delete')">
            <el-button link type="danger" :icon="Delete" @click="remove(image)" />
          </el-tooltip>
        </div>
      </div>

      <button v-if="canEdit" v-loading="uploading > 0" type="button" class="tile tile--add" @click="pickNew">
        <el-icon :size="26"><Plus /></el-icon>
        <span>{{ t('media.addImages') }}</span>
        <span class="tile__hint">{{ t('media.hintImage', { image: IMAGE_MAX_MB }) }}</span>
      </button>

      <el-empty
        v-if="!canEdit && !loading && !images.length"
        :description="t('common.noData')"
        class="gallery-card__empty"
      />
    </div>
  </section>
</template>

<style scoped>
.gallery-card {
  margin-top: 20px;
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.gallery-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.gallery-card__title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}
.gallery-card__subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.gallery-card__count {
  min-width: 28px;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--el-fill-color);
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}
.gallery-card__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
  min-height: 80px;
}
.gallery-card__empty {
  grid-column: 1 / -1;
}
.tile {
  position: relative;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  overflow: hidden;
  background: var(--el-bg-color);
}
.tile.is-hidden .tile__img {
  opacity: 0.45;
}
.tile__img {
  width: 100%;
  aspect-ratio: 4 / 3;
  display: block;
  background: var(--el-fill-color-light);
}
.tile__badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}
.tile__caption {
  margin: 0;
  padding: 8px 10px 0;
  font-size: 13px;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tile__caption.is-empty {
  color: var(--el-text-color-placeholder);
  font-style: italic;
}
.tile__actions {
  display: flex;
  justify-content: space-between;
  padding: 4px 6px 6px;
}
.tile__actions .el-button + .el-button {
  margin-left: 0;
}
.tile--add {
  min-height: 200px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  border: 1.5px dashed var(--el-border-color);
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-regular);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}
.tile--add:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
.tile__hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--el-text-color-secondary);
  text-align: center;
}
</style>
