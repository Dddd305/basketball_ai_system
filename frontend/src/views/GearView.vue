<template>
  <div class="view-container">
    <header class="header">
      <h1 class="header-title" style="display: flex; align-items: center; gap: 8px;">
        <Archive class="title-icon" :size="28" />
        Інвентар
      </h1>
    </header>

    <div v-if="loading" class="loading-state" style="display: flex; align-items: center; justify-content: center; gap: 10px; height: 50vh;">
      <Loader2 class="animate-spin" :size="24" color="#ff9800" />
      <p style="margin: 0; color: #b0bec5; font-size: 1.1em;">Завантаження даних з сервера...</p>
    </div>

    <div v-else-if="user">
      
      <div class="card form-card">
        <h2 class="form-title">Додати нові кросівки</h2>
        <form @submit.prevent="addShoe" class="add-shoe-form">
          
          <div class="form-group full-width">
            <label>Модель кросівок:</label>
            <input 
              type="text" 
              v-model="newShoe.brand_model" 
              required 
              class="input-field" 
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Тип взуття:</label>
              <select v-model="newShoe.shoe_type" class="input-field">
                <option value="Баскетбольні">Баскетбольні (x1.0)</option>
                <option value="Інші">Бігові / Інші (x0.7)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Основне покриття:</label>
              <select v-model="newShoe.surface_type" class="input-field">
                <option value="Паркет">Паркет (x1.0)</option>
                <option value="Гума/Тартан">Гума / Тартан (x0.8)</option>
                <option value="Гібрид (Мікс)">Гібрид (Мікс) (x0.75)</option>
                <option value="Асфальт">Асфальт (x0.5)</option>
              </select>
            </div>
          </div>

          <div class="calculator-box">
            <div class="calc-header">
              <span>Максимальний ресурс (розрахунок ШІ):</span>
              <strong class="highlight-text">{{ calculatedMaxLifespan }} год</strong>
            </div>
            <p class="calc-hint">Враховано вашу вагу ({{ user.weight_kg }} кг), тип взуття та покриття.</p>
            
            <div class="wear-section">
              <label class="wear-label">
                <span>Початковий знос (якщо б/в):</span>
                <span>{{ newShoe.initial_wear_percentage }}%</span>
              </label>
              
              <div class="hybrid-input-row">
                <input 
                  type="range" 
                  v-model.number="newShoe.initial_wear_percentage" 
                  min="0" 
                  max="100" 
                  class="range-slider"
                />
                <div class="hours-input-wrapper">
                  <input 
                    type="number" 
                    v-model.number="calculatedCurrentHours" 
                    min="0" 
                    :max="calculatedMaxLifespan" 
                    class="input-field mini-number"
                  />
                  <span class="hours-label">год</span>
                </div>
              </div>
            </div>
          </div>

          <button type="submit" :disabled="isAddingShoe" class="btn-primary">
            {{ isAddingShoe ? 'Зберігаю...' : '+ Додати в інвентар' }}
          </button>
        </form>
      </div>

      <h2 class="section-title">Мої Кросівки</h2>
      <div class="inventory-grid">
        <div v-for="shoe in user.shoes" :key="shoe.shoe_id" class="card shoe-card">
          <div class="shoe-header">
            <strong class="shoe-name">{{ shoe.brand_model }}</strong>
            <button @click="deleteShoe(shoe.shoe_id, shoe.brand_model)" class="btn-delete" title="Видалити">✖</button>
          </div>
          
          <div class="shoe-tags">
            <span class="tag">
              {{ shoe.cushion_type.includes(' | ') ? shoe.cushion_type.split(' | ')[0] : 'Баскетбольні' }}
            </span>
            <span class="tag surface-tag" v-if="shoe.cushion_type.includes(' | ')">
              {{ shoe.cushion_type.split(' | ')[1] }}
            </span>
          </div>
          
          <p class="shoe-wear">
            <span>Знос:</span>
            <strong :class="{'text-danger': shoe.current_hours_played >= shoe.max_lifespan_hours}">
              {{ shoe.current_hours_played.toFixed(1) }} / {{ shoe.max_lifespan_hours.toFixed(1) }} год
            </strong>
          </p>
          
          <progress 
            :value="shoe.current_hours_played" 
            :max="shoe.max_lifespan_hours" 
            class="wear-bar"
            :class="{'danger-bar': shoe.current_hours_played >= shoe.max_lifespan_hours}">
          </progress>
          
          <p v-if="shoe.current_hours_played >= shoe.max_lifespan_hours" class="warning-text">
            Ресурс вичерпано. Високий ризик травми.
          </p>
        </div>
        
        <p v-if="!user.shoes || user.shoes.length === 0" class="empty-text">
          У вас ще немає доданих кросівок.
        </p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Archive, Loader2 } from 'lucide-vue-next'
