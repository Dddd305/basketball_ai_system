import { defineStore } from 'pinia'


export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    userId: localStorage.getItem('userId') || null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token && !!state.userId,
    hasMetrics: (state) => state.user?.metrics && state.user.metrics.length > 0,
  },

  actions: {
    async fetchUser() {
      if (!this.userId || !this.token) return

      this.loading = true
      this.error = null

      // Офлайн-кеш (миттєве завантаження)
      const cachedData = localStorage.getItem(`user_data_${this.userId}`)
      if (cachedData) {
        this.user = JSON.parse(cachedData)
      }

      // Оновлення з сервера (з JWT токеном)
      if (navigator.onLine) {
        try {
           const API_URL = import.meta.env.VITE_API_URL || 'https://basketball-api-kyiv.onrender.com';
           const response = await fetch(`${API_URL}/api/users/${this.userId}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            }
          })

          if (response.status === 401) {
            throw new Error('Токен протерміновано')
          }

          if (!response.ok) throw new Error('Помилка мережі')

          const freshUser = await response.json()
          this.user = freshUser
          
          // Оновлення кешу
          localStorage.setItem(`user_data_${this.userId}`, JSON.stringify(freshUser))
        } catch (error) {
          console.error('Помилка синхронізації:', error.message)
          if (error.message === 'Токен протерміновано') {
            this.logout() // Автоматичний вихід, якщо токен більше не дійсний
          }
        }
      }
      this.loading = false
    },

    setAuthData(userId, token) {
      this.userId = userId
      this.token = token
      localStorage.setItem('userId', userId)
      localStorage.setItem('token', token)
    },

    logout() {
      const cachedKey = `user_data_${this.userId}`;
      
      this.user = null;
      this.userId = null;
      this.token = null;
      
      localStorage.removeItem('userId');
      localStorage.removeItem('token');
      localStorage.removeItem(cachedKey);
    }
  }
})