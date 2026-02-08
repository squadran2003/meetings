import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import App from './App.vue'
import Home from './views/Home.vue'
import Meeting from './views/Meeting.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/meeting/:roomId', component: Meeting, props: true }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const vuetify = createVuetify({
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        colors: {
          primary: '#4f46e5',
          error: '#ef4444',
          surface: '#16213e',
          background: '#1a1a2e',
        }
      },
      light: {
        colors: {
          primary: '#4f46e5',
          error: '#ef4444',
          surface: '#f5f5f5',
          background: '#ffffff',
        }
      }
    }
  }
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(vuetify)
app.mount('#app')
