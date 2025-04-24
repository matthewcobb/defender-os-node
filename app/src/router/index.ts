import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SettingsView from '../views/SettingsView.vue'
import AboutView from '../views/AboutView.vue'
import ReverseView from '../views/ReverseView.vue'
import BatteryView from '../views/BatteryView.vue'
import SolarView from '../views/SolarView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/home'
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