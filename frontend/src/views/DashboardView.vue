<template>
  <div class="view-container">
    
    <header class="header">
      <h1 class="header-title" style="display: flex; align-items: center; gap: 8px;">
        <User class="title-icon" :size="28" />
        Головна панель
      </h1>
      <button @click="logout" class="btn-outline">Вийти</button>
    </header>
    
    <div v-if="loading" class="loading-state" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 50vh;">
      <Loader2 class="animate-spin" :size="24" color="#ff9800" />
      <p style="margin: 0; color: #b0bec5; font-size: 1.1em;">Завантаження даних з сервера...</p>
    </div>
    
    <div v-else-if="user">
      
      <div v-if="showCalibrationModal" class="modal-overlay">
        <div class="modal-card modal-large">
          <div class="modal-icon" style="display: flex; justify-content: center; margin-bottom: 15px; color: #ff9800;">
            <Settings :size="48" />
          </div>
          <h2 class="modal-title">Налаштування профілю</h2>
          
          <div v-if="calibrationStep === 1">
            <p class="modal-subtitle">Крок 1/2: Базові параметри вашого тижня.</p>
            
            <form @submit.prevent="generateDraft" class="calibration-form">
              <div class="form-group">
                <label>Скільки днів ви тренувались за останні 7 днів?</label>
                <div class="slider-container">
                  <input type="range" v-model.number="calibrationForm.frequency" min="0" max="7" class="range-slider" />
                  <span class="slider-value">{{ calibrationForm.frequency }} дн.</span>
                </div>
              </div>

              <div class="form-group" v-if="calibrationForm.frequency > 0">
                <label>Типова інтенсивність (швидко формує чернетку):</label>
                <select v-model="calibrationForm.intensity" class="input-field">
                  <option value="Легко">Легко (~45 хв, RPE 4)</option>
                  <option value="Середньо">Середньо (~75 хв, RPE 6)</option>
                  <option value="Важко">Важко (~100 хв, RPE 8)</option>
                </select>
              </div>

              <div class="form-group">
                <label>Скільки в середньому ви спите? (годин)</label>
                <div class="slider-container">
                  <input type="range" v-model.number="calibrationForm.sleep_hours" min="4" max="24" step="0.5" class="range-slider" />
                  <span class="slider-value">{{ calibrationForm.sleep_hours }} год</span>
                </div>
              </div>

              <button type="submit" class="btn-primary">Далі: Згенерувати чернетку &rarr;</button>
            </form>
          </div>

          <div v-if="calibrationStep === 2">
            <p class="modal-subtitle">Крок 2/2: Перевірте та відредагуйте точні дані.</p>
            
            <div class="draft-list">
              <div v-for="(day, index) in draftDays" :key="index" class="draft-day-card" :class="{'active-day': day.activity_type !== 'Recovery'}">
                <div class="day-header">
                  <strong>{{ formatDate(day.date) }}</strong>
                  <select 
                    v-model="day.activity_type" 
                    :class="['input-field', 'badge', day.activity_type.toLowerCase()]" 
                    style="width: auto; padding: 4px 8px; cursor: pointer; border: none; outline: none; text-align: center;"
                  >
                    <option value="Training" style="background: #121212; color: #fff;">Тренування</option>
                    <option value="Game" style="background: #121212; color: #ff9800;">Гра</option>
                    <option value="Recovery" style="background: #121212; color: #4caf50;">Відпочинок</option>
                  </select>
                </div>
                
                <div v-if="day.activity_type !== 'Recovery'" class="day-details">
                  <div class="mini-group">
                    <label>Хвилин:</label>
                    <input type="number" v-model.number="day.duration_minutes" min="10" class="input-field mini-input" />
                  </div>
                  <div class="mini-group">
                    <label>RPE (1-10):</label>
                    <input type="number" v-model.number="day.rpe_score" min="1" max="10" class="input-field mini-input" />
                  </div>
                </div>
              </div>
            </div>

            <div class="wizard-actions">
              <button @click="calibrationStep = 1" class="btn-secondary">&larr; Назад</button>
              <button @click="submitExactData" :disabled="isCalibrating" class="btn-primary flex-fill">
                {{ isCalibrating ? 'Збереження...' : 'Зберегти точні дані в базу' }}
              </button>
            </div>
          </div>
          
        </div>
      </div>

      <div class="card metrics-card-container">
        <div class="card-header" style="display: flex; justify-content: space-between; margin-bottom: 15px;">
          <h3 style="margin: 0; font-size: 1.1em; color: #b0bec5;">Мій профіль</h3>
          <button v-if="!isEditing" @click="startEditing" class="btn-text" style="display: flex; align-items: center; gap: 5px;">
            <Edit2 :size="16" />
            Редагувати
          </button>
          <div v-else class="edit-actions">
            <button @click="cancelEditing" class="btn-text" style="color: #b0bec5;">Скасувати</button>
            <button @click="saveProfile" class="btn-text" style="color: #4caf50; font-weight: bold;">Зберегти</button>
          </div>
        </div>

        <div v-if="!isEditing" class="metrics-card">
          <div class="metric-item">
            <p class="label">Позиція</p>
            <p class="value highlight">{{ user.position }}</p>
          </div>
          <div class="metric-item border-left">
            <p class="label">Зріст</p>
            <p class="value">{{ user.height_cm }} <span class="unit">см</span></p>
          </div>
          <div class="metric-item border-left">
            <p class="label">Вага</p>
            <p class="value">{{ user.weight_kg }} <span class="unit">кг</span></p>
          </div>
        </div>

        <div v-else class="edit-form-grid">
          <div class="form-group">
            <label class="label">Позиція</label>
            <select v-model="editForm.position" class="input-field mini-input">
              <option value="PG">PG</option>
              <option value="SG">SG</option>
              <option value="SF">SF</option>
              <option value="PF">PF</option>
              <option value="C">C</option>
            </select>
          </div>
          <div class="form-group">
            <label class="label">Зріст (см)</label>
            <input type="number" v-model="editForm.height_cm" class="input-field mini-input" />
          </div>
          <div class="form-group">
            <label class="label">Вага (кг)</label>
            <input type="number" v-model="editForm.weight_kg" class="input-field mini-input" />
          </div>
        </div>
      </div>

      <h2 class="section-title">Аналітика здоров'я</h2>
      <div class="science-grid">
        
        <div class="card science-card">
          <p class="label">Індекс готовності</p>
          <div class="readiness-score" :style="{ color: getReadinessColor(user.readiness_score) }">
            {{ user.readiness_score }}%
          </div>
          <p class="science-hint">На основі останнього сну та RPE</p>
          <div class="progress-bg">
            <div class="progress-fill" :style="{ width: user.readiness_score + '%', backgroundColor: getReadinessColor(user.readiness_score) }"></div>
          </div>
        </div>

        <div class="card science-card">
          <div style="display: flex; justify-content: center; align-items: center; gap: 10px;">
            <p class="label" title="Acute:Chronic Workload Ratio" style="margin: 0;">Коефіцієнт ACWR</p>
            <span v-if="user.days_in_system < 28" title="Збір повноцінної хронічної бази (28 днів)" style="display: flex; align-items: center; background: rgba(255, 152, 0, 0.15); color: #ff9800; font-size: 0.65em; padding: 3px 6px; border-radius: 4px; border: 1px solid rgba(255, 152, 0, 0.5); text-transform: uppercase; font-weight: bold;">
              <AlertTriangle :size="12" style="margin-right: 4px;" />
              {{ user.days_in_system }}/28 дн.
            </span>
          </div>
          <div class="acwr-score" :style="{ color: getAcwrColor(user.acwr_ratio) }">
            {{ user.acwr_ratio }}
          </div>
          <p class="science-hint" :style="{ color: getAcwrColor(user.acwr_ratio), fontWeight: 'bold' }">
            {{ user.acwr_status }}
          </p>
          <p class="science-hint" style="margin-top: 5px;">Норма: 0.8 - 1.3</p>
        </div>

      </div>

      <div class="stats-grid">
        <div class="stat-card border-blue">
          <p class="label">Всього годин</p>
          <p class="value">{{ totalHoursPlayed }}</p>
        </div>
        <div class="stat-card border-purple">
          <p class="label">Середній RPE</p>
          <p class="value">{{ averageRpe }} <span class="unit">/ 10</span></p>
        </div>
        <div class="stat-card border-orange">
          <p class="label">Статус (ШІ)</p>
          <p class="value" :class="{'text-danger': currentRiskStatus.includes('Danger'), 'text-success': currentRiskStatus.includes('Optimal')}">
            {{ currentRiskStatus.split(' ')[0] }}
          </p>
        </div>
      </div>

      <div class="ai-card">
        <div class="ai-header">
          <h2 style="display: flex; align-items: center; gap: 10px;">
            <Cpu class="title-icon" :size="26" style="color: var(--primary);" />
            ШІ Тренер
          </h2>
          <button @click="generatePlan" :disabled="isGenerating" class="btn-ai">
            <span v-if="isGenerating"><Loader2 class="animate-spin" :size="16" style="vertical-align: middle; margin-right: 5px;"/> Аналізую...</span>
            <span v-else>Оновити план</span>
          </button>
        </div>

        <div v-if="user.plans && user.plans.length > 0">
          <div class="ai-focus">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
              <p class="label">Фокус тренування:</p>
              <p class="label" style="font-weight: bold; color: #ff9800;">План від: {{ formatDate(user.plans[user.plans.length - 1].date) }}</p>
            </div>
            <p class="value">{{ user.plans[user.plans.length - 1].plan_focus }}</p>
          </div>
          <p class="ai-content">
            {{ user.plans[user.plans.length - 1].plan_content }}
          </p>
        </div>
        <div v-else class="empty-text">
          <p>Натисніть "Оновити план", щоб ШІ проаналізував ваші метрики.</p>
        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { User, Loader2, Settings, Edit2, AlertTriangle, Cpu } from 'lucide-vue-next'
