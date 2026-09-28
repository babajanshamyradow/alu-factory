<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Message, Phone, Delete } from '@element-plus/icons-vue'

import { getContactMessage, setContactMessageStatus, deleteContactMessage } from '@/api/contactMessages'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/schedule'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  messageId: { type: Number, default: null },
})
// `changed` — status changed or message deleted; the list reloads.
const emit = defineEmits(['update:modelValue', 'changed'])

const { t, locale } = useI18n()
const authStore = useAuthStore()

const STATUSES = ['new', 'read', 'archived']
const STATUS_TAG = { new: 'danger', read: 'success', archived: 'info' }

const message = ref(null)
const loading = ref(false)
const loadError = ref(false)
const saving = ref(false)

function showErrors(data) {
  ElMessage.error((data['error-msg'] || []).map((c) => t(`errors.${c}`, c)).join(', '))
}

function handleRequestError(e) {
  // 401/403 are already surfaced by the axios interceptor.
  if (![401, 403].includes(e.response?.status)) ElMessage.error(t('errors.internal-server-error'))
}

async function setStatus(status, { silent = false } = {}) {
  saving.value = true
  try {
    const { data } = await setContactMessageStatus(message.value.id, status)
    if (data.status === 'SUCCESS') {
      message.value = data.result
      if (!silent) ElMessage.success(t('contact.statusChanged'))
      emit('changed')
    } else {
      showErrors(data)
    }
  } catch (e) {
    handleRequestError(e)
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  loadError.value = false
  message.value = null
  try {
    const { data } = await getContactMessage(props.messageId)
    if (data.status !== 'SUCCESS') {
      loadError.value = true
      return
    }
    message.value = data.result
    // Opening a new message means someone has read it.
    if (message.value.status === 'new' && authStore.can('contact.status')) {
      await setStatus('read', { silent: true })
    }
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.modelValue, props.messageId],
  ([open]) => {
    if (open && props.messageId !== null) load()
  },
)

async function remove() {
  try {
    await ElMessageBox.confirm(t('contact.deleteConfirm', { name: message.value.name }), t('common.delete'), {
      type: 'warning',
      confirmButtonText: t('common.delete'),
      cancelButtonText: t('common.cancel'),
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  saving.value = true
  try {
    const { data } = await deleteContactMessage(message.value.id)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t('contact.deleted'))
      emit('changed')
      emit('update:modelValue', false)
    } else {
      showErrors(data)
    }
  } catch (e) {
    handleRequestError(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    :title="t('contact.detailsTitle')"
    size="min(520px, 100vw)"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-alert v-if="loadError" :title="t('errors.internal-server-error')" type="error" show-icon :closable="false" />

    <div v-else v-loading="loading" class="details">
      <template v-if="message">
        <header class="details__head">
          <div>
            <h3 class="details__name">{{ message.name }}</h3>
            <span class="details__date">{{ formatDateTime(message['created-at'], locale) }}</span>
          </div>
          <el-tag :type="STATUS_TAG[message.status]" effect="light">{{ t(`contact.status.${message.status}`) }}</el-tag>
        </header>

        <div class="details__contacts">
          <a v-if="message.email" :href="`mailto:${message.email}`" class="details__contact">
            <el-icon><Message /></el-icon>{{ message.email }}
          </a>
          <a v-if="message.phone" :href="`tel:${message.phone.replace(/[^\d+]/g, '')}`" class="details__contact">
            <el-icon><Phone /></el-icon>{{ message.phone }}
          </a>
        </div>

        <section class="details__message">{{ message.message }}</section>

        <div v-if="authStore.can('contact.status')" class="details__status">
          <span class="details__label">{{ t('contact.changeStatus') }}</span>
          <el-radio-group
            :model-value="message.status"
            :disabled="saving"
            size="small"
            @change="setStatus"
          >
            <el-radio-button v-for="s in STATUSES" :key="s" :value="s">{{ t(`contact.status.${s}`) }}</el-radio-button>
          </el-radio-group>
        </div>

        <dl class="details__meta">
          <dt>{{ t('contact.ipAddress') }}</dt>
          <dd>{{ message['ip-address'] || '—' }}</dd>
          <dt>{{ t('contact.userAgent') }}</dt>
          <dd>{{ message['user-agent'] || '—' }}</dd>
        </dl>
      </template>
    </div>

    <template v-if="message && authStore.can('contact.delete')" #footer>
      <el-button type="danger" plain :icon="Delete" :loading="saving" @click="remove">{{ t('common.delete') }}</el-button>
    </template>
  </el-drawer>
</template>

<style scoped>
.details {
  min-height: 160px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.details__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.details__name {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
}
.details__date {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.details__contacts {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.details__contact {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 500;
}
.details__message {
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--el-fill-color-light);
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.55;
}
.details__status {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.details__label,
.details__meta dt {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}
.details__meta {
  margin: 0;
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 6px 14px;
  font-size: 12px;
}
.details__meta dd {
  margin: 0;
  word-break: break-all;
  color: var(--el-text-color-regular);
}
</style>
