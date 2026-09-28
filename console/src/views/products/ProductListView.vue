<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, Star, StarFilled, Picture } from '@element-plus/icons-vue'

import { listProducts, updateProduct, deleteProduct } from '@/api/products'
import { listCategories } from '@/api/categories'
import { useAuthStore } from '@/stores/auth'
import ProductFormDialog from './ProductFormDialog.vue'

const { t } = useI18n()
const authStore = useAuthStore()

const products = ref([])
const total = ref(0)
const loading = ref(false)
const loadError = ref(false)
const categories = ref([])

const filters = reactive({ search: '', categoryId: null, status: null })
const page = ref(1)
const perPage = ref(20)

const dialogOpen = ref(false)
const editingId = ref(null)
// Row ids with a flag change waiting for the server.
const busy = ref(new Set())

const hasRowActions = computed(() => ['products.edit', 'products.delete'].some((p) => authStore.can(p)))
const canEdit = computed(() => authStore.can('products.edit'))

const STATUS_OPTIONS = ['active', 'hidden', 'featured']

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
    const { data } = await listProducts({
      search: filters.search.trim() || undefined,
      'category-id': filters.categoryId ?? undefined,
      status: filters.status ?? undefined,
      page: page.value,
      'per-page': perPage.value,
    })
    if (data.status === 'SUCCESS') {
      products.value = data.result.items
      total.value = data.result.total
      // Deleting the last row of the last page leaves it empty — step back.
      if (!products.value.length && page.value > 1 && total.value > 0) {
        page.value = Math.ceil(total.value / perPage.value)
        await load()
      }
    } else {
      loadError.value = true
    }
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  load()
}

async function loadCategories() {
  try {
    const { data } = await listCategories()
    if (data.status === 'SUCCESS') categories.value = (data.result || []).map((c) => ({ id: c.id, name: c.name }))
  } catch {
    // The filter/select just stays empty; the table still works.
  }
}

function openCreate() {
  editingId.value = null
  dialogOpen.value = true
}

function openEdit(row) {
  editingId.value = row.id
  dialogOpen.value = true
}