import { useUserStore } from '../stores/userStore' 
import { storeToRefs } from 'pinia'

const userStore = useUserStore()

const { user, loading, userId, token } = storeToRefs(userStore)

const isAddingShoe = ref(false)

const newShoe = ref({ 
  brand_model: '', 
  shoe_type: 'Баскетбольні', 
  surface_type: 'Паркет',
  initial_wear_percentage: 0 
})

// --- ШІ КАЛЬКУЛЯТОР ---
const calculatedMaxLifespan = computed(() => {
  if (!user.value) return 80
  
  const base = 80.0
  const weight = user.value.weight_kg
  
  let rawWeightCoeff = 1.0 - (weight - 85) * 0.01
  const weightCoeff = Math.max(0.75, Math.min(1.25, rawWeightCoeff))
  
  const surfaceCoeff = 
    newShoe.value.surface_type === 'Асфальт' ? 0.5 : 
    newShoe.value.surface_type === 'Гібрид (Мікс)' ? 0.75 : 
    newShoe.value.surface_type === 'Гума/Тартан' ? 0.8 : 1.0;
    
  const typeCoeff = newShoe.value.shoe_type === 'Баскетбольні' ? 1.0 : 0.7

  return Math.round(base * weightCoeff * surfaceCoeff * typeCoeff)
})

const calculatedCurrentHours = computed({
  get: () => {
    return Math.round((newShoe.value.initial_wear_percentage / 100) * calculatedMaxLifespan.value)
  },
  set: (val) => {
    const safeMax = calculatedMaxLifespan.value > 0 ? calculatedMaxLifespan.value : 1;
    let percent = (val / safeMax) * 100
    newShoe.value.initial_wear_percentage = Math.min(100, Math.max(0, Math.round(percent)))
  }
})

// ==========================================
// --- МЕРЕЖЕВІ ЗАПИТИ З JWT ТОКЕНОМ ---
// ==========================================

