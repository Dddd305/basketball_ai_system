<template>
  <div class="view-container">
    <header class="header">
      <h1 class="page-title">
        <Activity class="title-icon" :size="28" />
        Активність
      </h1>
    </header>

    <div v-if="loading" class="loading-state">
      <Loader2 class="animate-spin" :size="24" color="#ff9800" />
      <p>Завантаження даних з сервера...</p>
    </div>

    <div v-else-if="user" class="content-wrapper">
      
      <div class="card form-card">
        <h2 class="form-title">
          <PlusCircle class="title-icon" :size="22" />
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

          <div class="form-row">
            <div class="form-group">
              <label>Сон (годин):</label>
              <input type="number" v-model="newMetric.sleep_hours" step="0.5" min="0" max="24" required class="input-field" />
            </div>
            <div class="form-group">
              <label>HRV (мс, необов'язково):</label>
              <input 
                type="number" 
                v-model.number="newMetric.hrv_value" 
                class="input-field" 
              />
            </div>
          </div>

          <div class="form-group" v-if="newMetric.activity_type !== 'Recovery'">
            <label>Кросівки (необов'язково):</label>
            <select v-model="newMetric.shoe_id" class="input-field">
              <option :value="null">Без кросівок / Інше</option>
              <option v-for="shoe in user?.shoes || []" :key="shoe.shoe_id" :value="shoe.shoe_id">
                {{ shoe.brand_model }} (Знос: {{ shoe.current_hours_played.toFixed(1) }} год)
              </option>
            </select>
          </div>

          <button type="submit" :disabled="isSubmitting" class="btn-primary">
            <Loader2 v-if="isSubmitting" class="animate-spin" :size="18" />
            <span>{{ isSubmitting ? 'Зберігаю...' : 'Зберегти' }}</span>
          </button>
          
          <transition name="fade">
            <div v-if="successMessage" class="alert-success">
              <CheckCircle :size="20" />
              <span>{{ successMessage }}</span>
            </div>
          </transition>
        </form>
      </div>

      <div class="card">
        <h2 class="section-title">
          <BarChart3 class="title-icon" :size="24" />
          Історія навантажень
        </h2>
        <div class="chart-wrapper">
          <canvas ref="chartCanvas"></canvas>
        </div>
        <p v-if="!hasMetrics" class="empty-text">
          Немає даних про тренування для побудови графіка.
        </p>
      </div>

      <div class="logbook-header">
        <h2 class="section-title" style="margin-top: 0;">
          <History class="title-icon" :size="24" />
          Щоденник тренувань
        </h2>
        <button @click="exportToCSV" class="btn-primary export-btn">
          <Download :size="16" />
          Експорт CSV
        </button>
      </div>

      <div class="card table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Тип</th>
              <th>Навантаження</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="metric in sortedMetrics" :key="metric.metric_id">
              <td>{{ metric.date.substring(5) }}</td>
              <td>
                <span :class="['badge', metric.activity_type.toLowerCase()]">
                  {{ translateActivity(metric.activity_type) }}
                </span>
              </td>
              <td>
                <span v-if="metric.activity_type !== 'Recovery'">{{ metric.duration_minutes }}хв (RPE {{ metric.rpe_score }})</span>
                <span v-else class="text-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Chart from 'chart.js/auto'
import { Activity, Loader2, PlusCircle, BarChart3, History, Download, CheckCircle } from 'lucide-vue-next'
import { useUserStore } from '../stores/userStore'
import { storeToRefs } from 'pinia'

const router = useRouter()
const userStore = useUserStore()

const { user, loading, userId, token, isAuthenticated } = storeToRefs(userStore)

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

// --- ОБЧИСЛЮВАЛЬНІ ВЛАСТИВОСТІ ---
const hasMetrics = computed(() => user.value?.metrics && user.value.metrics.length > 0)
const sortedMetrics = computed(() => {
  if (!hasMetrics.value) return []
  return [...user.value.metrics].sort((a, b) => b.date.localeCompare(a.date))
})

watch(sortedMetrics, async () => {
  await nextTick() // Чекає, поки DOM оновиться
  renderChart()
}, { deep: true, immediate: true })

/**
 * @function renderChart
 * @description Відмальовує гістограму навантажень за останні 7 днів за допомогою Chart.js.
 */
const renderChart = () => {
  if (!hasMetrics.value || !chartCanvas.value) return
  
  const ctx = chartCanvas.value
  const recentMetrics = sortedMetrics.value.slice(0, 7).reverse() 

  const labels = recentMetrics.map(m => m.date.substring(5)) 
  
  const data = recentMetrics.map(m => {
    if (m.activity_type === 'Recovery') return 0;
    return m.duration_minutes * m.rpe_score;
  });

  const colors = data.map(value => value > 600 ? '#e65100' : '#ff9800')

  if (chartInstance) chartInstance.destroy()

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{ 
        label: 'Навантаження', 
        data: data, 
        backgroundColor: colors, 
        borderRadius: 4 
      }]
    },
    options: {
      responsive: true, 
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, ticks: { color: '#b0bec5' }, grid: { color: '#333333' } },
        x: { ticks: { color: '#b0bec5' }, grid: { display: false } }
      },
      plugins: { 
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return 'Навантаження: ' + context.parsed.y;
            }
          }
        }
      }
    }
  })
}

