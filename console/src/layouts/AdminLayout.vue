<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Fold, Expand, Odometer, SwitchButton, ArrowDown, UserFilled, Lock, Menu, PictureFilled, Promotion, Goods, OfficeBuilding, ChatDotRound,
} from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'
import LangSwitcher from '@/components/LangSwitcher.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import BrandLogo from '@/components/BrandLogo.vue'
import { useBrandStore } from '@/stores/brand'
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'
import { useNewContactCount } from '@/composables/useNewContactCount'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const brand = useBrandStore()

const MOBILE_BREAKPOINT = 992
const isMobile = ref(window.innerWidth < MOBILE_BREAKPOINT)
const collapsed = ref(isMobile.value)

function onResize() {
  const mobile = window.innerWidth < MOBILE_BREAKPOINT
  if (mobile !== isMobile.value) {
    isMobile.value = mobile
    collapsed.value = mobile
  }
}
onMounted(() => window.addEventListener('resize', onResize))
onBeforeUnmount(() => window.removeEventListener('resize', onResize))

const activeMenu = computed(() => route.path)

const passwordDialogOpen = ref(false)

// "New contact messages" badge: polled so new website requests show up
// without a reload; the messages screen also refreshes it on changes.
const CONTACT_POLL_MS = 60000
const { newCount: newContactCount, refresh: refreshContactCount } = useNewContactCount()
let contactPollTimer = null
onMounted(() => {
  if (!authStore.can('contact.view')) return
  refreshContactCount()
  contactPollTimer = window.setInterval(refreshContactCount, CONTACT_POLL_MS)
})
onBeforeUnmount(() => window.clearInterval(contactPollTimer))

const pageTitle = computed(() => {
  const name = [...route.matched].reverse().find((r) => r.name)?.name
  return name ? t(`nav.${name}`, name) : ''
})

const displayName = computed(() => authStore.user?.fullname || authStore.user?.username || '')

const initials = computed(() => {
  const parts = displayName.value.trim().split(/\s+/).filter(Boolean)
  return parts.slice(0, 2).map((p) => p[0].toUpperCase()).join('') || '?'
})

