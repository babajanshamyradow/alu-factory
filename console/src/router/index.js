import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import AdminLayout from '@/layouts/AdminLayout.vue'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import UserListView from '@/views/users/UserListView.vue'
import CategoryListView from '@/views/categories/CategoryListView.vue'
import ProductListView from '@/views/products/ProductListView.vue'
import SliderListView from '@/views/slider/SliderListView.vue'
import BannerListView from '@/views/banners/BannerListView.vue'
import CompanyView from '@/views/company/CompanyView.vue'
import ContactMessageListView from '@/views/contact/ContactMessageListView.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
  {
    path: '/',
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: { name: 'dashboard' } },
      { path: 'dashboard', name: 'dashboard', component: DashboardView },
      {
        path: 'users',
        name: 'users',
        component: UserListView,
        meta: { permission: 'users.view' },
      },
      {
        path: 'categories',
        name: 'categories',
        component: CategoryListView,
        meta: { permission: 'categories.view' },
      },
      {
        path: 'products',
        name: 'products',
        component: ProductListView,
        meta: { permission: 'products.view' },
      },
      {
        path: 'slider',
        name: 'slider',
        component: SliderListView,
        meta: { permission: 'slider.view' },
      },
      {
        path: 'banners',
        name: 'banners',
        component: BannerListView,
        meta: { permission: 'banners.view' },
      },
      {
        path: 'company',
        name: 'company',
        component: CompanyView,
        meta: { permission: 'company.view' },
      },
      {
        path: 'contact-messages',
        name: 'contactMessages',
        component: ContactMessageListView,
        meta: { permission: 'contact.view' },
      },
      // New resource routes are added here.
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  // app.use(router) starts the initial navigation right away, before main.js
  // has confirmed the session — without this wait a page refresh (F5 /
  // Ctrl+R) on a protected route would always bounce to /login.
  if (!authStore.ready) {
    await authStore.restoreSession()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : undefined }
  }
  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { name: 'dashboard' }
  }
  // meta.permission is merged from parent routes; see src/permissions.js.
  if (to.meta.permission && !authStore.can(to.meta.permission)) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
