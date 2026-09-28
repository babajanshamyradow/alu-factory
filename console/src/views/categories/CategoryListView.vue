<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'

import { listCategories, updateCategory, deleteCategory } from '@/api/categories'
import { useAuthStore } from '@/stores/auth'
import CategoryFormDialog from './CategoryFormDialog.vue'

const { t } = useI18n()
const authStore = useAuthStore()

const categories = ref([])
const loading = ref(false)
const loadError = ref(false)
const search = ref('')

const dialogOpen = ref(false)
const editingCategory = ref(null)
// Row ids whose active switch is waiting for the server.
const toggling = ref(new Set())

const hasRowActions = computed(() => ['categories.edit', 'categories.delete'].some((p) => authStore.can(p)))

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
    const { data } = await listCategories(search.value.trim())
    if (data.status === 'SUCCESS') {
      categories.value = data.result || []
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
  editingCategory.value = null
  dialogOpen.value = true
}

function openEdit(row) {
  editingCategory.value = row
  dialogOpen.value = true
}

async function toggleActive(row, isActive) {
  toggling.value.add(row.id)
  try {
    const { data } = await updateCategory(row.id, {
      name: row.name,
      slug: row.slug,
      description: row.description,
      'sort-order': row['sort-order'],
      'is-active': isActive,
    })
    if (data.status === 'SUCCESS') {
      row['is-active'] = isActive
      ElMessage.success(t('categories.updated'))
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
    await ElMessageBox.confirm(t('categories.deleteConfirm', { name: row.name }), t('common.delete'), {
      type: 'warning',
      confirmButtonText: t('common.delete'),
      cancelButtonText: t('common.cancel'),
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  try {
    const { data } = await deleteCategory(row.id)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t('categories.deleted'))
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
  <section class="af-card categories">
    <header class="categories__toolbar">
      <el-input
        v-model="search"
        :placeholder="t('categories.searchPlaceholder')"
        :prefix-icon="Search"
        clearable
        class="categories__search"
        @keyup.enter="load"
        @clear="load"
      />
      <el-button v-if="authStore.can('categories.create')" type="primary" :icon="Plus" @click="openCreate">
        {{ t('categories.add') }}
      </el-button>
    </header>

    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <el-table v-else v-loading="loading" :data="categories" row-key="id" style="width: 100%">
      <el-table-column prop="sort-order" :label="t('categories.sortOrder')" width="100" align="center" />
      <el-table-column prop="name" :label="t('categories.name')" min-width="160" />
      <el-table-column prop="slug" :label="t('categories.slug')" min-width="160">
        <template #default="{ row }"><code class="categories__slug">{{ row.slug }}</code></template>
      </el-table-column>
      <el-table-column :label="t('categories.description')" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">{{ row.description || '—' }}</template>
      </el-table-column>
      <el-table-column prop="products-count" :label="t('categories.products')" width="110" align="center" />
      <el-table-column :label="t('categories.status')" width="130">
        <template #default="{ row }">
          <el-switch
            v-if="authStore.can('categories.edit')"
            :model-value="row['is-active']"
            :loading="toggling.has(row.id)"
            @change="toggleActive(row, $event)"
          />
          <el-tag v-else :type="row['is-active'] ? 'success' : 'info'" effect="plain">
            {{ row['is-active'] ? t('categories.statusActive') : t('categories.statusInactive') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="hasRowActions" :label="t('common.actions')" width="120" fixed="right">
        <template #default="{ row }">
          <el-tooltip v-if="authStore.can('categories.edit')" :content="t('common.edit')">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)" />
          </el-tooltip>
          <el-tooltip v-if="authStore.can('categories.delete')" :content="t('common.delete')">
            <el-button link type="danger" :icon="Delete" @click="remove(row)" />
          </el-tooltip>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :description="t('common.noData')" />
      </template>
    </el-table>

    <CategoryFormDialog v-model="dialogOpen" :category="editingCategory" @saved="load" />
  </section>
</template>

<style scoped>
.categories {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.categories__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.categories__search {
  max-width: 320px;
}
.categories__slug {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
