<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search, Message, Phone } from '@element-plus/icons-vue'

import { listContactMessages } from '@/api/contactMessages'
import { useNewContactCount } from '@/composables/useNewContactCount'
import { formatDateTime } from '@/utils/schedule'
import ContactMessageDrawer from './ContactMessageDrawer.vue'

const { t, locale } = useI18n()
const { setCount: setNewCount } = useNewContactCount()

const STATUS_TAG = { new: 'danger', read: 'success', archived: 'info' }
// '' = all statuses. New first: that's the inbox people work from.
const TABS = ['new', 'read', 'archived', '']

const messages = ref([])
const total = ref(0)
const counts = reactive({ new: 0, read: 0, archived: 0 })
const loading = ref(false)
const loadError = ref(false)

const status = ref('new')
const search = ref('')
const page = ref(1)
const perPage = ref(20)

const drawerOpen = ref(false)
const openedId = ref(null)

async function load() {
  loading.value = true
  loadError.value = false
  try {
    const { data } = await listContactMessages({
      search: search.value.trim() || undefined,
      status: status.value || undefined,
      page: page.value,
      'per-page': perPage.value,
    })
    if (data.status !== 'SUCCESS') {
      loadError.value = true
      return
    }
    messages.value = data.result.items
    total.value = data.result.total
    Object.assign(counts, data.result.counts)
    setNewCount(counts.new)
    // A status change can empty the last page — step back.
    if (!messages.value.length && page.value > 1 && total.value > 0) {
      page.value = Math.ceil(total.value / perPage.value)
      await load()
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

function tabCount(tab) {
  return tab ? counts[tab] : counts.new + counts.read + counts.archived
}

function open(row) {
  openedId.value = row.id
  drawerOpen.value = true
}

onMounted(load)
</script>

<template>
  <section class="af-card contact">
    <header class="contact__toolbar">
      <el-radio-group v-model="status" @change="applyFilters">
        <el-radio-button v-for="tab in TABS" :key="tab || 'all'" :value="tab">
          {{ tab ? t(`contact.status.${tab}`) : t('contact.all') }}
          <span class="contact__tab-count" :class="{ 'is-new': tab === 'new' && counts.new }">{{ tabCount(tab) }}</span>
        </el-radio-button>
      </el-radio-group>
      <el-input
        v-model="search"
        :placeholder="t('contact.searchPlaceholder')"
        :prefix-icon="Search"
        clearable
        class="contact__search"
        @keyup.enter="applyFilters"
        @clear="applyFilters"
      />
    </header>

    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <template v-else>
      <el-table
        v-loading="loading"
        :data="messages"
        row-key="id"
        :row-class-name="({ row }) => (row.status === 'new' ? 'is-unread' : '')"
        class="contact__table"
        style="width: 100%"
        @row-click="open"
      >
        <el-table-column :label="t('contact.date')" width="150">
          <template #default="{ row }">{{ formatDateTime(row['created-at'], locale) }}</template>
        </el-table-column>
        <el-table-column prop="name" :label="t('contact.name')" min-width="150" show-overflow-tooltip />
        <el-table-column :label="t('contact.contacts')" min-width="190">
          <template #default="{ row }">
            <div class="contact__contacts">
              <span v-if="row.email"><el-icon><Message /></el-icon>{{ row.email }}</span>
              <span v-if="row.phone"><el-icon><Phone /></el-icon>{{ row.phone }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="t('contact.message')" min-width="260">
          <template #default="{ row }"><div class="contact__preview">{{ row.message }}</div></template>
        </el-table-column>
        <el-table-column :label="t('contact.statusLabel')" width="130">
          <template #default="{ row }">
            <el-tag :type="STATUS_TAG[row.status]" effect="light" size="small">{{ t(`contact.status.${row.status}`) }}</el-tag>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :description="t('contact.empty')" />
        </template>
      </el-table>

      <el-pagination
        v-if="total > perPage"
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        background
        class="contact__pagination"
        @current-change="load"
        @size-change="applyFilters"
      />
    </template>

    <ContactMessageDrawer v-model="drawerOpen" :message-id="openedId" @changed="load" />
  </section>
</template>

<style scoped>
.contact {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.contact__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.contact__search {
  max-width: 320px;
}
.contact__tab-count {
  margin-left: 6px;
  padding: 0 7px;
  border-radius: 999px;
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
  font-size: 11px;
  font-weight: 600;
}
.contact__tab-count.is-new {
  background: var(--el-color-danger);
  color: #fff;
}
.contact__table :deep(.el-table__row) {
  cursor: pointer;
}
.contact__table :deep(.is-unread td) {
  font-weight: 600;
}
.contact__contacts {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 13px;
}
.contact__contacts span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.contact__preview {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: var(--el-text-color-regular);
  font-weight: 400;
}
.contact__pagination {
  justify-content: flex-end;
  flex-wrap: wrap;
}
@media (max-width: 640px) {
  .contact__search {
    max-width: none;
    width: 100%;
  }
}
</style>
