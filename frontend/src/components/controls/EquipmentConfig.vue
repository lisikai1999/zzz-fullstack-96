<template>
  <div class="equipment-config">
    <h3>Equipment</h3>
    <label>
      Focal length (mm)
      <input v-model.number="sessionStore.focalLength" type="number" min="50" max="10000" />
    </label>
    <label>
      Sensor W (mm)
      <input v-model.number="sessionStore.sensorWidth" type="number" min="1" max="100" step="0.1" />
    </label>
    <label>
      Sensor H (mm)
      <input v-model.number="sessionStore.sensorHeight" type="number" min="1" max="100" step="0.1" />
    </label>
    <label>
      Camera rotation
      <div class="rotation-row">
        <input
          v-model.number="sessionStore.fovRotation"
          type="range" min="0" max="360" step="1"
          class="rotation-slider"
        />
        <span class="rotation-val">{{ sessionStore.fovRotation }}°</span>
      </div>
    </label>
    <div class="fov-info" v-if="fov">
      FOV: {{ fov.fov_width_arcmin.toFixed(1) }}' &times; {{ fov.fov_height_arcmin.toFixed(1) }}'
      ({{ fov.fov_width_deg.toFixed(2) }}° &times; {{ fov.fov_height_deg.toFixed(2) }}°)
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useSessionStore } from '../../stores/session'
import { api } from '../../api/client'

const sessionStore = useSessionStore()
const fov = ref(null)

async function updateFov() {
  try {
    fov.value = await api.getFov(
      sessionStore.focalLength,
      sessionStore.sensorWidth,
      sessionStore.sensorHeight
    )
  } catch (e) {
    fov.value = null
  }
}

watch(
  () => [sessionStore.focalLength, sessionStore.sensorWidth, sessionStore.sensorHeight],
  updateFov,
  { immediate: true }
)
</script>

<style scoped>
.equipment-config {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
}

.equipment-config h3 {
  font-size: 13px;
  color: #8b949e;
  margin-bottom: 8px;
}

.equipment-config label {
  display: block;
  font-size: 12px;
  color: #8b949e;
  margin-bottom: 6px;
}

.equipment-config input[type="number"] {
  width: 100%;
  margin-top: 2px;
}

.rotation-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.rotation-slider {
  flex: 1;
  accent-color: #f0883e;
}

.rotation-val {
  font-size: 12px;
  min-width: 36px;
  color: #f0883e;
  font-weight: 600;
}

.fov-info {
  margin-top: 10px;
  font-size: 13px;
  color: #58a6ff;
  padding-top: 8px;
  border-top: 1px solid #21262d;
}
</style>
