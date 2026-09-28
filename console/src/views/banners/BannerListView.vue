<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, VideoCamera } from '@element-plus/icons-vue'

import { listBanners, updateBanner, deleteBanner } from '@/api/banners'
import { useAuthStore } from '@/stores/auth'
import BannerFormDialog from './BannerFormDialog.vue'
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

const hasRowActions = computed(() => ['banners.edit', 'banners.delete'].some((p) => authStore.can(p)))

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
    const { data } = await listBanners(search.value.trim())
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
    const { data } = await updateBanner(row.id, {
      'media-id': row['media-id'],
      'product-id': row['product-id'],
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
      ElMessage.success(t('banners.updated'))
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
      t('banners.deleteConfirm', { name: row.title || `#${row.id}` }),
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
    const { data } = await deleteBanner(row.id)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t('banners.deleted'))
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
  <section class="af-card banners">
    <header class="banners__toolbar">
      <el-input
        v-model="search"
        :placeholder="t('banners.searchPlaceholder')"
        :prefix-icon="Search"
        clearable
        class="banners__search"
        @keyup.enter="load"
        @clear="load"
      />
      <el-button v-if="authStore.can('banners.create')" type="primary" :icon="Plus" @click="openCreate">
        {{ t('banners.add') }}
      </el-button>
    </header>

    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <el-table v-else v-loading="loading" :data="items" row-key="id" style="width: 100%">
      <el-table-column prop="sort-order" :label="t('banners.sortOrder')" width="90" align="center" />
      <el-table-column :label="t('banners.media')" width="150">
        <template #default="{ row }">
          <div v-if="row.media?.['media-type'] === 'video'" class="banners__thumb banners__thumb--video">
            <video :src="row.media.url" muted preload="metadata" />
            <el-icon class="banners__video-icon"><VideoCamera /></el-icon>
          </div>
          <el-image
            v-else-if="row.media"
            :src="row.media.url"
            :preview-src-list="[row.media.url]"
            preview-teleported
            fit="cover"
            class="banners__thumb"
          />
        </template>
      </el-table-column>
      <el-table-column :label="t('banners.titleField')" min-width="220">
        <template #default="{ row }">
          <div class="banners__title">{{ row.title || '—' }}</div>
          <div v-if="row.subtitle" class="banners__subtitle">{{ row.subtitle }}</div>
        </template>
      </el-table-column>
      <el-table-column :label="t('banners.product')" min-width="150">
        <template #default="{ row }">
          <template v-if="row.product">
            <span>{{ row.product.name }}</span>
            <el-tag v-if="!row.product['is-active']" size="small" type="info" class="banners__product-hidden">
              {{ t('banners.productHidden') }}
            </el-tag>
          </template>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column :label="t('banners.linkUrl')" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">
          <a v-if="row['link-url']" :href="row['link-url']" target="_blank" rel="noopener">{{ row['link-url'] }}</a>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column :label="t('banners.schedule')" min-width="170">
        <template #default="{ row }">
          <div class="banners__schedule">
            <span>{{ t('banners.from') }}: {{ formatDate(row['starts-at']) || t('banners.noLimit') }}</span>
            <span>{{ t('banners.to') }}: {{ formatDate(row['ends-at']) || t('banners.noLimit') }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="t('banners.status')" width="150">
        <template #default="{ row }">
          <div class="banners__status">
            <el-switch
              v-if="authStore.can('banners.edit')"
              :model-value="row['is-active']"
              :loading="toggling.has(row.id)"
              @change="toggleActive(row, $event)"
            />
            <el-tag :type="STATUS_TAG[displayStatus(row)]" effect="plain" size="small">
              {{ t(`banners.state.${displayStatus(row)}`) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column v-if="hasRowActions" :label="t('common.actions')" width="110" fixed="right">
        <template #default="{ row }">
          <el-tooltip v-if="authStore.can('banners.edit')" :content="t('common.edit')">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)" />
          </el-tooltip>
          <el-tooltip v-if="authStore.can('banners.delete')" :content="t('common.delete')">
            <el-button link type="danger" :icon="Delete" @click="remove(row)" />
          </el-tooltip>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :description="t('common.noData')" />
      </template>
    </el-table>

    <BannerFormDialog v-model="dialogOpen" :banner="editingItem" @saved="load" />
  </section>
</template>

<style scoped>
.banners {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.banners__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.banners__search {
  max-width: 320px;
}
.banners__thumb {
  position: relative;
  width: 120px;
  height: 68px;
  display: block;
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-fill-color-light);
}
.banners__thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.banners__video-icon {
  position: absolute;
  right: 6px;
  bottom: 6px;
  padding: 3px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
}
.banners__title {
  font-weight: 600;
}
.banners__product-hidden {
  margin-left: 6px;
}
.banners__subtitle {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.banners__schedule {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: var(--el-text-color-regular);
}
.banners__status {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
