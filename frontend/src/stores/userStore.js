import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    userId: localStorage.getItem('userId') || null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null,
    _fetchController: null
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
      const cachedKey = `user_data_${this.userId}`
      const cachedData = localStorage.getItem(cachedKey)
      if (cachedData) {
        try {
          this.user = JSON.parse(cachedData)
        } catch {
          localStorage.removeItem(cachedKey) // Видалення пошкодженного кешу
        }
      }

      // Якщо немає інтернету - зупинка, показ кешу
      if (!navigator.onLine) {
        this.loading = false
        return
      }

      if (this._fetchController) {
        this._fetchController.abort()
      }
      this._fetchController = new AbortController()

      try {
        const API_URL = import.meta.env.VITE_API_URL || 'https://basketball-api-kyiv.onrender.com';
        const response = await fetch(`${API_URL}/api/users/${this.userId}`, {
          signal: this._fetchController.signal,
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
        localStorage.setItem(cachedKey, JSON.stringify(freshUser))

      } catch (error) {
        if (error.name === 'AbortError') return
        
        this.error = error.message

        if (error.message === 'Токен протерміновано') {
          this.logout() // Автоматичний вихід
        }
      } finally {
        this.loading = false
      }
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