/**
 * @function submitMetric
 * @description Відправляє тренування на сервер із JWT токеном.
 */
const submitMetric = async () => {
  if (!navigator.onLine) {
    alert('Відсутнє підключення до Інтернету. Збереження нового тренування наразі недоступне.')
    return
  }

  isSubmitting.value = true
  successMessage.value = ''
  const payload = { ...newMetric.value }

  if (payload.hrv_value === '' || payload.hrv_value === undefined) {
    payload.hrv_value = null;
  }
  
  if (payload.activity_type === 'Recovery') {
    payload.duration_minutes = 0; 
    payload.rpe_score = 0; 
    payload.shoe_id = null;
  }
  
  try {
    const API_URL = import.meta.env.VITE_API_URL;
    const response = await fetch(`${API_URL}/api/users/${userId.value}/metrics`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.value}`
      },
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) throw new Error('Помилка')
    
    successMessage.value = 'Збережено!'
    await userStore.fetchUser()
    
    // Скидання форми
    newMetric.value = {
      date: new Date().toISOString().split('T')[0],
      activity_type: 'Training',
      duration_minutes: 60,
      rpe_score: 5,
      hrv_value: null,
      sleep_hours: 8,
      shoe_id: null
    }

    setTimeout(() => { successMessage.value = '' }, 3000)
    
  } catch (error) {
    alert('Помилка збереження.')
  } finally {
    isSubmitting.value = false
  }
}

const exportToCSV = () => {
  if (!hasMetrics.value) {
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
  link.setAttribute('download', `metrics_${userId.value}.csv`);
  document.body.appendChild(link); 
  link.click(); 
  document.body.removeChild(link);
}

const translateActivity = (type) => {
  const dict = { 'Training': 'Тренування', 'Game': 'Гра', 'Recovery': 'Відновлення' }
  return dict[type] || type
}

onMounted(async () => {
  if (!isAuthenticated.value) {
    router.push('/')
    return
  }
  await userStore.fetchUser()
})

onUnmounted(() => {
  if (chartInstance) chartInstance.destroy()
})
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

.page-title { 
  margin: 0; 
  font-size: 1.5em; 
  display: flex;
  align-items: center;
  gap: 10px;
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
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.2em; 
  margin-top: 0; 
  color: #fff; 
  margin-bottom: 15px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 40vh;
  color: #b0bec5;
  font-size: 1.1em;
}

.training-form { 
  display: flex; 
  flex-direction: column; 
  gap: 15px; 
}

.form-row { 
  display: flex; 
  gap: 15px; 
  flex-wrap: wrap; 
}

.form-group { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  gap: 5px; 
  min-width: 150px; 
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary:disabled { 
  opacity: 0.7; 
}

.export-btn {
  padding: 8px 15px;
  font-size: 0.9em;
  height: auto;
}

.alert-success { 
  display: flex;
  align-items: center;
  gap: 10px;
  color: #4caf50; 
  background: rgba(76, 175, 80, 0.1); 
  padding: 12px 16px; 
  border-radius: 8px; 
  border: 1px solid rgba(76, 175, 80, 0.2); 
  font-weight: 500;
}

.chart-wrapper {
  position: relative;
  height: 250px;
  width: 100%;
}

.empty-text { 
  text-align: center; 
  color: #b0bec5; 
  padding: 15px 0; 
}

.logbook-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  margin-bottom: 10px;
}

.table-container {
  padding: 0;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.9em;
}

.data-table thead {
  background: #1e1e1e;
  z-index: 1;
  position: sticky;
  top: 0;
}

.data-table th {
  padding: 12px;
  color: #b0bec5;
  border-bottom: 2px solid #333;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #333;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 0.9em;
}

.badge.recovery { color: #4caf50; }
.badge.training { color: #fff; }
.badge.game { color: #ff9800; }
.text-muted { color: #b0bec5; }

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 600px) {
  .form-row {
    flex-direction: row; 
    gap: 10px;
  }

  .form-group {
    min-width: 0; 
  }

  .form-group label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.8em;
  }
}
</style>