// Flag toggles send the row without `images`, so the backend keeps them.
async function setFlag(row, key, value) {
  busy.value.add(row.id)
  try {
    const { data } = await updateProduct(row.id, {
      name: row.name,
      slug: row.slug,
      'category-id': row['category-id'],
      'short-description': row['short-description'],
      description: row.description,
      'sort-order': row['sort-order'],
      'is-active': row['is-active'],
      'is-featured': row['is-featured'],
      [key]: value,
      version: row.version,
    })
    if (data.status === 'SUCCESS') {
      row[key] = value
      row.version = data.result.version
      ElMessage.success(t('products.updated'))
    } else {
      showErrors(data)
      if ((data['error-msg'] || []).includes('product-modified')) load()
    }
  } catch (e) {
    handleRequestError(e)
  } finally {
    busy.value.delete(row.id)
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(t('products.deleteConfirm', { name: row.name }), t('common.delete'), {
      type: 'warning',
      confirmButtonText: t('common.delete'),
      cancelButtonText: t('common.cancel'),
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  try {
    const { data } = await deleteProduct(row.id)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t('products.deleted'))
      await load()
    } else {
      showErrors(data)
    }
  } catch (e) {
    handleRequestError(e)
  }
}

onMounted(() => {
  load()
  loadCategories()
})
</script>

<template>
  <section class="af-card products">
    <header class="products__toolbar">
      <div class="products__filters">
        <el-input
          v-model="filters.search"
          :placeholder="t('products.searchPlaceholder')"
          :prefix-icon="Search"
          clearable
          class="products__search"
          @keyup.enter="applyFilters"
          @clear="applyFilters"
        />
        <el-select
          v-model="filters.categoryId"
          :placeholder="t('products.allCategories')"
          clearable
          filterable
          class="products__filter"
          @change="applyFilters"
        >
          <el-option v-for="c in categories" :key="c.id" :value="c.id" :label="c.name" />
        </el-select>
        <el-select
          v-model="filters.status"
          :placeholder="t('products.allStatuses')"
          clearable
          class="products__filter"
          @change="applyFilters"
        >
          <el-option v-for="s in STATUS_OPTIONS" :key="s" :value="s" :label="t(`products.filter.${s}`)" />
        </el-select>
      </div>
      <el-button v-if="authStore.can('products.create')" type="primary" :icon="Plus" @click="openCreate">
        {{ t('products.add') }}
      </el-button>
    </header>

    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <template v-else>
      <el-table v-loading="loading" :data="products" row-key="id" style="width: 100%">
        <el-table-column prop="sort-order" :label="t('products.sortOrder')" width="90" align="center" />
        <el-table-column :label="t('products.image')" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.cover"
              :src="row.cover.url"
              :preview-src-list="[row.cover.url]"
              preview-teleported
              fit="cover"
              class="products__thumb"
            />
            <div v-else class="products__thumb products__thumb--empty">
              <el-icon><Picture /></el-icon>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="t('products.name')" min-width="220">
          <template #default="{ row }">
            <div class="products__name">{{ row.name }}</div>
            <code class="products__slug">{{ row.slug }}</code>
          </template>
        </el-table-column>
        <el-table-column :label="t('products.category')" min-width="140">
          <template #default="{ row }">{{ row.category?.name || '—' }}</template>
        </el-table-column>
        <el-table-column prop="images-count" :label="t('products.imagesCount')" width="90" align="center" />
        <el-table-column :label="t('products.featured')" width="110" align="center">
          <template #default="{ row }">
            <el-tooltip :content="t('products.featuredHint')">
              <el-button
                link
                :type="row['is-featured'] ? 'warning' : 'info'"
                :icon="row['is-featured'] ? StarFilled : Star"
                :disabled="!canEdit"
                :loading="busy.has(row.id)"
                @click="setFlag(row, 'is-featured', !row['is-featured'])"
              />
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="t('products.visibility')" width="120">
          <template #default="{ row }">
            <el-switch
              v-if="canEdit"
              :model-value="row['is-active']"
              :loading="busy.has(row.id)"
              @change="setFlag(row, 'is-active', $event)"
            />
            <el-tag v-else :type="row['is-active'] ? 'success' : 'info'" effect="plain">
              {{ row['is-active'] ? t('products.statusActive') : t('products.statusHidden') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="hasRowActions" :label="t('common.actions')" width="110" fixed="right">
          <template #default="{ row }">
            <el-tooltip v-if="canEdit" :content="t('common.edit')">
              <el-button link type="primary" :icon="Edit" @click="openEdit(row)" />
            </el-tooltip>
            <el-tooltip v-if="authStore.can('products.delete')" :content="t('common.delete')">
              <el-button link type="danger" :icon="Delete" @click="remove(row)" />
            </el-tooltip>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :description="t('common.noData')" />
        </template>
      </el-table>

      <el-pagination
        v-if="total > 0"
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        background
        class="products__pagination"
        @current-change="load"
        @size-change="applyFilters"
      />
    </template>

    <ProductFormDialog v-model="dialogOpen" :product-id="editingId" :categories="categories" @saved="load" />
  </section>
</template>

<style scoped>
.products {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.products__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.products__filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  flex: 1;
}
.products__search {
  max-width: 300px;
}
.products__filter {
  width: 190px;
}
.products__thumb {
  width: 64px;
  height: 48px;
  display: block;
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-fill-color-light);
}
.products__thumb--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
}
.products__name {
  font-weight: 600;
}
.products__slug {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.products__pagination {
  justify-content: flex-end;
  flex-wrap: wrap;
}
@media (max-width: 640px) {
  .products__search,
  .products__filter {
    max-width: none;
    width: 100%;
  }
}
</style>
