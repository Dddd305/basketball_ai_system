<template>
  <div class="view-container">
    <header class="header">
      <h1 style="display: flex; align-items: center;">
        <svg class="title-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
        Активність
      </h1>
    </header>

    <div v-if="loading" class="loading-state" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 50vh;">
      <svg class="animate-spin" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ff9800" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
      </svg>
      <p style="margin: 0; color: #b0bec5; font-size: 1.1em;">Завантаження даних з сервера...</p>
    </div>

    <div v-else-if="user">
      
      <div class="card form-card">
        <h2 class="form-title">Додати активність</h2>
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
          
          <p v-if="successMessage" class="success-message" style="display: flex; align-items: center; gap: 10px; background: rgba(76, 175, 80, 0.1); color: #4caf50; padding: 12px 16px; border-radius: 8px; border: 1px solid rgba(76, 175, 80, 0.2); margin-bottom: 20px; font-weight: 500;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <path d="m9 11 3 3L22 4"></path>
          </svg>
          {{ successMessage }}
          </p>
        </form>
      </div>

      <div class="card">
        <h2 class="section-title">Історія навантажень</h2>
        <div style="position: relative; height: 250px; width: 100%;">
          <canvas ref="chartCanvas"></canvas>
        </div>
        <p v-if="!user.metrics || user.metrics.length === 0" class="empty-text">
          Немає даних про тренування для побудови графіка.
        </p>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; margin-bottom: 10px;">
        <h2 class="section-title" style="margin: 0;">Щоденник</h2>
        <button @click="exportToCSV" class="btn-primary" style="padding: 6px 12px; font-size: 0.85em; margin-top: 0;">
          Експорт CSV
        </button>
      </div>

      <div class="card" style="max-height: 300px; overflow-y: auto; padding: 0;">
        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9em;">
          <thead style="background: #1e1e1e; z-index: 1;">
            <tr style="border-bottom: 2px solid #333;">
              <th style="padding: 12px; color: #b0bec5;">Дата</th>
              <th style="padding: 12px; color: #b0bec5;">Тип</th>
              <th style="padding: 12px; color: #b0bec5;">Навантаження</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="metric in [...(user.metrics || [])].sort((a, b) => new Date(b.date) - new Date(a.date))" :key="metric.metric_id" style="border-bottom: 1px solid #333;">
              <td style="padding: 12px;">{{ metric.date.substring(5) }}</td>
              <td style="padding: 12px;">
                <span v-if="metric.activity_type === 'Recovery'" style="color: #4caf50; font-weight: bold;">Відновлення</span>
                <span v-else>{{ metric.activity_type === 'Training' ? 'Трен.' : 'Гра' }}</span>
              </td>
              <td style="padding: 12px;">
                <span v-if="metric.activity_type !== 'Recovery'">{{ metric.duration_minutes }}хв (RPE {{ metric.rpe_score }})</span>
                <span v-else style="color: #b0bec5;">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'

const currentUserId = localStorage.getItem('userId')
const user = ref(null)
const loading = ref(true)
const isSubmitting = ref(false)
const successMessage = ref('')

const chartCanvas = ref(null) 
let chartInstance = null

const newMetric = ref({
  date: new Date().toISOString().split('T')[0],
  activity_type: 'Training',
  duration_minutes: 60,
  rpe_score: 5,
  hrv_value: null,
  sleep_hours: 8,
  shoe_id: null
})

// ==========================================
// --- МЕРЕЖЕВІ ЗАПИТИ (OFFLINE-FIRST) ---
// ==========================================
const fetchUser = async () => {
  loading.value = true

  // 1. Миттєве завантаження з кешу
  const cachedData = localStorage.getItem(`user_data_${currentUserId}`)
  if (cachedData) {
    console.log('📦 Активність: Дані завантажено з кешу')
    user.value = JSON.parse(cachedData)
    // Малюємо графік одразу з кешованих даних
    setTimeout(() => { renderChart() }, 150)
  }

  // 2. Оновлення з сервера у фоновому режимі
  if (navigator.onLine) {
    try {
      const response = await fetch(`/api/users/${currentUserId}`) 
      if (!response.ok) throw new Error('Мережа')
      
      const freshUser = await response.json()
      user.value = freshUser
      
      // Зберігаємо свіжі дані
      localStorage.setItem(`user_data_${currentUserId}`, JSON.stringify(freshUser))
      console.log('☁️ Активність: Дані оновлено з сервера')
      
      // Перемальовуємо графік новими даними
      setTimeout(() => { renderChart() }, 150)
      
    } catch (error) {
      console.error('Помилка оновлення з сервера:', error)
    }
  } else if (!cachedData) {
    console.error('Немає підключення і немає збережених даних :(')
  }

  loading.value = false
}

