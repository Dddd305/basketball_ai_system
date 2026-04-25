import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  server: {
    host: true, 
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  plugins: [
    vue(),
    VitePWA({ 
      registerType: 'autoUpdate',
      // Включаємо підтримку розробки (тепер PWA можна дебажити без build)
      devOptions: {
        enabled: true,
        type: 'module' // <-- ДОДАЙ ЦЕЙ РЯДОК! Без нього dev-режим блокує PWA
      },
      // Налаштування стратегії кешування
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,vue}'], // Кешуємо все для офлайну
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true
      },
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'AI Basketball Tracker',
        short_name: 'AI Hoops',
        description: 'Система моніторингу навантаження та ШІ-планування для баскетболістів',
        theme_color: '#ff9800',
        background_color: '#121212',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        orientation: 'portrait',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable' // Важливо для Android
          },
          {
            src: 'apple-touch-icon.png',
            sizes: '180x180',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})