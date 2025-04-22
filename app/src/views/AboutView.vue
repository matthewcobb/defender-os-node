<template>
  <div class="about-view">
    <div class="panel">
      <h3>Version Information</h3>
      <div class="info-row">
        <h4>Defender OS:</h4>
        <h4>v{{ appVersion }}</h4>
      </div>
      <div class="info-row">
        <h4>Vue Version:</h4>
        <h4>v{{ vueVersion }}</h4>
      </div>
      <div v-if="systemInfo.platform" class="info-row">
        <h4>Platform:</h4>
        <h4>{{ systemInfo.platform }}</h4>
      </div>
    </div>

    <div class="panel">
      <h3>Contributors</h3>
      <small>
        Defender OS is an open-source project developed by Land Rover enthusiasts.
      </small>
      <div class="contributors">
        <div class="contributor">
          <div class="avatar">MC</div>
          <small>Matthew Cobb</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import pkg from '../../package.json';

const appVersion = ref(pkg.version);
const vueVersion = ref(pkg.dependencies.vue.replace('^', ''));
const systemInfo = reactive({
  platform: '',
  arch: '',
  uptime: 0
});
</script>

<style lang="scss" scoped>
.about-view {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.5rem;
}
.info-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  &:last-child {
    border-bottom: none;
  }
}

.contributors {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.contributor {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 0.5rem;
}
</style>