<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

import { createUser, updateUser } from '@/api/users'
import { ROLES } from '@/permissions'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // null → create mode, otherwise the user being edited.
  user: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const { t } = useI18n()
const authStore = useAuthStore()

const MIN_PASSWORD_LENGTH = 6

const formRef = ref()
const saving = ref(false)
const form = reactive({ username: '', fullname: '', email: '', role: 'operator', password: '' })

const isEdit = computed(() => !!props.user)
const isSelf = computed(() => props.user?.username === authStore.user?.username)

// Only a superuser may grant the superuser role (backend enforces it too).
const roleOptions = computed(() =>
  ROLES.filter((r) => r !== 'superuser' || authStore.role === 'superuser'),
)

const rules = computed(() => ({
  username: [
    { required: true, message: t('users.usernameRequired'), trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_.-]{3,64}$/, message: t('errors.username-invalid'), trigger: 'blur' },
  ],
  fullname: [{ required: true, message: t('users.fullnameRequired'), trigger: 'blur' }],
  email: [{ type: 'email', message: t('errors.email-invalid'), trigger: 'blur' }],
  role: [{ required: true, trigger: 'change' }],
  password: [
    { required: true, message: t('users.passwordRequired'), trigger: 'blur' },
    { min: MIN_PASSWORD_LENGTH, message: t('errors.password-too-short'), trigger: 'blur' },
  ],
}))

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, {
      username: props.user?.username ?? '',
      fullname: props.user?.fullname ?? '',
      email: props.user?.email ?? '',
      role: props.user?.role ?? 'operator',
      password: '',
    })
    formRef.value?.clearValidate()
  },
)

function close() {
  emit('update:modelValue', false)
}

async function submit() {
  if (!(await formRef.value.validate().catch(() => false))) return

  saving.value = true
  try {
    const payload = { fullname: form.fullname, email: form.email || null, role: form.role }
    const { data } = isEdit.value
      ? await updateUser(props.user.username, payload)
      : await createUser({ ...payload, username: form.username, password: form.password })

    if (data.status === 'SUCCESS') {
      ElMessage.success(t(isEdit.value ? 'users.updated' : 'users.created'))
      emit('saved', data.result)
      close()
    } else {
      ElMessage.error((data['error-msg'] || []).map((c) => t(`errors.${c}`, c)).join(', '))
    }
  } catch (e) {
    // 401/403 are already surfaced by the axios interceptor.
    if (![401, 403].includes(e.response?.status)) ElMessage.error(t('errors.internal-server-error'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? t('users.editTitle') : t('users.addTitle')"
    width="min(480px, 92vw)"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item :label="t('users.username')" prop="username">
        <el-input v-model="form.username" :disabled="isEdit" autocomplete="off" />
      </el-form-item>
      <el-form-item :label="t('users.fullname')" prop="fullname">
        <el-input v-model="form.fullname" maxlength="64" />
      </el-form-item>
      <el-form-item :label="t('users.email')" prop="email">
        <el-input v-model="form.email" type="email" />
      </el-form-item>
      <el-form-item :label="t('users.role')" prop="role">
        <el-select v-model="form.role" :disabled="isSelf" style="width: 100%">
          <el-option v-for="r in roleOptions" :key="r" :value="r" :label="t(`roles.${r}`)" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="!isEdit" :label="t('users.password')" prop="password">
        <el-input v-model="form.password" type="password" show-password autocomplete="new-password" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="close">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="saving" @click="submit">{{ t('common.save') }}</el-button>
    </template>
  </el-dialog>
</template>
