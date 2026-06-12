<template>
  <div class="planner">
    <div class="planner-sidebar">
      <TargetSearch />
      <EquipmentConfig />
      <div class="tonight-list" v-if="targetStore.tonightTargets.length">
        <h3>Tonight's Best</h3>
        <div
          v-for="t in targetStore.tonightTargets.slice(0, 10)"
          :key="t.target_id"
          class="tonight-item"
          :class="{ active: targetStore.selectedTarget?.id === t.target_id }"
          @click="selectTonight(t)"
        >
          <span class="designation">{{ t.designation }}</span>
          <span class="name">{{ t.common_name || '' }}</span>
          <span class="score" :style="{ color: scoreColor(t.quality_score) }">
            {{ (t.quality_score * 100).toFixed(0) }}%
          </span>
        </div>
      </div>
    </div>
    <div class="planner-main">
      <div class="charts-row">
        <PolarChart />
        <AltitudeCurve />
      </div>
      <div class="info-row" v-if="window">
        <div class="info-card">
          <h4>Observation Window</h4>
          <p>{{ formatTime(window.optimal_start) }} - {{ formatTime(window.optimal_end) }}</p>
          <p>Peak: {{ window.peak_altitude.toFixed(1) }} alt</p>
          <p>Moon separation: {{ window.moon_separation_deg.toFixed(0) }}</p>
          <p>Quality: {{ (window.quality_score * 100).toFixed(0) }}%</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useLocationStore } from '../stores/location'
import { useSessionStore } from '../stores/session'
import { useTargetStore } from '../stores/targets'
import { api } from '../api/client'
import TargetSearch from '../components/controls/TargetSearch.vue'
import EquipmentConfig from '../components/controls/EquipmentConfig.vue'
import PolarChart from '../components/charts/PolarChart.vue'
import AltitudeCurve from '../components/charts/AltitudeCurve.vue'

const locationStore = useLocationStore()
const sessionStore = useSessionStore()
const targetStore = useTargetStore()
const window = ref(null)

function scoreColor(score) {
  if (score >= 0.7) return '#3fb950'
  if (score >= 0.4) return '#d29922'
  return '#f85149'
}

function formatTime(iso) {
  if (!iso) return '--:--'
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function selectTonight(t) {
  const target = await api.getTarget(t.target_id)
  targetStore.select(target)
}

async function loadWindow() {
  const loc = locationStore.activeLocation
  const target = targetStore.selectedTarget
  if (!loc || !target) return
  window.value = await api.getObservationWindow(target.id, loc.id, sessionStore.selectedDate)
}

async function loadTonight() {
  const loc = locationStore.activeLocation
  if (!loc) return
  await targetStore.loadTonight(loc.id, sessionStore.selectedDate)
}

watch(
  () => [locationStore.activeLocation, sessionStore.selectedDate],
  () => { loadTonight(); loadWindow() },
  { deep: true }
)

watch(
  () => targetStore.selectedTarget,
  () => loadWindow()
)

onMounted(loadTonight)
</script>

<style scoped>
.planner {
  display: flex;
  gap: 24px;
}

.planner-sidebar {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.planner-main {
  flex: 1;
  min-width: 0;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.tonight-list h3 {
  font-size: 14px;
  margin-bottom: 8px;
  color: #8b949e;
}

.tonight-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.tonight-item:hover {
  background: #21262d;
}

.tonight-item.active {
  background: #1f3a5f;
}

.tonight-item .designation {
  font-weight: 600;
  min-width: 50px;
}

.tonight-item .name {
  flex: 1;
  color: #8b949e;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tonight-item .score {
  font-weight: 600;
}

.info-row {
  display: flex;
  gap: 16px;
}

.info-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 16px;
}

.info-card h4 {
  font-size: 13px;
  color: #8b949e;
  margin-bottom: 8px;
}

.info-card p {
  font-size: 14px;
  margin: 4px 0;
}
</style>
