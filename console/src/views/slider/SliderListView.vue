<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, VideoCamera } from '@element-plus/icons-vue'

import { listSliderItems, updateSliderItem, deleteSliderItem } from '@/api/slider'
import { useAuthStore } from '@/stores/auth'
import SliderFormDialog from './SliderFormDialog.vue'
import { displayStatus, formatDateTime } from '@/utils/schedule'

const { t, locale } = useI18n()
const authStore = useAuthStore()

const items = ref([])
const loading = ref(false)
const loadError = ref(false)
const search = ref('')

const dialogOpen = ref(false)
const editingItem = ref(null)
// Row ids whose active switch is waiting for the server.
const toggling = ref(new Set())

const hasRowActions = computed(() => ['slider.edit', 'slider.delete'].some((p) => authStore.can(p)))

const STATUS_TAG = { live: 'success', scheduled: 'warning', expired: 'info', hidden: 'info' }

const formatDate = (value) => formatDateTime(value, locale.value)

function showErrors(data) {
  ElMessage.error((data['error-msg'] || []).map((c) => t(`errors.${c}`, c)).join(', '))
}

function handleRequestError(e) {
  // 401/403 are already surfaced by the axios interceptor.
  if (![401, 403].includes(e.response?.status)) ElMessage.error(t('errors.internal-server-error'))
}

async function load() {
  loading.value = true
  loadError.value = false
  try {
    const { data } = await listSliderItems(search.value.trim())
    if (data.status === 'SUCCESS') {
      items.value = data.result || []
    } else {
      loadError.value = true
    }
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingItem.value = null
  dialogOpen.value = true
}

function openEdit(row) {
  editingItem.value = row
  dialogOpen.value = true
}

async function toggleActive(row, isActive) {
  toggling.value.add(row.id)
  try {
    const { data } = await updateSliderItem(row.id, {
      'media-id': row['media-id'],
      title: row.title,
      subtitle: row.subtitle,
      'link-url': row['link-url'],
      'sort-order': row['sort-order'],
      // Send the stored strings back untouched — they are already UTC.
      'starts-at': row['starts-at'],
      'ends-at': row['ends-at'],
      'is-active': isActive,
    })
    if (data.status === 'SUCCESS') {
      row['is-active'] = isActive
      ElMessage.success(t('slider.updated'))
    } else {
      showErrors(data)
    }
  } catch (e) {
    handleRequestError(e)
  } finally {
    toggling.value.delete(row.id)
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(
      t('slider.deleteConfirm', { name: row.title || `#${row.id}` }),
      t('common.delete'),
      {
        type: 'warning',
        confirmButtonText: t('common.delete'),
        cancelButtonText: t('common.cancel'),
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }
  try {
    const { data } = await deleteSliderItem(row.id)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t('slider.deleted'))
      await load()
    } else {
      showErrors(data)
    }
  } catch (e) {
    handleRequestError(e)
  }
}

onMounted(load)
</script>

<template>
  <section class="af-card slider">
    <header class="slider__toolbar">
      <el-input
        v-model="search"
        :placeholder="t('slider.searchPlaceholder')"
        :prefix-icon="Search"
        clearable
        class="slider__search"
        @keyup.enter="load"
        @clear="load"
      />
      <el-button v-if="authStore.can('slider.create')" type="primary" :icon="Plus" @click="openCreate">
        {{ t('slider.add') }}
      </el-button>
    </header>

    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <el-table v-else v-loading="loading" :data="items" row-key="id" style="width: 100%">
      <el-table-column prop="sort-order" :label="t('slider.sortOrder')" width="90" align="center" />
      <el-table-column :label="t('slider.media')" width="150">
        <template #default="{ row }">
          <div v-if="row.media?.['media-type'] === 'video'" class="slider__thumb slider__thumb--video">
            <video :src="row.media.url" muted preload="metadata" />
            <el-icon class="slider__video-icon"><VideoCamera /></el-icon>
          </div>
          <el-image
            v-else-if="row.media"
            :src="row.media.url"
            :preview-src-list="[row.media.url]"
            preview-teleported
            fit="cover"
            class="slider__thumb"
          />
        </template>
      </el-table-column>
      <el-table-column :label="t('slider.titleField')" min-width="220">
        <template #default="{ row }">
          <div class="slider__title">{{ row.title || '—' }}</div>
          <div v-if="row.subtitle" class="slider__subtitle">{{ row.subtitle }}</div>
        </template>
      </el-table-column>
      <el-table-column :label="t('slider.linkUrl')" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">
          <a v-if="row['link-url']" :href="row['link-url']" target="_blank" rel="noopener">{{ row['link-url'] }}</a>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column :label="t('slider.schedule')" min-width="170">
        <template #default="{ row }">
          <div class="slider__schedule">
            <span>{{ t('slider.from') }}: {{ formatDate(row['starts-at']) || t('slider.noLimit') }}</span>
            <span>{{ t('slider.to') }}: {{ formatDate(row['ends-at']) || t('slider.noLimit') }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="t('slider.status')" width="150">
        <template #default="{ row }">
          <div class="slider__status">
            <el-switch
              v-if="authStore.can('slider.edit')"
              :model-value="row['is-active']"
              :loading="toggling.has(row.id)"
              @change="toggleActive(row, $event)"
            />
            <el-tag :type="STATUS_TAG[displayStatus(row)]" effect="plain" size="small">
              {{ t(`slider.state.${displayStatus(row)}`) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column v-if="hasRowActions" :label="t('common.actions')" width="110" fixed="right">
        <template #default="{ row }">
          <el-tooltip v-if="authStore.can('slider.edit')" :content="t('common.edit')">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)" />
          </el-tooltip>
          <el-tooltip v-if="authStore.can('slider.delete')" :content="t('common.delete')">
            <el-button link type="danger" :icon="Delete" @click="remove(row)" />
          </el-tooltip>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :description="t('common.noData')" />
      </template>
    </el-table>

    <SliderFormDialog v-model="dialogOpen" :item="editingItem" @saved="load" />
  </section>
</template>

<style scoped>
.slider {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.slider__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.slider__search {
  max-width: 320px;
}
.slider__thumb {
  position: relative;
  width: 120px;
  height: 68px;
  display: block;
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-fill-color-light);
}
.slider__thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.slider__video-icon {
  position: absolute;
  right: 6px;
  bottom: 6px;
  padding: 3px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
}
.slider__title {
  font-weight: 600;
}
.slider__subtitle {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.slider__schedule {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: var(--el-text-color-regular);
}
.slider__status {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
