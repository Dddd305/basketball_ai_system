<template>
  <div class="auth-container">
    <div class="auth-card">
      
      <div class="logo-container" style="display: flex; justify-content: center; margin-bottom: 10px;">
        <Dribbble :size="56" color="#ff9800" stroke-width="1.5" />
      </div>
      
      <h1 class="auth-title">Новий гравець</h1>
      <p class="auth-subtitle">Створіть свій профіль для початку</p>

      <form @submit.prevent="register" class="auth-form">
        
        <div class="form-group">
          <label>Ім'я</label>
          <input 
            type="text" 
            v-model="formData.name" 
            required 
            class="input-field" 
          />
        </div>

        <div class="form-group">
          <label>Електронна пошта</label>
          <input 
            type="email" 
            v-model="formData.email" 
            required  
            class="input-field" 
          />
        </div>

        <div class="form-group">
          <label>Пароль</label>
          <div style="position: relative; display: flex; align-items: center;">
            <input 
              :type="showPassword ? 'text' : 'password'" 
              v-model="formData.password" 
              required 
              minlength="6"
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

        <div class="form-row">
          <div class="form-group">
            <label>Вік</label>
            <input type="number" v-model="formData.age" required min="10" max="60" class="input-field" />
          </div>
          <div class="form-group">
            <label>Позиція</label>
            <select v-model="formData.position" required class="input-field">
              <option value="PG">PG (Розігруючий)</option>
              <option value="SG">SG (Атакуючий)</option>
              <option value="SF">SF (Легкий форвард)</option>
              <option value="PF">PF (Важкий форвард)</option>
              <option value="C">C (Центровий)</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Зріст (см)</label>
            <input type="number" v-model="formData.height_cm" required min="120" max="250" class="input-field" />
          </div>
          <div class="form-group">
            <label>Вага (кг)</label>
            <input type="number" v-model="formData.weight_kg" required min="30" max="150" class="input-field" />
          </div>
        </div>

        <button type="submit" :disabled="isLoading" class="btn-primary">
          <span v-if="isLoading">
            <Loader2 class="animate-spin" :size="18" style="vertical-align: middle; margin-right: 5px;" />
            Створення...
          </span>
          <span v-else>Зареєструватися</span>
        </button>
      </form>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <div class="login-link">
        Вже маєте акаунт? 
        <router-link to="/" class="link">Увійти</router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Dribbble, Eye, EyeOff, Loader2 } from 'lucide-vue-next'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const userStore = useUserStore()
const showPassword = ref(false)

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const isLoading = ref(false)
const errorMessage = ref('')

// Дані форми з оптимізованими дефолтними значеннями
const formData = ref({
  name: '',
  email: '',
  password: '',
  age: '',
  position: '',
  height_cm: '',
  weight_kg: ''
})

const register = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const API_URL = import.meta.env.VITE_API_URL || 'https://basketball-api-kyiv.onrender.com';
    const response = await fetch(`${API_URL}/api/users/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData.value) 
    })

    const data = await response.json()

    if (response.ok) {
      userStore.setAuthData(data.user_id, data.access_token)
      router.push('/dashboard')
    } else {
      errorMessage.value = data.detail || 'Помилка реєстрації. Перевірте дані.'
    }
  } catch (error) {
    errorMessage.value = 'Помилка підключення до сервера.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #121212;
  padding: 20px;
}

.auth-card {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 16px;
  padding: 30px;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  text-align: center;
}

.logo-container {
  margin-bottom: 15px;
  display: flex;
  justify-content: center;
}

.logo-container svg {
  color: #ff9800;
}

.auth-title {
  margin: 0 0 5px 0;
  color: #fff;
  font-size: 1.6em;
}

.auth-subtitle {
  color: #b0bec5;
  margin: 0 0 25px 0;
  font-size: 0.9em;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  text-align: left;
}

.form-row {
  display: flex;
  gap: 15px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  color: #b0bec5;
  font-size: 0.85em;
  font-weight: bold;
}

.input-field {
  background: #121212;
  color: #fff;
  border: 1px solid #333;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 0.95em;
  transition: border-color 0.3s;
  color-scheme: dark;
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
  font-size: 1.05em;
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
  margin-top: 15px;
  color: #ff5252;
  background: rgba(255, 82, 82, 0.1);
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 82, 82, 0.3);
  font-size: 0.9em;
}

.login-link {
  margin-top: 20px;
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