import { useUserStore } from '../stores/userStore'
import { storeToRefs } from 'pinia'

const router = useRouter()
const userStore = useUserStore()

const { user, loading, userId, token, isAuthenticated } = storeToRefs(userStore)

const isGenerating = ref(false)

// ==========================================
// --- УТИЛІТИ ДЛЯ КОЛЬОРІВ ---
// ==========================================
const getReadinessColor = (score) => {
  if (score >= 80) return '#4caf50' 
  if (score >= 60) return '#ffeb3b' 
  return '#f44336' 
}

const getAcwrColor = (ratio) => {
  const val = parseFloat(ratio)
  if (val === 0 || val < 0.8) return '#b0bec5'
  if (val <= 1.3) return '#4caf50'
  if (val <= 1.5) return '#ff9800'
  return '#f44336'
}

// ==========================================
// --- ЛОГІКА КАЛІБРУВАННЯ ---
// ==========================================
const showCalibrationModal = ref(false)
const isCalibrating = ref(false)
const calibrationStep = ref(1)

const calibrationForm = ref({ frequency: 3, intensity: 'Середньо', sleep_hours: 7.5 })
const draftDays = ref([])

const formatDate = (dateString) => {
  const d = new Date(dateString)
  return d.toLocaleDateString('uk-UA', { weekday: 'short', day: 'numeric', month: 'short' })
}

