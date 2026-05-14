import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
      // Lazy loading для сторінки реєстрації
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
    }
  ]
})

// Захист маршрутів: дозволяється доступ до /login та /register без авторизації
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('userId')
  
  if (to.name !== 'login' && to.name !== 'register' && !isAuthenticated) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router