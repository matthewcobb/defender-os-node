<template>
  <div class="about-view">
    <h1>About Defender OS</h1>

    <div class="about-section">
      <h2>Version Information</h2>
      <div class="info-row">
        <span class="info-label">Defender OS:</span>
        <span class="info-value">v0.1.0</span>
      </div>
      <div class="info-row">
        <span class="info-label">Node Version:</span>
        <span class="info-value">v18.12.1</span>
      </div>
      <div class="info-row">
        <span class="info-label">Vue Version:</span>
        <span class="info-value">v3.4.21</span>
      </div>
    </div>

    <div class="about-section">
      <h2>System Information</h2>
      <div class="info-row">
        <span class="info-label">Device:</span>
        <span class="info-value">Raspberry Pi 4</span>
      </div>
      <div class="info-row">
        <span class="info-label">CPU:</span>
        <span class="info-value">BCM2711 Quad-core Cortex-A72</span>
      </div>
      <div class="info-row">
        <span class="info-label">Memory:</span>
        <span class="info-value">4GB LPDDR4</span>
      </div>
      <div class="info-row">
        <span class="info-label">Storage:</span>
        <span class="info-value">32GB SD Card</span>
      </div>
    </div>

    <div class="about-section">
      <h2>Contributors</h2>
      <p>Defender OS is an open-source project developed by Land Rover enthusiasts.</p>
      <div class="contributors">
        <div class="contributor">
          <div class="avatar">MC</div>
          <div class="name">Matthew Cobb</div>
        </div>
        <div class="contributor">
          <div class="avatar">RM</div>
          <div class="name">Rhys Morgan</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// About view component
</script>

<style lang="scss" scoped>
.about-view {
}


.about-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.info-row {
  display: flex;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  &:last-child {
    border-bottom: none;
  }
}

.info-label {
  width: 40%;
  font-weight: 500;
}

.info-value {
  width: 60%;
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
  background: #4CAF50;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.name {
  font-size: 0.9rem;
}
</style>