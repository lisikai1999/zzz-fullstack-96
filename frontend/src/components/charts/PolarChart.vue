<template>
  <div class="polar-chart-container">
    <h3>Sky Chart <span class="visible-count" v-if="visibleCount">({{ visibleCount }} visible)</span></h3>
    <div ref="chartEl" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as d3 from 'd3'
import { useLocationStore } from '../../stores/location'
import { useSessionStore } from '../../stores/session'
import { useTargetStore } from '../../stores/targets'
import { api } from '../../api/client'

const chartEl = ref(null)
const locationStore = useLocationStore()
const sessionStore = useSessionStore()
const targetStore = useTargetStore()
const visibleCount = ref(0)

const SIZE = 420
const MARGIN = 34
const RADIUS = (SIZE - 2 * MARGIN) / 2
const CX = SIZE / 2
const CY = SIZE / 2

function altToR(alt) {
  return ((90 - alt) / 90) * RADIUS
}

function azAltToXY(az, alt) {
  const r = altToR(alt)
  const rad = (az - 90) * Math.PI / 180
  return [CX + r * Math.cos(rad), CY + r * Math.sin(rad)]
}

async function render() {
  if (!chartEl.value) return
  const loc = locationStore.activeLocation
  if (!loc) return

  d3.select(chartEl.value).selectAll('*').remove()

  const svg = d3.select(chartEl.value)
    .append('svg')
    .attr('viewBox', `0 0 ${SIZE} ${SIZE}`)
    .attr('width', '100%')

  // Background
  svg.append('circle')
    .attr('cx', CX).attr('cy', CY).attr('r', RADIUS)
    .attr('fill', '#080d14').attr('stroke', '#30363d')

  // Altitude rings
  ;[0, 30, 60].forEach(alt => {
    svg.append('circle')
      .attr('cx', CX).attr('cy', CY).attr('r', altToR(alt))
      .attr('fill', 'none')
      .attr('stroke', alt === 0 ? '#30363d' : '#1c2128')
      .attr('stroke-dasharray', alt > 0 ? '2,4' : 'none')
    if (alt > 0) {
      svg.append('text')
        .attr('x', CX + 4).attr('y', CY - altToR(alt) + 12)
        .attr('fill', '#484f58').attr('font-size', 9)
        .text(`${alt}°`)
    }
  })

  // Cardinal directions + intermediate
  const dirs = [
    { label: 'N', angle: 0 }, { label: 'NE', angle: 45 },
    { label: 'E', angle: 90 }, { label: 'SE', angle: 135 },
    { label: 'S', angle: 180 }, { label: 'SW', angle: 225 },
    { label: 'W', angle: 270 }, { label: 'NW', angle: 315 },
  ]
  dirs.forEach(({ label, angle }) => {
    const rad = (angle - 90) * Math.PI / 180
    const isCardinal = label.length === 1
    svg.append('line')
      .attr('x1', CX).attr('y1', CY)
      .attr('x2', CX + RADIUS * Math.cos(rad))
      .attr('y2', CY + RADIUS * Math.sin(rad))
      .attr('stroke', '#1c2128').attr('stroke-width', isCardinal ? 0.8 : 0.4)

    const labelR = RADIUS + (isCardinal ? 15 : 12)
    svg.append('text')
      .attr('x', CX + labelR * Math.cos(rad))
      .attr('y', CY + labelR * Math.sin(rad))
      .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
      .attr('fill', isCardinal ? '#8b949e' : '#484f58')
      .attr('font-size', isCardinal ? 12 : 9)
      .attr('font-weight', isCardinal ? 600 : 400)
      .text(label)
  })

  // Batch fetch all visible targets (single API call)
  let targets = []
  try {
    const res = await api.getVisibleTargets(loc.id)
    targets = res.targets
    visibleCount.value = res.visible_count
  } catch (e) { return }

  // Plot targets
  const g = svg.append('g').attr('class', 'targets')
  for (const t of targets) {
    const [x, y] = azAltToXY(t.azimuth, t.altitude)
    const mag = t.magnitude || 10
    const dotR = Math.max(1.5, 5.5 - mag / 2.5)
    const isSelected = targetStore.selectedTarget?.id === t.id

    g.append('circle')
      .attr('cx', x).attr('cy', y)
      .attr('r', isSelected ? dotR + 3 : dotR)
      .attr('fill', isSelected ? '#58a6ff' : typeColor(t.object_type))
      .attr('opacity', isSelected ? 1 : 0.8)
      .attr('stroke', isSelected ? '#79c0ff' : 'none')
      .attr('stroke-width', isSelected ? 1.5 : 0)
      .attr('cursor', 'pointer')
      .on('click', () => {
        api.getTarget(t.id).then(full => targetStore.select(full))
      })
      .append('title')
      .text(`${t.designation}${t.common_name ? ' (' + t.common_name + ')' : ''}\nAlt: ${t.altitude}° Az: ${t.azimuth}°\nMag: ${t.magnitude || '?'}`)

    if (isSelected || (mag !== null && mag < 5.5)) {
      g.append('text')
        .attr('x', x + dotR + 3).attr('y', y + 3)
        .attr('fill', isSelected ? '#58a6ff' : '#6e7681')
        .attr('font-size', isSelected ? 11 : 9)
        .attr('font-weight', isSelected ? 600 : 400)
        .text(t.designation)
    }
  }

  // FOV rectangle for selected target
  const selected = targetStore.selectedTarget
  if (selected) {
    const vis = targets.find(t => t.id === selected.id)
    if (vis && vis.altitude > 0) {
      try {
        const fov = await api.getFov(
          sessionStore.focalLength, sessionStore.sensorWidth, sessionStore.sensorHeight
        )
        const fovWPx = (fov.fov_width_deg / 90) * RADIUS
        const fovHPx = (fov.fov_height_deg / 90) * RADIUS
        const [x, y] = azAltToXY(vis.azimuth, vis.altitude)
        const angle = sessionStore.fovRotation || 0

        svg.append('rect')
          .attr('x', -fovWPx / 2).attr('y', -fovHPx / 2)
          .attr('width', fovWPx).attr('height', fovHPx)
          .attr('fill', 'rgba(240, 136, 62, 0.08)')
          .attr('stroke', '#f0883e')
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '4,2')
          .attr('transform', `translate(${x},${y}) rotate(${angle})`)

        // Crosshair
        svg.append('line')
          .attr('x1', x - 5).attr('y1', y)
          .attr('x2', x + 5).attr('y2', y)
          .attr('stroke', '#f0883e').attr('stroke-width', 0.7)
        svg.append('line')
          .attr('x1', x).attr('y1', y - 5)
          .attr('x2', x).attr('y2', y + 5)
          .attr('stroke', '#f0883e').attr('stroke-width', 0.7)
      } catch (e) {}
    }
  }
}

function typeColor(type) {
  switch (type) {
    case 'Galaxy': return '#a371f7'
    case 'Nebula': return '#7ee787'
    case 'Supernova Remnant': return '#7ee787'
    case 'Open Cluster': return '#ffa657'
    case 'Globular Cluster': return '#f8e3a1'
    case 'Planetary Nebula': return '#79c0ff'
    default: return '#c9d1d9'
  }
}

onMounted(render)
watch(
  () => [locationStore.activeLocation, sessionStore.selectedDate,
         targetStore.selectedTarget, sessionStore.focalLength,
         sessionStore.sensorWidth, sessionStore.sensorHeight,
         sessionStore.fovRotation],
  render,
  { deep: true }
)
</script>

<style scoped>
.polar-chart-container {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
}

.polar-chart-container h3 {
  font-size: 13px;
  color: #8b949e;
  margin-bottom: 8px;
}

.visible-count {
  font-weight: 400;
  color: #484f58;
}

.chart {
  width: 100%;
  aspect-ratio: 1;
}
</style>
