import '@fontsource/rubik/400.css'
import '@fontsource/rubik/500.css'
import '@fontsource/rubik/700.css'
import '@fontsource/rubik-mono-one'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './index.scss'
import App from './App.vue'
import router from './router'
import { initSocketIO } from './features/system/services/socketio'

const app = createApp(App)
const pinia = createPinia()

app.use(router)
app.use(pinia)

// Initialize Socket.IO connection
initSocketIO()

app.mount('#root')