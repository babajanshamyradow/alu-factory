<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Lock, Unlock, Key, Delete } from '@element-plus/icons-vue'

import { listUsers, setUserLocked, resetUserPassword, deleteUser } from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import UserFormDialog from './UserFormDialog.vue'

const { t } = useI18n()
const authStore = useAuthStore()

const MIN_PASSWORD_LENGTH = 6

const users = ref([])
const loading = ref(false)
const loadError = ref(false)
const search = ref('')

const dialogOpen = ref(false)
const editingUser = ref(null)

const hasRowActions = computed(() =>
  ['users.edit', 'users.lock', 'users.resetPassword', 'users.delete'].some((p) => authStore.can(p)),
)

const isSelf = (row) => row.username === authStore.user?.username

// Admins can edit, but not superuser accounts (enforced by the backend too).
const canEditRow = (row) =>
  authStore.can('users.edit') && (authStore.role === 'superuser' || row.role !== 'superuser')

const ROLE_TAG = { superuser: 'danger', admin: 'warning', operator: 'info' }

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
    const { data } = await listUsers(search.value.trim())
    if (data.status === 'SUCCESS') {
      users.value = data.result || []
    } else {
      loadError.value = true
    }
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function onSaved(saved) {
  // Keep the topbar name in sync when the current user edits themselves.
  if (saved && isSelf(saved)) authStore.setUser({ ...authStore.user, fullname: saved.fullname, email: saved.email })
  load()
}

function openCreate() {
  editingUser.value = null
  dialogOpen.value = true
}

function openEdit(row) {
  editingUser.value = row
  dialogOpen.value = true
}

async function toggleLock(row) {
  const locked = !row.locked
  try {
    await ElMessageBox.confirm(
      t(locked ? 'users.lockConfirm' : 'users.unlockConfirm', { name: row.username }),
      t('common.confirm'),
      { type: 'warning', confirmButtonText: t('common.yes'), cancelButtonText: t('common.no') },
    )
  } catch {
    return
  }
  try {
    const { data } = await setUserLocked(row.username, locked)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t(locked ? 'users.locked' : 'users.unlocked'))
      await load()
    } else {
      showErrors(data)
    }
  } catch (e) {
    handleRequestError(e)
  }
}

async function resetPassword(row) {
  let password
  try {
    ;({ value: password } = await ElMessageBox.prompt(
      t('users.resetPasswordPrompt', { name: row.username }),
      t('users.resetPassword'),
      {
        inputType: 'password',
        inputValidator: (v) => (v && v.length >= MIN_PASSWORD_LENGTH) || t('errors.password-too-short'),
        confirmButtonText: t('common.save'),
        cancelButtonText: t('common.cancel'),
      },
    ))
  } catch {
    return
  }
  try {
    const { data } = await resetUserPassword(row.username, password)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t('users.passwordReset'))
    } else {
      showErrors(data)
    }
  } catch (e) {
    handleRequestError(e)
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(t('users.deleteConfirm', { name: row.username }), t('common.delete'), {
      type: 'warning',
      confirmButtonText: t('common.delete'),
      cancelButtonText: t('common.cancel'),
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  try {
    const { data } = await deleteUser(row.username)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t('users.deleted'))
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
  <section class="af-card users">
    <header class="users__toolbar">
      <el-input
        v-model="search"
        :placeholder="t('users.searchPlaceholder')"
        :prefix-icon="Search"
        clearable
        class="users__search"
        @keyup.enter="load"
        @clear="load"
      />
      <el-button v-if="authStore.can('users.create')" type="primary" :icon="Plus" @click="openCreate">
        {{ t('users.add') }}
      </el-button>
    </header>

    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <el-table v-else v-loading="loading" :data="users" row-key="username" style="width: 100%">
      <el-table-column prop="username" :label="t('users.username')" min-width="130" />
      <el-table-column prop="fullname" :label="t('users.fullname')" min-width="160" />
      <el-table-column prop="email" :label="t('users.email')" min-width="180">
        <template #default="{ row }">{{ row.email || '—' }}</template>
      </el-table-column>
      <el-table-column :label="t('users.role')" width="130">
        <template #default="{ row }">
          <el-tag :type="ROLE_TAG[row.role]" effect="light">{{ t(`roles.${row.role}`) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('users.status')" width="130">
        <template #default="{ row }">
          <el-tag :type="row.locked ? 'danger' : 'success'" effect="plain">
            {{ row.locked ? t('users.statusLocked') : t('users.statusActive') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="hasRowActions" :label="t('common.actions')" width="200" fixed="right">
        <template #default="{ row }">
          <el-tooltip v-if="canEditRow(row)" :content="t('common.edit')">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)" />
          </el-tooltip>
          <template v-if="!isSelf(row)">
            <el-tooltip v-if="authStore.can('users.lock')" :content="row.locked ? t('users.unlock') : t('users.lock')">
              <el-button link :type="row.locked ? 'success' : 'warning'" :icon="row.locked ? Unlock : Lock" @click="toggleLock(row)" />
            </el-tooltip>
          </template>
          <el-tooltip v-if="authStore.can('users.resetPassword')" :content="t('users.resetPassword')">
            <el-button link type="info" :icon="Key" @click="resetPassword(row)" />
          </el-tooltip>
          <el-tooltip v-if="authStore.can('users.delete') && !isSelf(row)" :content="t('common.delete')">
            <el-button link type="danger" :icon="Delete" @click="remove(row)" />
          </el-tooltip>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :description="t('common.noData')" />
      </template>
    </el-table>

    <UserFormDialog v-model="dialogOpen" :user="editingUser" @saved="onSaved" />
  </section>
</template>

<style scoped>
.users {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.users__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.users__search {
  max-width: 320px;
}
</style>
