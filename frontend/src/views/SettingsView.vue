<template>
  <div class="view-container">
    <header class="header">
      <h1 class="header-title" style="display: flex; align-items: center; gap: 8px;">
        <Settings class="title-icon" :size="28" />
        Налаштування
      </h1>
    </header>

    <div v-if="loading" class="loading-state" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 50vh;">
      <Loader2 class="animate-spin" :size="24" color="#ff9800" />
      <p style="margin: 0; color: #b0bec5; font-size: 1.1em;">Завантаження даних з сервера...</p>
    </div>

    <div v-else-if="user">
      
      <nav class="tabs-nav">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'profile' }" 
          @click="activeTab = 'profile'"
        >
          <Mail :size="18" /> 
          <span>Дані</span>
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'security' }" 
          @click="activeTab = 'security'"
        >
          <Lock :size="18" /> 
          <span>Безпека</span>
        </button>
        <button 
          class="tab-btn danger-tab" 
          :class="{ 'active-danger': activeTab === 'danger' }" 
          @click="activeTab = 'danger'"
        >
          <AlertTriangle :size="18" />
          <span>Видалення</span>
        </button>
      </nav>

      <div v-if="activeTab === 'profile'" class="card form-card">
        <h2 class="form-title">Особисті дані</h2>
        
        <div class="info-banner">
          <span class="info-label">Поточний Email:</span>
          <strong class="info-value">{{ user.email }}</strong>
        </div>

        <form @submit.prevent="updateEmail" class="settings-form">
          <div class="form-group full-width">
            <label>Нова електронна адреса:</label>
            <input 
              type="email" 
              v-model="emailForm.new_email" 
              required 
              class="input-field" 
            />
          </div>
          <button type="submit" :disabled="isUpdatingEmail" class="btn-primary">
            <Loader2 v-if="isUpdatingEmail" class="animate-spin" :size="18" style="margin-right: 8px;" />
            {{ isUpdatingEmail ? 'Оновлюю...' : 'Оновити Email' }}
          </button>
        </form>
      </div>

      <div v-if="activeTab === 'security'" class="card form-card">
        <h2 class="form-title">Безпека акаунта</h2>
        <form @submit.prevent="updatePassword" class="settings-form">
          
          <div class="form-group full-width">
            <label>Поточний пароль:</label>
            <div class="password-wrapper">
              <input 
                :type="showOldPassword ? 'text' : 'password'" 
                v-model="passwordForm.old_password" 
                required 
                class="input-field password-input" 
              />
              <button type="button" @click="toggleOldPassword" class="btn-toggle-password">
                <EyeOff v-if="showOldPassword" :size="20" />
                <Eye v-else :size="20" />
              </button>
            </div>
          </div>

          <div class="form-group full-width">
            <label>Новий пароль:</label>
            <div class="password-wrapper">
              <input 
                :type="showNewPassword ? 'text' : 'password'" 
                v-model="passwordForm.new_password" 
                required 
                class="input-field password-input" 
              />
              <button type="button" @click="toggleNewPassword" class="btn-toggle-password">
                <EyeOff v-if="showNewPassword" :size="20" />
                <Eye v-else :size="20" />
              </button>
            </div>
          </div>

          <div class="form-group full-width">
            <label>Підтвердіть новий пароль:</label>
            <div class="password-wrapper">
              <input 
                :type="showConfirmPassword ? 'text' : 'password'" 
                v-model="passwordForm.confirm_password" 
                required 
                class="input-field password-input" 
              />
              <button type="button" @click="toggleConfirmPassword" class="btn-toggle-password">
                <EyeOff v-if="showConfirmPassword" :size="20" />
                <Eye v-else :size="20" />
              </button>
            </div>
          </div>

          <button type="submit" :disabled="isUpdatingPassword" class="btn-primary">
            <Loader2 v-if="isUpdatingPassword" class="animate-spin" :size="18" style="margin-right: 8px;" />
            {{ isUpdatingPassword ? 'Зберігаю...' : 'Змінити пароль' }}
          </button>
        </form>
      </div>

      <div v-if="activeTab === 'danger'" class="card danger-card">
        <div style="display: flex; justify-content: center; margin-bottom: 15px; color: #e65100;">
          <AlertTriangle :size="48" />
        </div>
        <h2 class="form-title" style="text-align: center; color: #fff;">Видалення акаунта</h2>
        <p class="warning-text" style="text-align: center; margin-bottom: 20px; color: #fff;">
          Ця дія є незворотною. Всі ваші тренування, показники готовності та дані інвентарю будуть назавжди видалені з системи.
        </p>
        <button @click="confirmDeleteAccount" class="btn-danger">
          <Trash2 :size="18" style="margin-right: 8px;" />
          Видалити мій акаунт
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue' // ДОДАНО: імпорт watch
import { useRouter } from 'vue-router'
import { Settings, Mail, Lock, AlertTriangle, Trash2, Loader2, Eye, EyeOff } from 'lucide-vue-next'
import { useUserStore } from '../stores/userStore'
import { storeToRefs } from 'pinia'

