<template>
  <div class="auth-container">
    <div class="auth-card">
      
      <div class="logo-container">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
          <circle cx="8.5" cy="7" r="4"></circle>
          <line x1="20" y1="8" x2="20" y2="14"></line>
          <line x1="23" y1="11" x2="17" y2="11"></line>
        </svg>
      </div>
      
      <h1 class="auth-title">Новий гравець</h1>
      <p class="auth-subtitle">Створіть свій профіль для початку</p>

      <form @submit.prevent="register" class="auth-form">
        
        <div class="form-group">
          <label>Ім'я та Прізвище</label>
          <input 
            type="text" 
            v-model="formData.name" 
            required 
            placeholder="Напр: Дмитро" 
            class="input-field" 
          />
        </div>

        <div class="form-group">
          <label>Електронна пошта</label>
          <input 
            type="email" 
            v-model="formData.email" 
            required 
            placeholder="player@gmail.com" 
            class="input-field" 
          />
        </div>

        <div class="form-group">
          <label>Пароль</label>
          <input 
            type="password" 
            v-model="formData.password" 
            required 
            placeholder="Мінімум 6 символів" 
            minlength="6"
            class="input-field" 
          />
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
          {{ isLoading ? 'Створення...' : 'Зареєструватися' }}
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

const router = useRouter()
const isLoading = ref(false)
const errorMessage = ref('')

// Дані форми за замовчуванням
const formData = ref({
  name: '',
  email: '',
  password: '',
  age: 20,
  position: 'PG',
  height_cm: 185,
  weight_kg: 80
})

const register = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch('/api/users/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData.value)
    })

    const data = await response.json()

    if (response.ok) {
      // Якщо успішно - відразу логінимо користувача (зберігаємо отриманий ID)
      localStorage.setItem('userId', data.user_id)
      // Переходимо на Dashboard
      router.push('/dashboard')
    } else {
      // Якщо помилка (наприклад, Email зайнятий)
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