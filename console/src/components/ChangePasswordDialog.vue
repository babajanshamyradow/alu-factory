<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

import { changeOwnPassword } from '@/api/users'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const { t } = useI18n()

const MIN_PASSWORD_LENGTH = 6

const formRef = ref()
const saving = ref(false)
const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })

const rules = computed(() => ({
  oldPassword: [{ required: true, message: t('users.passwordRequired'), trigger: 'blur' }],
  newPassword: [
    { required: true, message: t('users.passwordRequired'), trigger: 'blur' },
    { min: MIN_PASSWORD_LENGTH, message: t('errors.password-too-short'), trigger: 'blur' },
  ],
  confirmPassword: [
    {
      validator: (_, value, cb) =>
        value === form.newPassword ? cb() : cb(new Error(t('profile.passwordMismatch'))),
      trigger: 'blur',
    },
  ],
}))

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, { oldPassword: '', newPassword: '', confirmPassword: '' })
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
    const { data } = await changeOwnPassword(form.oldPassword, form.newPassword)
    if (data.status === 'SUCCESS') {
      ElMessage.success(t('profile.passwordChanged'))
      close()
    } else {
      ElMessage.error((data['error-msg'] || []).map((c) => t(`errors.${c}`, c)).join(', '))
    }
  } catch (e) {
    if (e.response?.status !== 401) ElMessage.error(t('errors.internal-server-error'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="t('profile.changePassword')"
    width="min(420px, 92vw)"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item :label="t('profile.oldPassword')" prop="oldPassword">
        <el-input v-model="form.oldPassword" type="password" show-password autocomplete="current-password" />
      </el-form-item>
      <el-form-item :label="t('profile.newPassword')" prop="newPassword">
        <el-input v-model="form.newPassword" type="password" show-password autocomplete="new-password" />
      </el-form-item>
      <el-form-item :label="t('profile.confirmPassword')" prop="confirmPassword">
        <el-input v-model="form.confirmPassword" type="password" show-password autocomplete="new-password" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="close">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="saving" @click="submit">{{ t('common.save') }}</el-button>
    </template>
  </el-dialog>
</template>
