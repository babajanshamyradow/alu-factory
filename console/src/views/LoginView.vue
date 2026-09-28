<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { User, Lock, Right } from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'
import LangSwitcher from '@/components/LangSwitcher.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import BrandLogo from '@/components/BrandLogo.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const submitting = ref(false)
const serverError = ref('')

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: () => t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: () => t('login.passwordRequired'), trigger: 'blur' }],
}

async function handleSubmit() {
  serverError.value = ''
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const { success, errors } = await authStore.login(form.username, form.password)
    if (success) {
      const redirect = route.query.redirect
      router.push(typeof redirect === 'string' ? redirect : { name: 'dashboard' })
    } else {
      const code = errors[0] || 'internal-server-error'
      serverError.value = t(`errors.${code}`, code)
    }
  } catch {
    serverError.value = t('errors.internal-server-error')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- Brand panel -->
    <section class="brand-panel">
      <div class="brand-panel__grid" />
      <div class="brand-panel__glow brand-panel__glow--a" />
      <div class="brand-panel__glow brand-panel__glow--b" />

      <div class="brand-panel__top">
        <BrandLogo :size="40" />
        <span class="brand-panel__name">Alu-Factory</span>
      </div>

      <div class="brand-panel__body">
        <h2>{{ t('login.brandTitle') }}</h2>
        <p>{{ t('login.brandText') }}</p>
      </div>

      <div class="brand-panel__footer">© {{ new Date().getFullYear() }} Alu-Factory</div>
    </section>

    <!-- Form panel -->
    <section class="form-panel">
      <div class="form-panel__toolbar">
        <ThemeToggle />
        <LangSwitcher />
      </div>

      <div class="form-panel__inner">
        <div class="form-panel__mobile-brand">
          <BrandLogo :size="44" />
        </div>

        <h1 class="form-panel__title">{{ t('login.title') }}</h1>
        <p class="form-panel__subtitle">{{ t('login.subtitle') }}</p>

        <transition name="shake">
          <el-alert
            v-if="serverError"
            :title="serverError"
            type="error"
            show-icon
            :closable="false"
            class="form-panel__error"
          />
        </transition>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          class="login-form"
          @keyup.enter="handleSubmit"
        >
          <el-form-item :label="t('login.username')" prop="username">
            <el-input
              v-model="form.username"
              :placeholder="t('login.username')"
              :prefix-icon="User"
              autocomplete="username"
              autofocus
            />
          </el-form-item>
          <el-form-item :label="t('login.password')" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              :placeholder="t('login.password')"
              :prefix-icon="Lock"
              autocomplete="current-password"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-form__submit"
            :loading="submitting"
            @click="handleSubmit"
          >
            {{ t('login.submit') }}
            <el-icon v-if="!submitting" class="el-icon--right"><Right /></el-icon>
          </el-button>
        </el-form>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  background: var(--el-bg-color);
}

/* ---------- Brand panel ---------- */
.brand-panel {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px 56px;
  color: #fff;
  background: linear-gradient(160deg, #0f1629 0%, #16214a 55%, #1b3a8a 100%);
}
.brand-panel__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse at 30% 40%, #000 20%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at 30% 40%, #000 20%, transparent 75%);
}
.brand-panel__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.55;
  animation: float 14s ease-in-out infinite alternate;
}
.brand-panel__glow--a {
  width: 420px;
  height: 420px;
  top: -120px;
  right: -100px;
  background: #4361ee;
}
.brand-panel__glow--b {
  width: 360px;
  height: 360px;
  bottom: -140px;
  left: -80px;
  background: #4cc9f0;
  opacity: 0.35;
  animation-delay: -7s;
}
@keyframes float {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(30px, 40px) scale(1.1); }
}
.brand-panel__top,
.brand-panel__body,
.brand-panel__footer {
  position: relative;
  z-index: 1;
}
.brand-panel__top {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-panel__name {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.brand-panel__body {
  max-width: 460px;
}
.brand-panel__body h2 {
  margin: 0 0 16px;
  font-size: clamp(30px, 3.2vw, 44px);
  line-height: 1.1;
  font-weight: 800;
  background: linear-gradient(90deg, #fff 0%, #c7d5ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.brand-panel__body p {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
  color: rgba(226, 232, 255, 0.72);
}
.brand-panel__footer {
  font-size: 13px;
  color: rgba(226, 232, 255, 0.5);
}

/* ---------- Form panel ---------- */
.form-panel {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 88px 24px 48px;
}
.form-panel__toolbar {
  position: absolute;
  top: 24px;
  right: 24px;
  display: flex;
  gap: 10px;
}
.form-panel__inner {
  width: 100%;
  max-width: 380px;
  animation: rise 0.45s ease both;
}
@keyframes rise {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; }
}
.form-panel__mobile-brand {
  display: none;
  margin-bottom: 24px;
}
.form-panel__title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 800;
}
.form-panel__subtitle {
  margin: 0 0 28px;
  font-size: 15px;
  color: var(--el-text-color-secondary);
}
.form-panel__error {
  margin-bottom: 20px;
  border-radius: 10px;
}
.login-form :deep(.el-form-item__label) {
  font-weight: 600;
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.login-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 1px 14px;
}
.login-form__submit {
  width: 100%;
  margin-top: 8px;
  height: 48px;
  border: 0;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  background: var(--af-gradient);
  transition: transform 0.15s, box-shadow 0.2s, filter 0.2s;
}
.login-form__submit:hover {
  filter: brightness(1.06);
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(67, 97, 238, 0.38);
}

.shake-enter-active {
  animation: shake 0.4s;
}
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .brand-panel {
    display: none;
  }
  .form-panel {
    background:
      radial-gradient(80% 50% at 50% 0%, var(--el-color-primary-light-9), transparent 70%),
      var(--el-bg-color);
  }
  .form-panel__mobile-brand {
    display: block;
  }
  .form-panel__toolbar {
    top: 16px;
    right: 16px;
  }
}
</style>
