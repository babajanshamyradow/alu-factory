import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/HomeView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView, meta: { titleKey: 'nav.home' } },
  { path: '/products', name: 'catalog', component: () => import('@/views/CatalogView.vue'), meta: { titleKey: 'nav.catalog' } },
  { path: '/products/:slug', name: 'product', component: () => import('@/views/ProductView.vue') },
  { path: '/about', name: 'about', component: () => import('@/views/AboutView.vue'), meta: { titleKey: 'nav.about' } },
  { path: '/contact', name: 'contact', component: () => import('@/views/ContactView.vue'), meta: { titleKey: 'nav.contact' } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue'), meta: { titleKey: 'notFound.title' } },
]

// Scrolling is handled by App.vue after the page transition finishes
// (see onAfterLeave), so the old page doesn't jump before fading out.
export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => false,
})