function onMenuSelect() {
  if (isMobile.value) collapsed.value = true
}

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="admin-shell" :class="{ 'is-collapsed': collapsed, 'is-mobile': isMobile }">
    <aside class="sidebar">
      <div class="sidebar__brand">
        <BrandLogo :size="34" />
        <transition name="fade">
          <div v-if="!collapsed" class="sidebar__brand-text">
            <strong>{{ brand.displayName }}</strong>
            <span>{{ t('app.console') }}</span>
          </div>
        </transition>
      </div>

      <div v-if="!collapsed" class="sidebar__section">{{ t('nav.menu') }}</div>

      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        class="sidebar__menu"
        @select="onMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>{{ t('nav.dashboard') }}</template>
        </el-menu-item>

        <el-menu-item v-if="authStore.can('users.view')" index="/users">
          <el-icon><UserFilled /></el-icon>
          <template #title>{{ t('nav.users') }}</template>
        </el-menu-item>

        <el-menu-item v-if="authStore.can('categories.view')" index="/categories">
          <el-icon><Menu /></el-icon>
          <template #title>{{ t('nav.categories') }}</template>
        </el-menu-item>

        <el-menu-item v-if="authStore.can('products.view')" index="/products">
          <el-icon><Goods /></el-icon>
          <template #title>{{ t('nav.products') }}</template>
        </el-menu-item>

        <el-menu-item v-if="authStore.can('slider.view')" index="/slider">
          <el-icon><PictureFilled /></el-icon>
          <template #title>{{ t('nav.slider') }}</template>
        </el-menu-item>

        <el-menu-item v-if="authStore.can('banners.view')" index="/banners">
          <el-icon><Promotion /></el-icon>
          <template #title>{{ t('nav.banners') }}</template>
        </el-menu-item>

        <el-menu-item v-if="authStore.can('company.view')" index="/company">
          <el-icon><OfficeBuilding /></el-icon>
          <template #title>{{ t('nav.company') }}</template>
        </el-menu-item>

        <el-menu-item v-if="authStore.can('contact.view')" index="/contact-messages">
          <el-icon class="menu-icon" :class="{ 'has-dot': collapsed && newContactCount }"><ChatDotRound /></el-icon>
          <template #title>
            <span class="menu-title">{{ t('nav.contactMessages') }}</span>
            <span v-if="newContactCount" class="menu-badge">{{ newContactCount > 99 ? '99+' : newContactCount }}</span>
          </template>
        </el-menu-item>

        <!--
          As new admin-facing backend endpoints are added, add a matching
          <el-menu-item> here. See the "add a new endpoint" checklist in
          console/README.md.
        -->
      </el-menu>

      <div class="sidebar__footer">
        <el-tooltip :content="t('common.logout')" placement="right" :disabled="!collapsed">
          <button type="button" class="sidebar__logout" @click="handleLogout">
            <el-icon :size="18"><SwitchButton /></el-icon>
            <span v-if="!collapsed">{{ t('common.logout') }}</span>
          </button>
        </el-tooltip>
      </div>
    </aside>

    <div v-if="isMobile && !collapsed" class="sidebar-backdrop" @click="collapsed = true" />

    <div class="main">
      <header class="topbar">
        <button type="button" class="topbar__collapse" @click="collapsed = !collapsed">
          <el-icon :size="18">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
        </button>

        <h2 class="topbar__title">{{ pageTitle }}</h2>

        <div class="topbar__actions">
          <ThemeToggle />
          <LangSwitcher />
          <el-dropdown trigger="click" placement="bottom-end">
            <button type="button" class="user-chip">
              <span class="user-chip__avatar">{{ initials }}</span>
              <span class="user-chip__meta">
                <span class="user-chip__name">{{ displayName }}</span>
                <span v-if="authStore.role" class="user-chip__role">{{ authStore.role }}</span>
              </span>
              <el-icon class="user-chip__arrow"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="passwordDialogOpen = true">
                  <el-icon><Lock /></el-icon>
                  {{ t('profile.changePassword') }}
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  {{ t('common.logout') }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <ChangePasswordDialog v-model="passwordDialogOpen" />
  </div>
</template>

<style scoped>
.admin-shell {
  --sidebar-w: 248px;
  min-height: 100vh;
  display: flex;
}
.admin-shell.is-collapsed {
  --sidebar-w: 72px;
}

/* ---------- Sidebar ---------- */
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: var(--sidebar-w);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(120% 60% at 0% 0%, rgba(67, 97, 238, 0.22), transparent 60%),
    linear-gradient(180deg, var(--af-sidebar-bg) 0%, var(--af-sidebar-bg-2) 100%);
  border-right: 1px solid var(--af-sidebar-border);
  transition: width 0.22s ease;
  overflow: hidden;
  z-index: 30;
}
.sidebar__brand {
  height: 68px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 19px;
  white-space: nowrap;
}
.sidebar__brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.sidebar__brand-text strong {
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.sidebar__brand-text span {
  color: var(--af-sidebar-text);
  font-size: 12px;
}
.sidebar__section {
  padding: 18px 24px 8px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(151, 163, 194, 0.6);
  white-space: nowrap;
}
.sidebar__menu {
  --el-menu-bg-color: transparent;
  --el-menu-hover-bg-color: var(--af-sidebar-hover);
  --el-menu-text-color: var(--af-sidebar-text);
  --el-menu-active-color: var(--af-sidebar-text-active);
  --el-menu-item-height: 44px;
  --el-menu-base-level-padding: 14px;
  flex: 1;
  border-right: none;
  padding: 4px 12px;
  overflow-y: auto;
}
.sidebar__menu.el-menu--collapse {
  width: 100%;
  padding: 4px 12px;
}
.sidebar__menu :deep(.el-menu-item) {
  border-radius: 10px;
  margin-bottom: 4px;
  font-weight: 500;
  transition: background 0.2s, color 0.2s;
}
.sidebar__menu :deep(.el-menu-item.is-active) {
  background: var(--af-gradient);
  box-shadow: 0 6px 18px rgba(67, 97, 238, 0.35);
}
.sidebar__menu :deep(.el-menu-item.is-active .el-icon) {
  color: #fff;
}
.sidebar__footer {
  padding: 12px;
  border-top: 1px solid var(--af-sidebar-border);
}
.sidebar__logout {
  width: 100%;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--af-sidebar-text);
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.admin-shell:not(.is-collapsed) .sidebar__logout {
  justify-content: flex-start;
  padding: 0 14px;
}
.sidebar__logout:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
}

.menu-title {
  flex: 1;
}
.menu-badge {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--el-color-danger);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}
.menu-icon {
  position: relative;
}
.menu-icon.has-dot::after {
  content: '';
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--el-color-danger);
}

/* ---------- Main area ---------- */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 68px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 28px;
  background: var(--af-header-bg);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.topbar__collapse {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}
.topbar__collapse:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
}
.topbar__title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.topbar__actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  height: 44px;
  padding: 4px 10px 4px 4px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  background: var(--el-bg-color);
  font: inherit;
  color: inherit;
  cursor: pointer;
  transition: border-color 0.2s;
}
.user-chip:hover {
  border-color: var(--el-color-primary-light-5);
}
.user-chip__avatar {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  background: var(--af-gradient);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}
.user-chip__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.25;
}
.user-chip__name {
  font-size: 13px;
  font-weight: 600;
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-chip__role {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--el-color-primary);
}
.user-chip__arrow {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.content {
  flex: 1;
  padding: 28px;
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ---------- Mobile: sidebar becomes an off-canvas drawer ---------- */
.is-mobile .sidebar {
  position: fixed;
  left: 0;
  width: 264px;
  transform: translateX(0);
  transition: transform 0.25s ease;
  box-shadow: 12px 0 40px rgba(0, 0, 0, 0.3);
}
.is-mobile.is-collapsed .sidebar {
  transform: translateX(-100%);
  box-shadow: none;
}
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 25;
  background: rgba(8, 12, 24, 0.45);
  backdrop-filter: blur(2px);
}

@media (max-width: 768px) {
  .topbar {
    padding: 0 16px;
    gap: 10px;
  }
  .content {
    padding: 16px;
  }
  .user-chip__meta,
  .user-chip__arrow {
    display: none;
  }
  .user-chip {
    padding: 4px;
  }
}
</style>
