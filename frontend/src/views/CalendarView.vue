<template>
  <div class="calendar-view">
    <div class="calendar-header">
      <button @click="prevMonth">&lt;</button>
      <h2>{{ monthLabel }}</h2>
      <button @click="nextMonth">&gt;</button>
      <div class="calendar-target">
        <TargetSearch />
      </div>
    </div>
    <ObservationCalendar :days="days" :year="year" :month="month" @select-day="goToDay" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useLocationStore } from '../stores/location'
import { useSessionStore } from '../stores/session'
import { useTargetStore } from '../stores/targets'
import { api } from '../api/client'
import TargetSearch from '../components/controls/TargetSearch.vue'
import ObservationCalendar from '../components/calendar/ObservationCalendar.vue'

const router = useRouter()
const locationStore = useLocationStore()
const sessionStore = useSessionStore()
const targetStore = useTargetStore()

const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)
const days = ref([])

const monthLabel = computed(() => {
  const d = new Date(year.value, month.value - 1)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })
})

function prevMonth() {
  if (month.value === 1) { year.value--; month.value = 12 }
  else month.value--
  loadCalendar()
}

function nextMonth() {
  if (month.value === 12) { year.value++; month.value = 1 }
  else month.value++
  loadCalendar()
}

function goToDay(date) {
  sessionStore.setDate(date)
  router.push('/planner')
}

async function loadCalendar() {
  const loc = locationStore.activeLocation
  const target = targetStore.selectedTarget
  if (!loc || !target) {
    days.value = []
    return
  }
  const res = await api.getCalendar(target.id, loc.id, year.value, month.value)
  days.value = res.days
}

watch(
  () => [locationStore.activeLocation, targetStore.selectedTarget],
  loadCalendar,
  { deep: true }
)

onMounted(loadCalendar)
</script>

<style scoped>
.calendar-view {
  max-width: 900px;
}

.calendar-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.calendar-header h2 {
  min-width: 140px;
  text-align: center;
}

.calendar-target {
  margin-left: auto;
}
</style>
