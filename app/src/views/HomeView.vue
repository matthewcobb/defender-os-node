<template>
  <div class="home-view">
    <div class="battery-status">
      <div class="battery-card solar">
        <h2>Solar Battery</h2>
        <div class="battery-info">
          <div class="battery-level">
            <div class="level" :style="{ width: '75%' }"></div>
          </div>
          <div class="battery-details">
            <div class="stat">
              <span class="label">Charge</span>
              <span class="value">75%</span>
            </div>
            <div class="stat">
              <span class="label">Voltage</span>
              <span class="value">12.8V</span>
            </div>
            <div class="stat">
              <span class="label">Current</span>
              <span class="value">2.3A</span>
            </div>
          </div>
        </div>
      </div>

      <div class="battery-card leisure">
        <h2>Leisure Battery</h2>
        <div class="battery-info">
          <div class="battery-level">
            <div class="level" :style="{ width: '85%' }"></div>
          </div>
          <div class="battery-details">
            <div class="stat">
              <span class="label">Charge</span>
              <span class="value">85%</span>
            </div>
            <div class="stat">
              <span class="label">Voltage</span>
              <span class="value">13.2V</span>
            </div>
            <div class="stat">
              <span class="label">Current</span>
              <span class="value">0.8A</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Home view component displaying solar and leisure battery status
</script>

<style lang="scss" scoped>

.battery-status {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.battery-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;

  h2 {
    margin-top: 0;
    margin-bottom: 1rem;
    font-size: 1.2rem;
  }
}

.battery-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.battery-level {
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.level {
  height: 100%;
  border-radius: 10px;
}

.solar {
  .level {
    background: linear-gradient(90deg, #FFD700, #FFA500);
  }
}

.leisure {
  .level {
    background: linear-gradient(90deg, #00BCD4, #2196F3);
  }
}

.battery-details {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.label {
  font-size: 0.8rem;
  color: #aaa;
  margin-bottom: 0.25rem;
}

.value {
  font-size: 1.1rem;
  font-weight: bold;
}
</style>