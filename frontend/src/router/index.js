import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes: [
    {
      path: '/',
      name: 'login',
      component: LoginView,
      meta: { hideBottomNav: true } 
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { hideBottomNav: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue')
    },
    {
      path: '/activity',
      name: 'activity',
      component: () => import('../views/ActivityView.vue')
    },
    {
      path: '/gear',
      name: 'gear',
      component: () => import('../views/GearView.vue')
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue')
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      redirect: { name: 'dashboard' }
    }
  ]
})

const GUEST_ROUTES = ['login', 'register']

router.beforeEach((to, from) => {
  const isAuthenticated = !!localStorage.getItem('userId')
  const isGuestRoute = GUEST_ROUTES.includes(to.name)
  
  if (!isGuestRoute && !isAuthenticated) {
    return { name: 'login' }
  }
  
  if (isGuestRoute && isAuthenticated) {
    return { name: 'dashboard' }
  }

  return true
})

export default router