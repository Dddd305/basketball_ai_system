<template>
  <div class="dashboard-container">
    <div class="content-wrapper">
      
      <header class="header">
        <h1 style="display: flex; align-items: center;">
          <svg class="title-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>
          </svg>
          Профіль Гравця
        </h1>
        <button @click="logout" class="btn-outline">Вийти</button>
      </header>
      
      <div v-if="loading" class="loading-state">
        <p>⏳ Завантаження даних з сервера...</p>
      </div>
      
      <div v-else-if="user">
        
        <div class="card metrics-card">
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
            <p class="value" :class="{'text-danger': currentRiskStatus === 'High', 'text-success': currentRiskStatus === 'Optimal'}">
              {{ currentRiskStatus }}
            </p>
          </div>
        </div>

        <h2 class="section-title">
          <svg class="title-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>
          </svg>
          Історія навантажень
        </h2>
        <div class="card">
          <div style="position: relative; height: 300px; width: 100%;">
            <canvas id="loadChart"></canvas>
          </div>
          <p v-if="!user.metrics || user.metrics.length === 0" class="empty-text">
            Немає даних про тренування для побудови графіка.
          </p>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 30px;">
        <h2 class="section-title" style="margin-top: 0;">
          <svg class="title-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          Щоденник тренувань
        </h2>
        
        <button @click="exportToCSV" class="btn-primary" style="padding: 8px 15px; font-size: 0.9em; height: auto; display: flex; align-items: center; gap: 8px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Експорт у CSV
        </button>
      </div>

      <div class="card" style="max-height: 300px; overflow-y: auto; padding: 0; margin-bottom: 30px;">
        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9em;">
          <thead style="position: sticky; top: 0; background: var(--surface); z-index: 1;">
            <tr style="border-bottom: 2px solid var(--border);">
              <th style="padding: 12px 15px; color: var(--text-muted);">Дата</th>
              <th style="padding: 12px 15px; color: var(--text-muted);">Тип</th>
              <th style="padding: 12px 15px; color: var(--text-muted);">Навантаження</th>
              <th style="padding: 12px 15px; color: var(--text-muted);">Сон / HRV</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="metric in (user.metrics || []).slice().reverse()" :key="metric.metric_id" style="border-bottom: 1px solid var(--border);">
              <td style="padding: 12px 15px;">{{ metric.date }}</td>
              <td style="padding: 12px 15px;">
                <span v-if="metric.activity_type === 'Recovery'" style="color: #2ecc71; font-weight: bold;">Відновлення</span>
                <span v-else>{{ metric.activity_type }}</span>
              </td>
              <td style="padding: 12px 15px;">
                <span v-if="metric.activity_type !== 'Recovery'">{{ metric.duration_minutes }} хв (RPE {{ metric.rpe_score }})</span>
                <span v-else style="color: var(--text-muted);">—</span>
              </td>
              <td style="padding: 12px 15px;">
                {{ metric.sleep_hours }} год / <span v-if="metric.hrv_value">{{ metric.hrv_value }}</span><span v-else style="color: var(--text-muted);">—</span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!user.metrics || user.metrics.length === 0" style="padding: 20px; text-align: center; color: var(--text-muted);">
          Немає записів для відображення.
        </p>
      </div>
        <div class="card form-card">
          <h2 class="form-title">
            <svg class="title-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
            Додати активність
          </h2>
          <form @submit.prevent="submitMetric" class="training-form">
            
            <div class="form-row">
              <div class="form-group">
                <label>Дата:</label>
                <input type="date" v-model="newMetric.date" required class="input-field" />
              </div>
              <div class="form-group">
                <label>Тип:</label>
                <select v-model="newMetric.activity_type" class="input-field">
                  <option value="Training">Тренування</option>
                  <option value="Game">Гра</option>
                  <option value="Recovery">Відновлення</option>
                </select>
              </div>
            </div>

            <div class="form-row" v-if="newMetric.activity_type !== 'Recovery'">
              <div class="form-group">
                <label>Тривалість (хв):</label>
                <input type="number" v-model="newMetric.duration_minutes" required min="1" class="input-field" />
              </div>
              <div class="form-group">
                <label>Втома RPE (1-10):</label>
                <input type="number" v-model="newMetric.rpe_score" required min="1" max="10" class="input-field" />
              </div>
            </div>

            <div class="form-group" v-if="newMetric.activity_type !== 'Recovery'">
              </div>

            <div class="form-row" style="display: flex; gap: 15px; flex-wrap: wrap;">
              <div class="form-group" style="flex: 1;">
                <label>Сон (годин):</label>
                <input type="number" v-model="newMetric.sleep_hours" step="0.5" min="0" max="24" required class="input-field" />
              </div>
              <div class="form-group" style="flex: 1;">
                <label>HRV (мс, необов'язково):</label>
                <input type="number" v-model="newMetric.hrv_value" step="0.1" placeholder="Напр: 65" class="input-field" />
              </div>
            </div>

            <div class="form-group" v-if="newMetric.activity_type !== 'Recovery'">
              <label>Кросівки (необов'язково):</label>
              <select v-model="newMetric.shoe_id" class="input-field">
                <option :value="null">Без кросівок / Інше</option>
                <option v-for="shoe in user.shoes" :key="shoe.shoe_id" :value="shoe.shoe_id">
                  {{ shoe.brand_model }} (Знос: {{ shoe.current_hours_played.toFixed(1) }} год)
                </option>
              </select>
            </div>

            <button type="submit" :disabled="isSubmitting" class="btn-primary">
              {{ isSubmitting ? 'Зберігаю...' : 'Зберегти' }}
            </button>
            
            <p v-if="successMessage" class="success-message">✅ {{ successMessage }}</p>
          </form>
        </div>

        <h2 class="section-title">
          <svg class="title-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line>
          </svg>
          Інвентар
        </h2>
      
        <div class="card" style="margin-bottom: 20px; padding: 15px; border-left: 4px solid var(--primary);">
          <form @submit.prevent="addShoe" style="display: flex; gap: 15px; align-items: flex-end; flex-wrap: wrap;">
            <div class="form-group" style="flex: 2; min-width: 200px;">
              <label style="font-size: 0.85em; color: var(--text-muted); margin-bottom: 5px; display: block;">Модель кросівок:</label>
              <input type="text" v-model="newShoe.brand_model" required placeholder="Наприклад: Nike Lebron 20" class="input-field" style="width: 100%; box-sizing: border-box;" />
            </div>
            <div class="form-group" style="flex: 1; min-width: 120px;">
              <label style="font-size: 0.85em; color: var(--text-muted); margin-bottom: 5px; display: block;">Ресурс (годин):</label>
              <input type="number" v-model="newShoe.max_lifespan_hours" required min="10" class="input-field" style="width: 100%; box-sizing: border-box;" />
            </div>
            <button type="submit" :disabled="isAddingShoe" class="btn-primary" style="margin-top: 0; padding: 10px 20px; height: 42px;">
            {{ isAddingShoe ? '...' : '+ Додати' }}
            </button>
          </form>
        </div>
        <div class="inventory-grid">
          <div v-for="shoe in user.shoes" :key="shoe.shoe_id" class="card shoe-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <strong class="shoe-name">{{ shoe.brand_model }}</strong>
              <button @click="deleteShoe(shoe.shoe_id, shoe.brand_model)" class="btn-delete" title="Видалити кросівки">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  <line x1="10" y1="11" x2="10" y2="17"></line>
                  <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
              </button>
            </div>
            <p class="shoe-wear">
              <span>Знос:</span>
              <strong>{{ shoe.current_hours_played.toFixed(1) }} / {{ shoe.max_lifespan_hours }} год</strong>
            </p>
            <progress :value="shoe.current_hours_played" :max="shoe.max_lifespan_hours" class="wear-bar"></progress>
          </div>
        </div>

        <div class="ai-card">
          <div class="ai-header">
            <h2 style="display: flex; align-items: center;">
              <svg class="title-icon" style="color: var(--primary); margin-right: 10px;" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line>
              </svg>
              ШІ Тренер
            </h2>
            <button @click="generatePlan" :disabled="isGenerating" class="btn-ai">
              {{ isGenerating ? 'Аналізую...' : 'Оновити план' }}
            </button>
          </div>

          <div v-if="user.plans && user.plans.length > 0">
            <div class="ai-focus">
              <p class="label">Фокус тренування:</p>
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
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Chart from 'chart.js/auto'

const route = useRoute()
const router = useRouter()
const currentUserId = route.params.id

const user = ref(null)
const loading = ref(true)
const isGenerating = ref(false)
const isSubmitting = ref(false)
const successMessage = ref('')
let chartInstance = null

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

const newMetric = ref({
  date: new Date().toISOString().split('T')[0],
  activity_type: 'Training',
  duration_minutes: 60,
  rpe_score: 5,
  hrv_value: null,
  sleep_hours: 8,
  shoe_id: null
})

const newShoe = ref({
  brand_model: '',
  max_lifespan_hours: 50, // Стандартний ресурс
  cushion_type: 'Standard' // Додаємо, якщо твоя база цього вимагає
})
const isAddingShoe = ref(false)

const renderChart = () => {
  if (!user.value || !user.value.metrics || user.value.metrics.length === 0) return

  const ctx = document.getElementById('loadChart')
  if (!ctx) return

  const recentMetrics = user.value.metrics.slice(-7)
  const labels = recentMetrics.map(m => m.date)
  const data = recentMetrics.map(m => m.duration_minutes * m.rpe_score) 
  
  // Кольори для Dark Mode: Помаранчевий (норма) та Червоний (високе навантаження)
  const colors = data.map(value => value > 800 ? '#e65100' : '#ff9800')

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Навантаження (Хвилини × RPE)',
        data: data,
        backgroundColor: colors,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { 
          beginAtZero: true,
          ticks: { color: '#b0bec5' }, // Світло-сірий текст осі
          grid: { color: '#333333' }   // Темна сітка
        },
        x: {
          ticks: { color: '#b0bec5' },
          grid: { display: false }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  })
}

const fetchUser = async () => {
  try {
    const response = await fetch(`/api/users/${currentUserId}`) 
    if (!response.ok) throw new Error('Помилка мережі')
    
    user.value = await response.json()
    loading.value = false
    
    await nextTick()
    renderChart()
  } catch (error) {
    console.error('Помилка:', error)
    loading.value = false
  }
}

const submitMetric = async () => {
  isSubmitting.value = true
  successMessage.value = ''
  
  // Cтворення копії даних для відправки
  const payload = { ...newMetric.value }
  
  // Якщо це відновлення - примусово ставляться нулі
  if (payload.activity_type === 'Recovery') {
    payload.duration_minutes = 0
    payload.rpe_score = 0
    payload.shoe_id = null
  }
  
  try {
    const response = await fetch(`/api/users/${currentUserId}/metrics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload) 
    })
    
    if (!response.ok) throw new Error('Помилка збереження')
    
    successMessage.value = 'Активність успішно додано!'
    await fetchUser()
    
    newMetric.value.duration_minutes = 60
    newMetric.value.rpe_score = 5
    newMetric.value.sleep_hours = 8
    newMetric.value.hrv_value = null
    newMetric.value.shoe_id = null
    newMetric.value.activity_type = 'Training'
    
    setTimeout(() => { successMessage.value = '' }, 3000)
  } catch (error) {
    alert('Не вдалося зберегти активність.')
  } finally {
    isSubmitting.value = false
  }
}

// Експорт даних у CSV формат
const exportToCSV = () => {
  if (!user.value || !user.value.metrics || user.value.metrics.length === 0) {
    alert('Немає даних для експорту!');
    return;
  }

  // Створються заголовки колонок
  const headers = ['Дата', 'Тип_Активності', 'Тривалість_хв', 'RPE', 'Сон_год', 'HRV'];
  
  // Витягуються всі дані
  const rows = user.value.metrics.map(m => [
    m.date,
    m.activity_type,
    m.duration_minutes,
    m.rpe_score,
    m.sleep_hours,
    m.hrv_value || ''
  ]);

  // Збирається це все у формат CSV (розділювач - кома)
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n');

  // Створення файлу у браузері та його завантаження
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  
  link.setAttribute('href', url);
  link.setAttribute('download', `metrics_player_${currentUserId}.csv`);
  document.body.appendChild(link);
  
  link.click(); // Симулюється клік по посиланню
  
  document.body.removeChild(link); // Прибираємо сліди
}

const addShoe = async () => {
  isAddingShoe.value = true
  
  try {
    const response = await fetch(`/api/users/${currentUserId}/shoes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newShoe.value)
    })
    
    if (!response.ok) throw new Error('Помилка збереження кросівок')
    
    // Оновлюємо дані на сторінці
    await fetchUser()
    
    // Очищаємо поле вводу
    newShoe.value.brand_model = ''
    newShoe.value.max_lifespan_hours = 50
    
  } catch (error) {
    console.error('Помилка:', error)
    alert('Не вдалося додати кросівки. Перевір бекенд.')
  } finally {
    isAddingShoe.value = false
  }
}