const addShoe = async () => {
  // Захист офлайну
  if (!navigator.onLine) {
    alert('Відсутнє підключення. Додавання кросівок наразі недоступне в офлайн-режимі.')
    return
  }

  isAddingShoe.value = true
  try {
    const API_URL = import.meta.env.VITE_API_URL || 'https://basketball-api-kyiv.onrender.com';
    const response = await fetch(`${API_URL}/api/users/${userId.value}/shoes`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.value}`
      },
      body: JSON.stringify(newShoe.value) 
    })
    
    if (!response.ok) throw new Error('Помилка сервера при збереженні')
    
    await userStore.fetchUser()
    
    newShoe.value.brand_model = ''
    newShoe.value.initial_wear_percentage = 0
  } catch (error) {
    alert('Не вдалося додати кросівки. Спробуйте пізніше.')
  } finally {
    isAddingShoe.value = false
  }
}

const deleteShoe = async (shoeId, shoeName) => {
  // Захист офлайну
  if (!navigator.onLine) {
    alert('Відсутнє підключення. Видалення кросівок наразі недоступне в офлайн-режимі.')
    return
  }

  if (!confirm(`Видалити кросівки ${shoeName}?`)) return
  
  try {
    const API_URL = import.meta.env.VITE_API_URL || 'https://basketball-api-kyiv.onrender.com';
    const response = await fetch(`${API_URL}/api/shoes/${shoeId}`, {
      method: 'DELETE', 
      headers: { 
        'Authorization': `Bearer ${token.value}`
      }
    })
    
    if (!response.ok) throw new Error('Помилка видалення')
    
    await userStore.fetchUser()
  } catch (error) {
    alert(error.message)
  }
}

onMounted(async () => {
  if (userId.value) {
    // Якщо дані ще не завантажені (наприклад користувач оновив сторінку прямо на /gear)
    if (!user.value) {
      await userStore.fetchUser()
    }
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

.add-shoe-form { 
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
}

.btn-primary:hover:not(:disabled) {
  background: #f57c00;
}

.btn-primary:disabled { 
  opacity: 0.7; 
  cursor: not-allowed;
}

.btn-delete { 
  background: transparent; 
  color: #b0bec5; 
  border: none; 
  cursor: pointer; 
  padding: 5px; 
  border-radius: 4px; 
  transition: all 0.2s;
}

.btn-delete:hover { 
  color: #e65100; 
  background: rgba(230, 81, 0, 0.1); 
}

.animate-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* ШІ Калькулятор */
.calculator-box { 
  background: rgba(255, 152, 0, 0.05); 
  border: 1px solid rgba(255, 152, 0, 0.3); 
  border-radius: 8px; 
  padding: 15px; 
}

.calc-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  font-size: 0.95em; 
}

.highlight-text { 
  color: #ff9800; 
  font-size: 1.2em; 
}

.calc-hint { 
  font-size: 0.8em; 
  color: #b0bec5; 
  margin: 5px 0 0 0; 
}

.wear-section {
  margin-top: 15px;
}

.wear-label {
  display: flex; 
  justify-content: space-between; 
  color: #b0bec5; 
  font-size: 0.85em; 
  margin-bottom: 8px;
}

.hybrid-input-row { 
  display: flex; 
  align-items: center; 
  gap: 15px; 
}

.range-slider { 
  flex: 1; 
  accent-color: #ff9800; 
  cursor: pointer; 
}

.hours-input-wrapper { 
  display: flex; 
  align-items: center; 
  background: #121212; 
  border: 1px solid #333; 
  border-radius: 6px; 
  padding-right: 10px; 
}

.mini-number { 
  border: none; 
  width: 60px; 
  text-align: center; 
  padding: 8px; 
}

.hours-label { 
  color: #b0bec5; 
  font-size: 0.85em; 
}

/* Сітка інвентарю */
.inventory-grid { 
  display: grid; 
  grid-template-columns: 1fr; 
  gap: 15px; 
}

@media (min-width: 600px) { 
  .inventory-grid { 
    grid-template-columns: 1fr 1fr; 
  } 
}

.shoe-card { 
  border-left: 4px solid #b0bec5; 
  padding: 15px; 
  display: flex; 
  flex-direction: column; 
}

.shoe-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: flex-start; 
}

.shoe-name { 
  font-size: 1.1em; 
  color: #fff; 
}

.shoe-tags { 
  display: flex; 
  gap: 5px; 
  margin: 10px 0; 
}

.tag { 
  background: #333; 
  color: #b0bec5; 
  font-size: 0.75em; 
  padding: 3px 8px; 
  border-radius: 12px; 
}

.surface-tag { 
  background: rgba(255, 152, 0, 0.2); 
  color: #ff9800; 
  border: 1px solid rgba(255, 152, 0, 0.3); 
}

/* Прогрес бар зносу */
.shoe-wear { 
  display: flex; 
  justify-content: space-between; 
  margin: 10px 0 5px 0; 
  font-size: 0.85em; 
  color: #b0bec5; 
}

.wear-bar { 
  width: 100%; 
  height: 6px; 
  border-radius: 3px; 
  overflow: hidden; 
}

.wear-bar::-webkit-progress-bar { 
  background-color: #333; 
}

.wear-bar::-webkit-progress-value { 
  background-color: #ff9800; 
}

.wear-bar.danger-bar::-webkit-progress-value { 
  background-color: #e65100; 
}

/* Статуси та попередження */
.text-danger { 
  color: #e65100 !important; 
}

.warning-text { 
  color: #e65100; 
  font-size: 0.8em; 
  margin: 10px 0 0 0; 
  font-weight: bold; 
}

.empty-text { 
  grid-column: 1 / -1; 
  text-align: center; 
  color: #b0bec5; 
  padding: 20px 0; 
}
</style>