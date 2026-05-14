<template>
  <div class="login-container">
    <div class="login-card">
      
      <div class="logo-container" style="display: flex; justify-content: center; margin-bottom: 15px;">
        <Dribbble :size="64" color="#ff9800" stroke-width="1.5" />
      </div>
      
      <h1 class="login-title">З поверненням!</h1>
      <p class="login-subtitle">Увійдіть до системи моніторингу</p>

      <button 
        v-if="showInstallButton" 
        @click.prevent="installPWA" 
        class="install-pwa-btn"
      >
        <Download :size="20" style="margin-right: 8px;" />
        Встановити на головний екран
      </button>

      <form @submit.prevent="login" class="login-form">
        
        <div class="form-group">
          <label>Електронна пошта</label>
          <input 
            type="email" 
            v-model="credentials.email" 
            required 
            class="input-field" 
          />
        </div>

        <div class="form-group">
          <label>Пароль</label>
          <div style="position: relative; display: flex; align-items: center;">
            <input 
              :type="showPassword ? 'text' : 'password'" 
              v-model="credentials.password" 
              required 
              class="input-field" 
              style="width: 100%; padding-right: 40px; box-sizing: border-box;"
            />
            <button 
              type="button" 
              @click="togglePassword" 
              style="position: absolute; right: 10px; background: none; border: none; color: #b0bec5; cursor: pointer; padding: 0; display: flex; align-items: center;"
            >
              <EyeOff v-if="showPassword" :size="20" />
              <Eye v-else :size="20" />
            </button>
          </div>
        </div>

        <button type="submit" :disabled="isLoading" class="btn-primary">
          <span v-if="isLoading">
            <Loader2 class="animate-spin" :size="18" style="vertical-align: middle; margin-right: 5px;" />
            Перевірка...
          </span>
          <span v-else>Увійти</span>
        </button>
      </form>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <div class="register-link">
        Ще немає акаунту? 
        <router-link to="/register" class="link">Зареєструватися</router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue' 
import { useRouter } from 'vue-router'
import { Dribbble, Eye, EyeOff, Loader2, Download } from 'lucide-vue-next'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const userStore = useUserStore()
const credentials = ref({ email: '', password: '' })
const errorMessage = ref('')
const isLoading = ref(false)

// Логіка видимості пароля
const showPassword = ref(false)
const togglePassword = () => {
  showPassword.value = !showPassword.value
}

// ==========================================
// --- ЛОГІКА ВСТАНОВЛЕННЯ PWA ---
// ==========================================
const deferredPrompt = ref(null)
const showInstallButton = ref(false)

const handleBeforeInstallPrompt = (e) => {
  e.preventDefault()
  deferredPrompt.value = e
  showInstallButton.value = true
}

const installPWA = async () => {
  if (!deferredPrompt.value) return
  
  deferredPrompt.value.prompt()
  const { outcome } = await deferredPrompt.value.userChoice
  
  if (outcome === 'accepted') {
    console.log('Користувач встановив додаток!')
  }
  
  deferredPrompt.value = null
  showInstallButton.value = false
}

onMounted(() => {
  const savedUserId = localStorage.getItem('userId')
  if (savedUserId) {
    console.log('Знайдено активну сесію. Автоматичний вхід...')
    router.push('/dashboard')
    return 
  }

  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
})
// ==========================================

const login = async () => {
  isLoading.value = true
  errorMessage.value = ''

  // РОЗУМНИЙ ОФЛАЙН-ЛОГІН
  if (!navigator.onLine) {
    const savedUserId = localStorage.getItem('userId')

    if (savedUserId) {
      console.log('Офлайн режим: Знайдено збережену сесію.')
      router.push('/dashboard')
    } else {
      errorMessage.value = 'Немає підключення. Для першого входу потрібен Інтернет.'
    }
    
    isLoading.value = false
    return 
  }

  // Стандартний логін
  try {
    const API_URL = import.meta.env.VITE_API_URL || 'https://basketball-api-kyiv.onrender.com';
    console.log('Спроба входу. API_URL:', API_URL);
    const response = await fetch(`${API_URL}/api/users/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials.value)
    })

    const data = await response.json()

    if (response.ok) {
      userStore.setAuthData(data.user_id, data.access_token)
      router.push('/dashboard')
    } else {
      errorMessage.value = data.detail || 'Помилка авторизації'
    }
  } catch (error) {
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      const savedUserId = localStorage.getItem('userId')
      
      if (savedUserId) {
        console.log('Збій мережі: Переходимо в офлайн режим.')
        router.push('/dashboard')
        return
      } else {
        errorMessage.value = 'Мережа недоступна. Потрібен інтернет для першого входу.'
        return
      }
    }
    
    errorMessage.value = 'Помилка підключення до сервера'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #121212;
  padding: 20px;
}

.login-card {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 16px;
  padding: 40px 30px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  text-align: center;
}

.logo-container {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

.logo-container svg {
  color: #ff9800;
}

.login-title {
  margin: 0 0 10px 0;
  color: #fff;
  font-size: 1.8em;
}

.login-subtitle {
  color: #b0bec5;
  margin: 0 0 20px 0;
  font-size: 0.9em;
}

/* ДОДАНО: Стилі для кнопки PWA */
.install-pwa-btn {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  background: rgba(255, 152, 0, 0.1);
  color: #ff9800;
  border: 1px solid #ff9800;
  padding: 12px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 25px;
  transition: all 0.3s ease;
}

.install-pwa-btn:hover {
  background: rgba(255, 152, 0, 0.2);
  transform: translateY(-2px);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  text-align: left;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #b0bec5;
  font-size: 0.9em;
  font-weight: bold;
}

.input-field {
  background: #121212;
  color: #fff;
  border: 1px solid #333;
  padding: 12px 15px;
  border-radius: 8px;
  font-size: 1em;
  transition: border-color 0.3s;
}

.input-field:focus {
  outline: none;
  border-color: #ff9800;
}

.btn-primary {
  background: #ff9800;
  color: #000;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-weight: bold;
  font-size: 1.1em;
  cursor: pointer;
  transition: background 0.3s;
  margin-top: 10px;
}

.btn-primary:hover:not(:disabled) {
  background: #f57c00;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-message {
  margin-top: 20px;
  color: #ff5252;
  background: rgba(255, 82, 82, 0.1);
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 82, 82, 0.3);
  font-size: 0.9em;
}

.register-link {
  margin-top: 25px;
  color: #b0bec5;
  font-size: 0.9em;
}

.link {
  color: #ff9800;
  text-decoration: none;
  font-weight: bold;
}

.link:hover {
  text-decoration: underline;
}
</style>