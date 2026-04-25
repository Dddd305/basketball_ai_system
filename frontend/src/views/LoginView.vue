<template>
  <div class="login-container">
    <div class="login-card">
      
      <div class="logo-container">
        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>
        </svg>
      </div>
      
      <h1 class="login-title">З поверненням!</h1>
      <p class="login-subtitle">Увійдіть до системи моніторингу</p>

      <button 
        v-if="showInstallButton" 
        @click.prevent="installPWA" 
        class="install-pwa-btn"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        Встановити на головний екран
      </button>

      <form @submit.prevent="login" class="login-form">
        
        <div class="form-group">
          <label>Електронна пошта</label>
          <input 
            type="email" 
            v-model="credentials.email" 
            required 
            placeholder="player@gmail.com" 
            class="input-field" 
          />
        </div>

        <div class="form-group">
          <label>Пароль</label>
          <input 
            type="password" 
            v-model="credentials.password" 
            required 
            placeholder="••••••••" 
            class="input-field" 
          />
        </div>

        <button type="submit" :disabled="isLoading" class="btn-primary">
          {{ isLoading ? 'Перевірка...' : 'Увійти' }}
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
import { ref, onMounted, onUnmounted } from 'vue' // ДОДАНО: onMounted та onUnmounted
import { useRouter } from 'vue-router'

const router = useRouter()
const credentials = ref({ email: '', password: '' })
const errorMessage = ref('')
const isLoading = ref(false)

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
  // ДОДАНО: Авто-вхід для PWA
  const savedUserId = localStorage.getItem('userId')
  if (savedUserId) {
    console.log('Знайдено активну сесію. Автоматичний вхід...')
    router.push('/dashboard')
    return // Зупиняємо виконання подальшого коду
  }

  // Твій існуючий код для кнопки PWA
  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
})
// ==========================================

const login = async () => {
  isLoading.value = true
  errorMessage.value = ''

  // ==========================================
  // ДОДАНО: РОЗУМНИЙ ОФЛАЙН-ЛОГІН
  // ==========================================
  if (!navigator.onLine) {
    // 1. Перевіряємо, чи є в пам'яті збережений ID користувача
    const savedUserId = localStorage.getItem('userId')

    if (savedUserId) {
      // 2. Якщо ID є, імітуємо успішний логін і пускаємо на Дашборд
      console.log('🌐 Офлайн режим: Знайдено збережену сесію.')
      router.push('/dashboard')
    } else {
      // 3. Якщо ID немає (взагалі перший вхід на цьому пристрої)
      errorMessage.value = 'Немає підключення. Для першого входу потрібен Інтернет.'
    }
    
    isLoading.value = false
    return // Зупиняємо функцію, щоб не робити запит на сервер!
  }
  // ==========================================

  // --- Стандартний логін (якщо Інтернет Є) ---
  try {
    const response = await fetch('https://basketball-api-kyiv.onrender.com/api/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials.value)
    })

    const data = await response.json()

    if (response.ok) {
      // Успішний вхід: зберігаємо ID у пам'ять для майбутніх офлайн-сесій
      localStorage.setItem('userId', data.user_id)
      router.push('/dashboard')
    } else {
      errorMessage.value = data.detail || 'Помилка авторизації'
    }
  } catch (error) {
    // 🛡 ПІДСТРАХОВКА: Якщо fetch впав через мережу (навіть якщо navigator.onLine брехав)
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      const savedUserId = localStorage.getItem('userId')
      
      if (savedUserId) {
        console.log('🌐 Збій мережі: Переходимо в офлайн режим за збереженою сесією.')
        router.push('/dashboard')
        return
      } else {
        errorMessage.value = 'Мережа недоступна. Потрібен інтернет для першого входу.'
        return
      }
    }
    
    // Якщо помилка не пов'язана з інтернетом
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
  margin: 0 0 20px 0; /* Трохи зменшив відступ, бо тепер є кнопка PWA */
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