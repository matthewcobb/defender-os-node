<template>
  <div class="wedding-view">
    <WeddingComponent @close="closeWeddingMode" />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import WeddingComponent from '../components/WeddingComponent.vue';

const router = useRouter();

const closeWeddingMode = () => {
  router.push('/home');
};
</script>

<style scoped>
.wedding-view {
  height: 100%;
  width: 100%;
}
</style>