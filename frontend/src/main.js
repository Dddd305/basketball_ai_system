import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 1. Імпортую функцію реєстрації PWA від нашого плагіна
import { registerSW } from 'virtual:pwa-register'

const app = createApp(App)

app.use(router)

app.mount('#app')

// 2. Ініціалізація Service Worker
if ('serviceWorker' in navigator) {
  registerSW({
    immediate: true, // Змушує додаток оновлюватися одразу, як тільки ти зміниш код
    onOfflineReady() {
      console.log('PWA: Додаток успішно закешовано. Тепер він працює без Інтернету! 🚀')
    },
    onNeedRefresh() {
      console.log('PWA: Знайдено нову версію додатка. Завантажую оновлення...')
    }
  })
}