const getLocalDateString = (dateObj) => {
  const year = dateObj.getFullYear()
  const month = String(dateObj.getMonth() + 1).padStart(2, '0')
  const day = String(dateObj.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const generateDraft = () => {
  const intensityMap = { "Легко": { duration: 45, rpe: 4 }, "Середньо": { duration: 75, rpe: 6 }, "Важко": { duration: 100, rpe: 8 } }
  const stats = intensityMap[calibrationForm.value.intensity]
  const today = new Date()
  const daysArray = []

  for (let i = 0; i < 7; i++) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    daysArray.push({
      date: getLocalDateString(d),
      activity_type: 'Recovery', 
      duration_minutes: stats.duration,
      rpe_score: stats.rpe,
      sleep_hours: calibrationForm.value.sleep_hours
    })
  }

  if (calibrationForm.value.frequency > 0) {
    const totalDays = Math.min(calibrationForm.value.frequency, 7);
    const slots = [0, 1, 2, 3, 4, 5, 6].sort(() => Math.random() - 0.5);
    for (let i = 0; i < totalDays; i++) { daysArray[slots[i]].activity_type = 'Training'; }
  }
  draftDays.value = daysArray.reverse()
  calibrationStep.value = 2
}

const submitExactData = async () => {
  isCalibrating.value = true
  try {
    const response = await fetch(`https://basketball-api-kyiv.onrender.com/api/users/${userId.value}/calibrate`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.value}`
      },
      body: JSON.stringify(draftDays.value)
    })
    
    if (!response.ok) throw new Error('Помилка при збереженні даних')
    
    await userStore.fetchUser() 
    showCalibrationModal.value = false 
  } catch (error) {
    alert('Помилка: ' + error.message)
  } finally {
    isCalibrating.value = false
  }
}

// --- Редагування профілю ---
const isEditing = ref(false)
const editForm = ref({ position: '', height_cm: 0, weight_kg: 0 })

const startEditing = () => {
  editForm.value = { position: user.value.position, height_cm: user.value.height_cm, weight_kg: user.value.weight_kg }
  isEditing.value = true
}

const cancelEditing = () => { isEditing.value = false }

const saveProfile = async () => {
  try {
    const response = await fetch(`https://basketball-api-kyiv.onrender.com/api/users/${userId.value}`, {
      method: 'PUT', 
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.value}`
      }, 
      body: JSON.stringify(editForm.value)
    })
    if (!response.ok) throw new Error('Помилка оновлення')
    await userStore.fetchUser()
    isEditing.value = false 
  } catch (error) {
    alert('Не вдалося зберегти зміни.')
  }
}

// --- БАЗОВА СТАТИСТИКА ---
const totalHoursPlayed = computed(() => {
  if (!user.value || !user.value.metrics) return 0
  const totalMinutes = user.value.metrics.reduce((sum, m) => sum + m.duration_minutes, 0)
  return (totalMinutes / 60).toFixed(1)
})

const averageRpe = computed(() => {
  if (!user.value || !user.value.metrics || user.value.metrics.length === 0) return 0
  const sum = user.value.metrics.reduce((acc, m) => acc + m.rpe_score, 0)
  return (sum / user.value.metrics.length).toFixed(1)
})

const currentRiskStatus = computed(() => {
  if (!user.value || !user.value.plans || user.value.plans.length === 0) return 'Невідомо'
  return user.value.plans[user.value.plans.length - 1].fatigue_risk
})

// Генерація плану від ШІ
const generatePlan = async () => {
  isGenerating.value = true
  try {
    const response = await fetch(`https://basketball-api-kyiv.onrender.com/api/ai/generate_plan/${userId.value}`, { 
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token.value}` }
    })
    if (!response.ok) throw new Error('Помилка генерації')
    await userStore.fetchUser()
  } catch (error) {
    console.error('Помилка генерації:', error)
  } finally {
    isGenerating.value = false
  }
}

const logout = () => {
  userStore.logout()
  router.push('/')
}

onMounted(async () => {
  if (!isAuthenticated.value) {
    logout()
    return
  }
  
  await userStore.fetchUser()
  
  if (user.value && (!user.value.metrics || user.value.metrics.length === 0)) {
    showCalibrationModal.value = true
  }
})
</script>

<style scoped>
/* =========================================
   БАЗОВИЙ МАКЕТ ТА ТИПОГРАФІКА
   ========================================= */
.view-container { 
  padding: 20px; 
  max-width: 800px; 
  margin: 0 auto; 
  position: relative; 
}

.header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  border-bottom: 1px solid #333; 
  padding-bottom: 15px; 
  margin-bottom: 25px; 
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

.section-title { 
  font-size: 1.2em; 
  margin-top: 0; 
  color: #fff; 
  margin-bottom: 15px; 
}

/* =========================================
   КНОПКИ ТА ЕЛЕМЕНТИ УПРАВЛІННЯ
   ========================================= */
.btn-outline { 
  background: transparent; 
  color: #b0bec5; 
  border: 1px solid #333; 
  padding: 6px 12px; 
  border-radius: 20px; 
  cursor: pointer; 
  transition: 0.3s; 
}

.btn-outline:hover { 
  border-color: #ff9800; 
  color: #ff9800; 
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

.btn-secondary { 
  background: transparent; 
  color: #b0bec5; 
  border: 1px solid #555; 
  padding: 14px; 
  border-radius: 8px; 
  cursor: pointer; 
  margin-top: 10px; 
}

.btn-secondary:hover { 
  border-color: #ff9800; 
  color: #ff9800; 
}

.btn-text { 
  background: transparent; 
  border: none; 
  color: #ff9800; 
  cursor: pointer; 
  font-size: 0.9em; 
  padding: 0; 
}

.animate-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* =========================================
   КАРТКИ (ОСНОВНИЙ ДИЗАЙН)
   ========================================= */
.card { 
  background: #1e1e1e; 
  border: 1px solid #333; 
  border-radius: 12px; 
  padding: 20px; 
  margin-bottom: 25px; 
}

/* =========================================
   МОДАЛЬНЕ ВІКНО "МАЙСТЕР КАЛІБРУВАННЯ"
   ========================================= */
.modal-overlay {
  position: fixed; 
  top: 0; 
  left: 0; 
  right: 0; 
  bottom: 0;
  background: rgba(0, 0, 0, 0.85); 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  z-index: 1000; 
  backdrop-filter: blur(5px); 
  padding: 20px;
}

.modal-card {
  background: linear-gradient(145deg, #1e1e1e 0%, #121212 100%);
  border: 1px solid #ff9800; 
  border-radius: 16px; 
  padding: 30px; 
  width: 100%; 
  box-shadow: 0 10px 40px rgba(255, 152, 0, 0.2);
}

.modal-large { 
  max-width: 550px; 
}

.modal-icon { 
  font-size: 3em; 
  margin-bottom: 10px; 
  text-align: center; 
}

.modal-title { 
  color: #ff9800; 
  margin: 0 0 10px 0; 
  font-size: 1.5em; 
  text-align: center; 
}

.modal-subtitle { 
  color: #b0bec5; 
  font-size: 0.9em; 
  margin-bottom: 25px; 
  line-height: 1.5; 
  text-align: center; 
}

.calibration-form { 
  display: flex; 
  flex-direction: column; 
  gap: 20px; 
  text-align: left; 
}

.wizard-actions { 
  display: flex; 
  gap: 15px; 
}

.flex-fill { 
  flex: 1; 
}

/* --- Список днів (Чернетка) --- */
.draft-list { 
  display: flex; 
  flex-direction: column; 
  gap: 10px; 
  margin-bottom: 20px; 
  max-height: 400px; 
  overflow-y: auto; 
  padding-right: 5px; 
}

.draft-list::-webkit-scrollbar { 
  width: 6px; 
}

.draft-list::-webkit-scrollbar-thumb { 
  background: #ff9800; 
  border-radius: 3px; 
}

.draft-day-card { 
  border: 1px solid #333; 
  background: #1a1a1a; 
  border-radius: 8px; 
  padding: 12px; 
  transition: 0.3s; 
}

.active-day { 
  border-color: rgba(255, 152, 0, 0.5); 
  background: rgba(255, 152, 0, 0.05); 
}

.day-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
}

.day-header strong { 
  color: #fff; 
  font-size: 0.95em; 
}

.day-details { 
  display: flex; 
  gap: 15px; 
  margin-top: 15px; 
  padding-top: 10px; 
  border-top: 1px dashed #333; 
}

.mini-group { 
  flex: 1; 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
}

.mini-group label { 
  color: #b0bec5; 
  font-size: 0.8em; 
}

/* =========================================
   ФОРМИ ТА INPUT ЕЛЕМЕНТИ
   ========================================= */
.slider-container { 
  display: flex; 
  align-items: center; 
  gap: 15px; 
}

.range-slider { 
  flex: 1; 
  accent-color: #ff9800; 
  cursor: pointer; 
}

.slider-value { 
  min-width: 60px; 
  text-align: right; 
  font-weight: bold; 
  color: #ff9800; 
}

.input-field { 
  background: #121212; 
  color: #fff; 
  border: 1px solid #333; 
  border-radius: 6px; 
  padding: 10px; 
  color-scheme: dark; 
  width: 100%; 
  box-sizing: border-box; 
}

.input-field:focus { 
  outline: none; 
  border-color: #ff9800; 
}

.mini-input { 
  width: 100%; 
  padding: 8px; 
  margin-top: 5px; 
  text-align: center; 
  font-size: 1em; 
  font-weight: bold; 
}

/* =========================================
   АНАЛІТИКА ЗДОРОВ'Я ТА МЕТРИКИ
   ========================================= */
.metrics-card { 
  display: flex; 
  justify-content: space-around; 
  text-align: center; 
}

.metric-item { 
  flex: 1; 
}

.border-left { 
  border-left: 1px solid #333; 
}

.label { 
  margin: 0; 
  color: #b0bec5; 
  font-size: 0.85em; 
  text-transform: uppercase; 
}

.value { 
  margin: 5px 0 0 0; 
  font-size: 1.5em; 
  font-weight: bold; 
}

.unit { 
  font-size: 0.5em; 
  color: #b0bec5; 
  font-weight: normal; 
}

.highlight { 
  color: #ff9800; 
}

.science-grid { 
  display: flex; 
  gap: 15px; 
  margin-bottom: 25px; 
}

.science-card { 
  flex: 1; 
  text-align: center; 
  margin-bottom: 0; 
  display: flex; 
  flex-direction: column; 
  justify-content: center; 
}

.readiness-score, .acwr-score { 
  font-size: 2.5em; 
  font-weight: bold; 
  margin: 10px 0; 
  text-shadow: 0 0 10px rgba(0,0,0,0.5); 
}

.science-hint { 
  margin: 0; 
  font-size: 0.8em; 
  color: #b0bec5; 
}

.progress-bg { 
  width: 100%; 
  height: 8px; 
  background: #333; 
  border-radius: 4px; 
  margin-top: 15px; 
  overflow: hidden; 
}

.progress-fill { 
  height: 100%; 
  transition: width 0.5s ease; 
}

/* =========================================
   СТАТИСТИКА (Кольорові картки)
   ========================================= */
.stats-grid { 
  display: flex; 
  gap: 15px; 
  margin-bottom: 25px; 
}

.stat-card { 
  flex: 1; 
  background: #1e1e1e; 
  padding: 15px; 
  border-radius: 12px; 
  border: 1px solid #333; 
}

.border-blue { border-left: 4px solid #2196f3; }
.border-purple { border-left: 4px solid #9c27b0; }
.border-orange { border-left: 4px solid #ff9800; }

.text-danger { color: #e65100; }
.text-success { color: #4caf50; }

/* =========================================
   ШІ ТРЕНЕР (AI CARD)
   ========================================= */
.ai-card { 
  background: linear-gradient(145deg, #1e1e1e 0%, #121212 100%); 
  border: 1px solid #ff9800; 
  padding: 25px; 
  border-radius: 12px; 
  box-shadow: 0 4px 15px rgba(255, 152, 0, 0.1); 
}

.ai-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  border-bottom: 1px solid #333; 
  padding-bottom: 15px; 
  margin-bottom: 15px; 
}

.ai-header h2 { 
  margin: 0; 
  font-size: 1.3em; 
  color: #ff9800; 
}

.btn-ai { 
  background: #ffffff; 
  color: #000; 
  border: none; 
  padding: 8px 16px; 
  border-radius: 20px; 
  cursor: pointer; 
  font-weight: bold; 
}

.btn-ai:hover:not(:disabled) { 
  background: #ff9800; 
}

.ai-focus { 
  background: rgba(255, 255, 255, 0.05); 
  padding: 15px; 
  border-radius: 8px; 
  margin-bottom: 15px; 
}

.ai-content { 
  margin: 0; 
  line-height: 1.6; 
  white-space: pre-line; 
  color: #b0bec5; 
}

.empty-text { 
  text-align: center; 
  color: #b0bec5; 
}

.edit-actions { 
  display: flex; 
  gap: 15px; 
}

.edit-form-grid { 
  display: flex; 
  gap: 15px; 
  justify-content: space-between; 
}

/* --- Кольорові бейджі для Select --- */
.badge {
  font-weight: bold;
  font-size: 0.9em;
  border-radius: 4px;
}
.badge.recovery { color: #4caf50; background: rgba(76, 175, 80, 0.1); }
.badge.training { color: #fff; background: rgba(255, 255, 255, 0.1); }
.badge.game { color: #ff9800; background: rgba(255, 152, 0, 0.1); }

</style>