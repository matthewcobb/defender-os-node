import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SettingsView from '../views/SettingsView.vue'
import AboutView from '../views/AboutView.vue'
import ReverseView from '../views/ReverseView.vue'
import BatteryView from '../views/BatteryView.vue'
import SolarView from '../views/SolarView.vue'
import WeddingView from '../views/WeddingView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: () => {
        // Check if wedding mode is enabled
        const savedWeddingMode = localStorage.getItem('weddingMode');

        // If no saved setting, default to wedding mode on
        if (savedWeddingMode === null) {
          localStorage.setItem('weddingMode', 'true');
          return '/wedding';
        }

        // Otherwise use saved setting
        return savedWeddingMode === 'true' ? '/wedding' : '/home';
      }
    },
    {
      path: '/wedding',
      name: 'wedding',
      component: WeddingView
    },
    {
      path: '/home',
      name: 'home',
      component: HomeView
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView
    },
    {
      path: '/reverse',
      name: 'reverse',
      component: ReverseView
    },
    {
      path: '/battery',
      name: 'battery',
      component: BatteryView
    },
    {
      path: '/solar',
      name: 'solar',
      component: SolarView
    }
  ]
})

export default router