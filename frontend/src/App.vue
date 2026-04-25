<template>
  <div id="app-container">
    
    <transition name="slide-down">
      <div v-if="isOffline" class="offline-banner">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="1" y1="1" x2="23" y2="23"></line>
          <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"></path>
          <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"></path>
          <path d="M10.71 5.05A16 16 0 0 1 22.58 9"></path>
          <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"></path>
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
          <line x1="12" y1="20" x2="12.01" y2="20"></line>
        </svg>
        <span>Офлайн: доступний тільки перегляд</span>
      </div>
    </transition>

    <main class="main-content" :class="{ 'with-bottom-nav': !hideBottomNav }">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <nav v-if="!hideBottomNav" class="bottom-nav">
      
      <router-link to="/dashboard" class="nav-item" active-class="active">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
        <span>Головна</span>
      </router-link>

      <router-link to="/activity" class="nav-item" active-class="active">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
        <span>Активність</span>
      </router-link>

      <router-link to="/gear" class="nav-item" active-class="active">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"></path><line x1="16" y1="8" x2="2" y2="22"></line><line x1="17.5" y1="15" x2="9" y2="6.5"></line>
        </svg>
        <span>Інвентар</span>
      </router-link>

    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue' // Додано хуки
import { useRoute } from 'vue-router'

const route = useRoute()

const hideBottomNav = computed(() => {
  return route.meta.hideBottomNav || false
})

// ==========================================
// --- ЛОГІКА ІНДИКАТОРА МЕРЕЖІ ---
// ==========================================
const isOffline = ref(!navigator.onLine)

const updateOnlineStatus = () => {
  isOffline.value = !navigator.onLine
}

onMounted(() => {
  // Слухаємо системні події браузера про зміну статусу мережі
  window.addEventListener('online', updateOnlineStatus)
  window.addEventListener('offline', updateOnlineStatus)
})

onUnmounted(() => {
  // Прибираємо слухачів, якщо компонент знищується
  window.removeEventListener('online', updateOnlineStatus)
  window.removeEventListener('offline', updateOnlineStatus)
})
</script>

<style>
/* Базові глобальні стилі для всього додатку */
body {
  margin: 0;
  padding: 0;
  background-color: #121212;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #ffffff;
  -webkit-user-select: none;
  user-select: none;
}

#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
}
.with-bottom-nav {
  padding-bottom: 70px; 
}

/* ДОДАНО: Стилі офлайн-банера */
.offline-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background-color: #e65100; /* Темно-помаранчевий/Червоний колір небезпеки */
  color: white;
  text-align: center;
  padding: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  z-index: 2000;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  /* Відступ для сучасних смартфонів з камерою на екрані */
  padding-top: calc(10px + env(safe-area-inset-top));
}

/* Анімація появи банера зверху */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* Дизайн нижньої панелі */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 65px;
  background-color: #1e1e1e;
  border-top: 1px solid #333;
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 1000;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
  padding-bottom: env(safe-area-inset-bottom);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #b0bec5;
  text-decoration: none;
  font-size: 0.75rem;
  gap: 4px;
  width: 33%;
  transition: all 0.3s ease;
}

.nav-item svg {
  transition: transform 0.2s ease, stroke 0.2s ease;
}

/* Активний стан вкладки */
.nav-item.active {
  color: #ff9800;
  font-weight: bold;
}

.nav-item.active svg {
  stroke: #ff9800;
  transform: translateY(-2px);
}

/* Плавна анімація зміни сторінок */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>