const router = useRouter()
const userStore = useUserStore()

const { user, loading, userId, token } = storeToRefs(userStore)

const BASE_API = import.meta.env.VITE_API_URL || 'https://basketball-api-kyiv.onrender.com'

const activeTab = ref(sessionStorage.getItem('settings_tab') || 'profile')

watch(activeTab, (newTab) => {
  sessionStorage.setItem('settings_tab', newTab)
})

const emailForm = ref({ new_email: '' })
const passwordForm = ref({ old_password: '', new_password: '', confirm_password: '' })

const isUpdatingEmail = ref(false)
const isUpdatingPassword = ref(false)

const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const toggleOldPassword = () => { showOldPassword.value = !showOldPassword.value }
const toggleNewPassword = () => { showNewPassword.value = !showNewPassword.value }
const toggleConfirmPassword = () => { showConfirmPassword.value = !showConfirmPassword.value }

const updateEmail = async () => {
  if (!navigator.onLine) {
    alert('Відсутнє підключення. Оновлення наразі недоступне в офлайн-режимі.')
    return
  }

  isUpdatingEmail.value = true
  try {
    const response = await fetch(`${BASE_API}/api/users/me/change-email`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.value}`
      },
      body: JSON.stringify(emailForm.value)
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Помилка оновлення')
    
    await userStore.fetchUser()
    emailForm.value.new_email = ''
    alert('Електронну адресу успішно оновлено')
  } catch (e) {
    alert(e.message)
  } finally {
    isUpdatingEmail.value = false
  }
}

const updatePassword = async () => {
  if (!navigator.onLine) {
    alert('Відсутнє підключення. Оновлення наразі недоступне в офлайн-режимі.')
    return
  }

  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    alert('Нові паролі не співпадають! Будь ласка, перевірте правильність введення.')
    return
  }

  isUpdatingPassword.value = true
  try {
    const response = await fetch(`${BASE_API}/api/users/me/change-password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.value}`
      },
      body: JSON.stringify({
        old_password: passwordForm.value.old_password,
        new_password: passwordForm.value.new_password
      })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Помилка доступу')
    
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
    showOldPassword.value = false
    showNewPassword.value = false
    showConfirmPassword.value = false
    alert('Пароль успішно змінено')
  } catch (e) {
    alert(e.message)
  } finally {
    isUpdatingPassword.value = false
  }
}

const confirmDeleteAccount = async () => {
  if (!navigator.onLine) {
    alert('Відсутнє підключення. Видалення наразі недоступне в офлайн-режимі.')
    return
  }

  const confirmed = confirm('Ви впевнені? Це дію неможливо скасувати. Всі ваші дані будуть видалені безповоротно.')
  if (!confirmed) return

  try {
    const response = await fetch(`${BASE_API}/api/users/me`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token.value}` }
    })
    if (response.ok) {
      userStore.logout()
      router.push('/')
      alert('Акаунт видалено. Дякуємо, що були з нами.')
    }
  } catch (e) {
    alert('Не вдалося видалити акаунт. Спробуйте пізніше.')
  }
}

onMounted(async () => {
  if (userId.value && !user.value) {
    await userStore.fetchUser()
  }
})
</script>

<style scoped>
/* Базові стилі контейнера та заголовків */
.view-container { 
  padding: 20px; 
  max-width: 800px; 
  margin: 0 auto; 
}

.header { 
  border-bottom: 1px solid #333; 
  padding-bottom: 15px; 
  margin-bottom: 20px; 
}

.header-title { 
  display: flex; 
  align-items: center;
  margin: 0; 
  font-size: 1.5em; 
}