const deleteShoe = async (shoeId, shoeName) => {
  // Запитуємо підтвердження у користувача
  if (!confirm(`Ви впевнені, що хочете видалити ${shoeName}? Цю дію неможливо скасувати.`)) {
    return
  }

  try {
    const response = await fetch(`/api/shoes/${shoeId}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error('Не вдалося видалити кросівки. Можливо, до них прив\'язані тренування.')
    }
    
    // Якщо успішно - просто перезавантажуємо дані користувача
    await fetchUser()
    alert('Кросівки успішно видалено!')
    
  } catch (error) {
    console.error('Помилка видалення:', error)
    alert(error.message)
  }
}

const generatePlan = async () => {
  isGenerating.value = true
  try {
    const response = await fetch(`/api/ai/generate_plan/${currentUserId}`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Помилка генерації')
    await fetchUser()
  } catch (error) {
    console.error('Помилка генерації:', error)
  } finally {
    isGenerating.value = false
  }
}

const logout = () => {
  router.push('/')
}

onMounted(() => {
  fetchUser()
})
</script>

<style scoped>
/* Глобальні змінні нашого дизайну */
.dashboard-container {
  --bg-dark: #121212;
  --surface: #1e1e1e;
  --text-main: #ffffff;
  --text-muted: #b0bec5;
  --primary: #ff9800;
  --primary-hover: #f57c00;
  --danger: #e65100;
  --success: #4caf50;
  --border: #333333;

  background-color: var(--bg-dark);
  color: var(--text-main);
  min-height: 100vh;
  padding: 20px 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.content-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Шапка */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 15px;
  margin-bottom: 25px;
}
.header h1 {
  margin: 0;
  color: var(--text-main);
}
.btn-outline {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: 0.3s;
}
.btn-outline:hover {
  border-color: var(--primary);
  color: var(--primary);
}

/* Стиль для нових SVG іконок у заголовках */
.title-icon {
  color: var(--primary); /* Робимо їх помаранчевими */
  margin-right: 10px; /* Відступ від тексту */
  stroke-width: 2.5; /* Робимо лінії трохи товщими і виразнішими */
}

/* Дозволяємо іконці та тексту стояти ідеально рівно на одній лінії */
.section-title, .form-title {
  display: flex;
  align-items: center;
}

/* Картки (основа) */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 25px;
}

.btn-delete {
  background: transparent;
  color: var(--text-muted); /* Базовий приємний сірий колір, як у решти тексту */
  border: none;
  cursor: pointer;
  padding: 5px;
  display: flex; /* Вирівнює іконку рівно по центру */
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease; /* Плавна зміна кольору */
}

.btn-delete:hover {
  color: var(--danger); /* При наведенні стає агресивно-помаранчевим (колір небезпеки/видалення) */
  background: rgba(230, 81, 0, 0.1); /* Легкий напівпрозорий фон для ефекту натискання */
  transform: scale(1.05); /* Ледь помітне збільшення іконки */
}

/* Антропометрія */
.metrics-card {
  display: flex;
  justify-content: space-around;
  text-align: center;
}
.metric-item {
  flex: 1;
}
.border-left {
  border-left: 1px solid var(--border);
}
.label {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.9em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.value {
  margin: 5px 0 0 0;
  font-size: 1.6em;
  font-weight: bold;
}
.unit {
  font-size: 0.5em;
  font-weight: normal;
  color: var(--text-muted);
}
.highlight {
  color: var(--primary);
}

/* Статистика */
.stats-grid {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
}
.stat-card {
  flex: 1;
  background: var(--surface);
  padding: 15px;
  border-radius: 12px;
  border: 1px solid var(--border);
}
.border-blue { border-left: 4px solid #2196f3; }
.border-purple { border-left: 4px solid #9c27b0; }
.border-orange { border-left: 4px solid var(--primary); }
.text-danger { color: var(--danger); }
.text-success { color: var(--success); }

/* Заголовки секцій */
.section-title {
  color: var(--text-main);
  font-size: 1.3em;
  margin-bottom: 15px;
}

/* Форми */
.form-title {
  font-size: 1.2em;
  margin-top: 0;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
  color: var(--text-main);
}
.training-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 15px;
}
.form-row {
  display: flex;
  gap: 15px;
}
.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.form-group label {
  font-size: 0.85em;
  color: var(--text-muted);
  font-weight: bold;
}
.input-field {
  background: var(--bg-dark);
  color: var(--text-main);
  border: 1px solid var(--border);
  padding: 10px;
  border-radius: 6px;
  color-scheme: dark; /* Щоб календар теж був темним */
}
.input-field:focus {
  outline: none;
  border-color: var(--primary);
}
.btn-primary {
  background: var(--primary);
  color: #000;
  border: none;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  font-size: 1em;
  transition: 0.3s;
  margin-top: 5px;
}
.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}
.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.success-message {
  color: var(--success);
  text-align: center;
  background: rgba(76, 175, 80, 0.1);
  padding: 10px;
  border-radius: 4px;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

/* Інвентар */
.inventory-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 25px;
}
.shoe-card {
  margin-bottom: 0;
  border-left: 4px solid var(--text-muted);
}
.shoe-name {
  font-size: 1.1em;
  color: var(--text-main);
}
.shoe-wear {
  display: flex;
  justify-content: space-between;
  margin: 10px 0 5px 0;
  font-size: 0.85em;
  color: var(--text-muted);
}
.wear-bar {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
}
.wear-bar::-webkit-progress-bar {
  background-color: var(--border);
}
.wear-bar::-webkit-progress-value {
  background-color: var(--primary);
}

/* ШІ Тренер */
.ai-card {
  background: linear-gradient(145deg, #1e1e1e 0%, #121212 100%);
  border: 1px solid var(--primary);
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(255, 152, 0, 0.1);
}
.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 15px;
  margin-bottom: 15px;
}
.ai-header h2 {
  margin: 0;
  font-size: 1.4em;
  color: var(--primary);
}
.btn-ai {
  background: var(--text-main);
  color: #000;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-weight: bold;
  transition: 0.3s;
}
.btn-ai:hover:not(:disabled) {
  background: var(--primary);
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
  color: var(--text-muted);
}
.empty-text {
  text-align: center;
  color: var(--text-muted);
  padding: 15px 0;
}
</style>