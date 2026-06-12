<template>
  <div class="observation-calendar">
    <div class="cal-header">
      <div v-for="d in weekDays" :key="d" class="cal-header-cell">{{ d }}</div>
    </div>
    <div class="cal-grid">
      <div
        v-for="(cell, i) in grid"
        :key="i"
        class="cal-cell"
        :class="{ empty: !cell, clickable: !!cell }"
        @click="cell && emit('selectDay', cell.date)"
      >
        <template v-if="cell">
          <span class="day-num">{{ cell.dayNum }}</span>
          <span class="score-bar" :style="{ background: scoreColor(cell.quality_score), width: (cell.quality_score * 100) + '%' }"></span>
          <span class="moon">{{ moonIcon(cell.moon_illumination) }}</span>
          <span class="hours" v-if="cell.window_hours > 0">{{ cell.window_hours.toFixed(1) }}h</span>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  days: { type: Array, default: () => [] },
  year: Number,
  month: Number,
})

const emit = defineEmits(['selectDay'])

const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const grid = computed(() => {
  if (!props.days.length) return []
  const firstDay = new Date(props.year, props.month - 1, 1)
  let dow = firstDay.getDay()
  dow = dow === 0 ? 6 : dow - 1 // Monday = 0

  const cells = []
  for (let i = 0; i < dow; i++) cells.push(null)
  for (const d of props.days) {
    cells.push({ ...d, dayNum: parseInt(d.date.split('-')[2]) })
  }
  return cells
})

function scoreColor(score) {
  if (score >= 0.7) return '#3fb950'
  if (score >= 0.4) return '#d29922'
  if (score > 0) return '#f85149'
  return '#21262d'
}

function moonIcon(illum) {
  if (illum < 0.1) return '\u{1F311}'
  if (illum < 0.35) return '\u{1F312}'
  if (illum < 0.65) return '\u{1F313}'
  if (illum < 0.9) return '\u{1F314}'
  return '\u{1F315}'
}
</script>

<style scoped>
.cal-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 4px;
}

.cal-header-cell {
  text-align: center;
  font-size: 12px;
  color: #8b949e;
  padding: 4px;
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.cal-cell {
  background: #161b22;
  border: 1px solid #21262d;
  border-radius: 6px;
  padding: 6px;
  min-height: 70px;
  position: relative;
}

.cal-cell.clickable {
  cursor: pointer;
}

.cal-cell.clickable:hover {
  border-color: #58a6ff;
}

.cal-cell.empty {
  background: transparent;
  border: none;
}

.day-num {
  font-size: 13px;
  font-weight: 600;
}

.score-bar {
  display: block;
  height: 3px;
  border-radius: 2px;
  margin-top: 4px;
}

.moon {
  display: block;
  font-size: 14px;
  margin-top: 2px;
}

.hours {
  font-size: 11px;
  color: #8b949e;
}
</style>