.title-icon { 
  color: #ff9800; 
  margin-right: 10px; 
}

.section-title, .form-title { 
  font-size: 1.2em; 
  margin-top: 0; 
  color: #fff; 
  margin-bottom: 15px; 
}

/* Картки та форми */
.card { 
  background: #1e1e1e; 
  border: 1px solid #333; 
  border-radius: 12px; 
  padding: 20px; 
  margin-bottom: 20px; 
}

.form-card { 
  padding: 20px; 
  border-left: 4px solid #ff9800; 
}

.settings-form { 
  display: flex; 
  flex-direction: column; 
  gap: 15px; 
}

.form-group { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  gap: 5px; 
}

.full-width {
  width: 100%;
  margin-bottom: 10px;
}

.form-group label { 
  font-size: 0.85em; 
  color: #b0bec5; 
  font-weight: bold; 
}

.input-field { 
  background: #121212; 
  color: #fff; 
  border: 1px solid #333; 
  padding: 10px; 
  border-radius: 6px; 
  color-scheme: dark; 
  width: 100%;
  box-sizing: border-box;
}

.input-field:focus { 
  outline: none; 
  border-color: #ff9800; 
}

/* Кнопки */
.btn-primary { 
  background: #ff9800; 
  color: #000; 
  border: none; 
  padding: 12px; 
  border-radius: 6px; 
  cursor: pointer; 
  font-weight: bold; 
  width: 100%; 
  margin-top: 10px; 
  transition: background-color 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
}

.btn-primary:hover:not(:disabled) {
  background: #f57c00;
}

.btn-primary:disabled { 
  opacity: 0.7; 
  cursor: not-allowed;
}

.animate-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* Статуси та попередження */
.text-danger { 
  color: #e65100 !important; 
}

.warning-text { 
  color: #e65100; 
  font-size: 0.9em; 
  margin: 10px 0 0 0; 
  font-weight: bold; 
}

/* ==========================================
   Специфічні стилі для SettingsView
   ========================================== */

/* Навігація вкладок */
.tabs-nav {
  display: flex;
  gap: 8px;
  background: #121212;
  padding: 5px;
  border-radius: 12px;
  border: 1px solid #333;
  margin-bottom: 25px;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 5px;
  background: transparent;
  color: #b0bec5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  font-size: 0.9em;
  transition: all 0.2s ease;
}

.tab-btn:hover { 
    color: #fff; 
    background: rgba(255, 255, 255, 0.05);
 }
.tab-btn.active { 
    background: #333; 
    color: #ff9800; 
}
.tab-btn.danger-tab.active-danger { 
    background: rgba(230, 81, 0, 0.1); 
    color: #e65100; 
    border: 1px solid rgba(230, 81, 0, 0.2); 
}

/* Картка небезпечної зони */
.danger-card {
  padding: 20px; 
  border-left: 4px solid #e65100; 
  background: rgba(230, 81, 0, 0.02);
}

.btn-danger {
  background: transparent; 
  color: #e65100; 
  border: 1px solid #e65100; 
  padding: 12px; 
  border-radius: 6px; 
  cursor: pointer; 
  font-weight: bold; 
  width: 100%; 
  margin-top: 10px; 
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
}
.btn-danger:hover { 
    background: rgba(230, 81, 0, 0.1); 
}

/* Інфо банер Email */
.info-banner {
  display: flex;
  gap: 10px;
  align-items: center;
  background: #121212;
  padding: 12px 15px;
  border-radius: 6px;
  border: 1px solid #333;
  margin-bottom: 20px;
}
.info-label { 
    color: #b0bec5; 
    font-size: 0.9em; 
    font-weight: bold; 
}
.info-value { 
    color: #fff; 
    font-size: 1em; 
}

/* Обгортка пароля */
.password-wrapper { 
    position: relative; 
    display: flex; 
    align-items: center; 
    width: 100%; 
}
.password-input { 
    padding-right: 40px; 
}
.btn-toggle-password {
  position: absolute; 
  right: 10px; 
  background: none; 
  border: none; color: #b0bec5; 
  cursor: pointer; 
  padding: 0; 
  display: flex; 
  align-items: center; 
  transition: color 0.2s;
}
.btn-toggle-password:hover { 
    color: #ff9800; 
    }
</style>