const renderChart = () => {
  if (!user.value || !user.value.metrics || user.value.metrics.length === 0) return
  
  const ctx = chartCanvas.value
  if (!ctx) return

  const sortedMetrics = [...user.value.metrics].sort((a, b) => new Date(a.date) - new Date(b.date))
  const recentMetrics = sortedMetrics.slice(-7)
  const labels = recentMetrics.map(m => m.date.substring(5)) 
  const data = recentMetrics.map(m => m.duration_minutes * m.rpe_score) 
  const colors = data.map(value => value > 800 ? '#e65100' : '#ff9800')

  if (chartInstance) chartInstance.destroy()

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { 
          label: 'Навантаження', 
          data: data, 
          backgroundColor: colors, 
          borderRadius: 4 
        }
      ]
    },
    options: {
      responsive: true, 
      maintainAspectRatio: false,
      scales: {
        y: { 
          beginAtZero: true, 
          ticks: { color: '#b0bec5' }, 
          grid: { color: '#333333' } 
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

const submitMetric = async () => {
  // 🛡 ЗАХИСТ ОФЛАЙНУ: Перевірка перед відправкою
  if (!navigator.onLine) {
    alert('Відсутнє підключення до Інтернету. Збереження нового тренування наразі недоступне.')
    return
  }

  isSubmitting.value = true
  successMessage.value = ''
  const payload = { ...newMetric.value }
  
  if (payload.activity_type === 'Recovery') {
    payload.duration_minutes = 0; 
    payload.rpe_score = 0; 
    payload.shoe_id = null;
  }
  
  try {
    const response = await fetch(`/api/users/${currentUserId}/metrics`, {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(payload) 
    })
    
    if (!response.ok) throw new Error('Помилка')
    
    successMessage.value = 'Збережено!'
    await fetchUser() // Це автоматично оновить графік і перезапише кеш
    setTimeout(() => { successMessage.value = '' }, 3000)
    
  } catch (error) {
    alert('Помилка збереження.')
  } finally {
    isSubmitting.value = false
  }
}

const exportToCSV = () => {
  // Ця функція ПРАЦЮВАТИМЕ В ОФЛАЙНІ завдяки нашому кешу!
  if (!user.value || !user.value.metrics || user.value.metrics.length === 0) {
    return alert('Немає даних!');
  }
  
  const headers = ['Дата', 'Тип', 'Хвилини', 'RPE', 'Сон', 'HRV'];
  
  const rows = user.value.metrics.map(m => [
    m.date, 
    m.activity_type, 
    m.duration_minutes, 
    m.rpe_score, 
    m.sleep_hours, 
    m.hrv_value || ''
  ]);
  
  const csvContent = [
    headers.join(','), 
    ...rows.map(row => row.join(','))
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  
  link.setAttribute('href', url); 
  link.setAttribute('download', `metrics_${currentUserId}.csv`);
  document.body.appendChild(link); 
  link.click(); 
  document.body.removeChild(link);
}

onMounted(() => fetchUser())
</script>

<style scoped>
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

.header h1 { 
  margin: 0; 
  font-size: 1.5em; 
}

.title-icon { 
  color: #ff9800; 
  margin-right: 10px; 
}

.card { 
  background: #1e1e1e; 
  border: 1px solid #333; 
  border-radius: 12px; 
  padding: 20px; 
  margin-bottom: 25px; 
}

.form-title, 
.section-title { 
  font-size: 1.2em; 
  margin-top: 0; 
  color: #fff; 
  margin-bottom: 15px;
}

.training-form { 
  display: flex; 
  flex-direction: column; 
  gap: 15px; 
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
}

.input-field:focus { 
  outline: none; 
  border-color: #ff9800; 
}

.btn-primary { 
  background: #ff9800; 
  color: #000; 
  border: none; 
  padding: 12px; 
  border-radius: 6px; 
  cursor: pointer; 
  font-weight: bold; 
  margin-top: 5px; 
}

.btn-primary:disabled { 
  opacity: 0.7; 
}

.success-message { 
  color: #4caf50; 
  text-align: center; 
  background: rgba(76, 175, 80, 0.1); 
  padding: 10px; 
  border-radius: 4px; 
  border: 1px solid rgba(76, 175, 80, 0.3); 
}

.empty-text { 
  text-align: center; 
  color: #b0bec5; 
  padding: 15px 0; 
}

.animate-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  100% { transform: rotate(360deg); }
}
</style>