<template>
  <div class="altitude-curve-container">
    <h3>
      Altitude Curve
      <span class="curve-legend">
        <span class="leg-target">Target</span>
        <span class="leg-moon">Moon</span>
        <span class="leg-window">Best Window</span>
      </span>
    </h3>
    <div ref="chartEl" class="chart"></div>
    <div class="twilight-legend">
      <span class="tw-item"><i style="background:#2d333b"></i>Day</span>
      <span class="tw-item"><i style="background:#1c2d4a"></i>Civil</span>
      <span class="tw-item"><i style="background:#121d33"></i>Nautical</span>
      <span class="tw-item"><i style="background:#0a1220"></i>Astronomical</span>
      <span class="tw-item"><i style="background:#060b12"></i>Night</span>
    </div>
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

const WIDTH = 560
const HEIGHT = 320
const MARGIN = { top: 16, right: 16, bottom: 36, left: 42 }

async function render() {
  if (!chartEl.value) return
  const loc = locationStore.activeLocation
  const target = targetStore.selectedTarget
  d3.select(chartEl.value).selectAll('*').remove()

  if (!loc || !target) {
    d3.select(chartEl.value).append('div')
      .attr('class', 'empty-msg')
      .text('Select a target to view altitude curve')
    return
  }

  let curveData, twilight, moonData, obsWindow
  try {
    ;[curveData, twilight, moonData, obsWindow] = await Promise.all([
      api.getAltitudeCurve(target.id, loc.id, sessionStore.selectedDate),
      api.getTwilight(loc.id, sessionStore.selectedDate),
      api.getMoon(loc.id, sessionStore.selectedDate),
      api.getObservationWindow(target.id, loc.id, sessionStore.selectedDate),
    ])
  } catch (e) { return }

  const svg = d3.select(chartEl.value)
    .append('svg')
    .attr('viewBox', `0 0 ${WIDTH} ${HEIGHT}`)
    .attr('width', '100%')
    .attr('preserveAspectRatio', 'xMidYMid meet')

  const w = WIDTH - MARGIN.left - MARGIN.right
  const h = HEIGHT - MARGIN.top - MARGIN.bottom
  const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`)

  // Parse time data
  const points = curveData.points.map(p => ({
    time: new Date(p.time_utc),
    alt: p.altitude,
  }))
  const moonPoints = moonData.altitude_curve.map(p => ({
    time: new Date(p.time_utc),
    alt: p.altitude,
  }))

  const timeExtent = d3.extent(points, d => d.time)
  const xScale = d3.scaleTime().domain(timeExtent).range([0, w])
  const yScale = d3.scaleLinear().domain([-10, 90]).range([h, 0])

  // === TWILIGHT BACKGROUND BANDS ===
  // Fill entire chart background with sky state color at each time slice
  const sliceWidth = w / points.length
  const twilightEvents = buildTwilightTimeline(twilight, timeExtent)

  // Draw twilight as continuous background
  g.append('rect')
    .attr('x', 0).attr('y', 0).attr('width', w).attr('height', h)
    .attr('fill', '#2d333b') // daytime base

  twilightEvents.forEach(band => {
    const x1 = Math.max(0, xScale(band.start))
    const x2 = Math.min(w, xScale(band.end))
    if (x2 > x1) {
      g.append('rect')
        .attr('x', x1).attr('y', 0)
        .attr('width', x2 - x1).attr('height', h)
        .attr('fill', band.color)
    }
  })

  // === BEST OBSERVATION WINDOW HIGHLIGHT ===
  if (obsWindow && obsWindow.optimal_start && obsWindow.optimal_end) {
    const ws = new Date(obsWindow.optimal_start)
    const we = new Date(obsWindow.optimal_end)
    const x1 = xScale(ws)
    const x2 = xScale(we)
    if (x2 > x1) {
      g.append('rect')
        .attr('x', x1).attr('y', 0)
        .attr('width', x2 - x1).attr('height', h)
        .attr('fill', 'rgba(63, 185, 80, 0.12)')
        .attr('stroke', '#3fb950')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '4,3')

      // Label
      g.append('text')
        .attr('x', (x1 + x2) / 2).attr('y', 12)
        .attr('text-anchor', 'middle')
        .attr('fill', '#3fb950').attr('font-size', 10).attr('font-weight', 600)
        .text(`Best: ${formatHM(ws)}-${formatHM(we)}`)
    }
  }

  // === GRID LINES ===
  ;[0, 30, 60].forEach(alt => {
    g.append('line')
      .attr('x1', 0).attr('y1', yScale(alt))
      .attr('x2', w).attr('y2', yScale(alt))
      .attr('stroke', '#30363d')
      .attr('stroke-dasharray', alt === 0 ? 'none' : '3,5')
      .attr('stroke-width', alt === 0 ? 1 : 0.5)
  })

  // 30° label
  g.append('text')
    .attr('x', w - 2).attr('y', yScale(30) - 3)
    .attr('text-anchor', 'end').attr('fill', '#484f58').attr('font-size', 9)
    .text('30°')

  // === MOON ALTITUDE (dashed, with fill) ===
  const moonAbove = moonPoints.filter(p => p.time >= timeExtent[0] && p.time <= timeExtent[1])
  const moonArea = d3.area()
    .x(d => xScale(d.time))
    .y0(h)
    .y1(d => yScale(Math.max(-10, d.alt)))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(moonAbove.filter(d => d.alt > 0))
    .attr('d', moonArea)
    .attr('fill', 'rgba(139, 148, 158, 0.06)')

  const moonLine = d3.line()
    .x(d => xScale(d.time))
    .y(d => yScale(Math.max(-10, d.alt)))
    .defined(d => d.alt > -10)
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(moonAbove)
    .attr('d', moonLine)
    .attr('fill', 'none')
    .attr('stroke', '#6e7681')
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '5,3')

  // Moon illumination label
  g.append('text')
    .attr('x', w - 2).attr('y', h - 4)
    .attr('text-anchor', 'end')
    .attr('fill', '#6e7681').attr('font-size', 9)
    .text(`Moon ${(moonData.illumination * 100).toFixed(0)}% ${moonData.phase_name}`)

  // === TARGET ALTITUDE LINE ===
  const targetArea = d3.area()
    .x(d => xScale(d.time))
    .y0(yScale(0))
    .y1(d => yScale(Math.max(0, d.alt)))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(points.filter(d => d.alt > 0))
    .attr('d', targetArea)
    .attr('fill', 'rgba(88, 166, 255, 0.1)')

  const targetLine = d3.line()
    .x(d => xScale(d.time))
    .y(d => yScale(Math.max(-10, d.alt)))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(points)
    .attr('d', targetLine)
    .attr('fill', 'none')
    .attr('stroke', '#58a6ff')
    .attr('stroke-width', 2.5)

  // Transit marker
  if (curveData.transit_time) {
    const tTime = new Date(curveData.transit_time)
    if (tTime >= timeExtent[0] && tTime <= timeExtent[1]) {
      const tx = xScale(tTime)
      const ty = yScale(curveData.max_altitude)
      g.append('circle')
        .attr('cx', tx).attr('cy', ty).attr('r', 4)
        .attr('fill', '#58a6ff').attr('stroke', '#fff').attr('stroke-width', 1)
      g.append('text')
        .attr('x', tx).attr('y', ty - 8)
        .attr('text-anchor', 'middle').attr('fill', '#58a6ff').attr('font-size', 9)
        .text(`${curveData.max_altitude.toFixed(1)}°`)
    }
  }

  // === AXES ===
  const xAxis = d3.axisBottom(xScale)
    .ticks(8)
    .tickFormat(d3.timeFormat('%H:%M'))

  g.append('g')
    .attr('transform', `translate(0,${h})`)
    .call(xAxis)
    .selectAll('text').attr('fill', '#8b949e').attr('font-size', 10)

  g.selectAll('.domain, .tick line').attr('stroke', '#30363d')

  const yAxis = d3.axisLeft(yScale)
    .tickValues([0, 30, 60, 90])
    .tickFormat(d => `${d}°`)

  g.append('g')
    .call(yAxis)
    .selectAll('text').attr('fill', '#8b949e').attr('font-size', 10)

  g.selectAll('.domain').remove()

  // Rise/Set markers
  if (curveData.rise_time) {
    const rt = new Date(curveData.rise_time)
    if (rt >= timeExtent[0] && rt <= timeExtent[1]) {
      g.append('text')
        .attr('x', xScale(rt)).attr('y', yScale(0) + 12)
        .attr('text-anchor', 'middle').attr('fill', '#58a6ff').attr('font-size', 9)
        .text(`↑${formatHM(rt)}`)
    }
  }
  if (curveData.set_time) {
    const st = new Date(curveData.set_time)
    if (st >= timeExtent[0] && st <= timeExtent[1]) {
      g.append('text')
        .attr('x', xScale(st)).attr('y', yScale(0) + 12)
        .attr('text-anchor', 'middle').attr('fill', '#58a6ff').attr('font-size', 9)
        .text(`↓${formatHM(st)}`)
    }
  }
}

function buildTwilightTimeline(tw, [tStart, tEnd]) {
  const bands = []
  const events = []

  // Collect all events and sort by time
  const keys = ['sunset', 'civil_dusk', 'nautical_dusk', 'astro_dusk',
                'astro_dawn', 'nautical_dawn', 'civil_dawn', 'sunrise']
  for (const k of keys) {
    if (tw[k]) events.push({ key: k, time: new Date(tw[k]) })
  }
  events.sort((a, b) => a.time - b.time)

  // Map twilight state between events to colors
  const colorMap = {
    day: '#2d333b',
    civil: '#1c2d4a',
    nautical: '#121d33',
    astronomical: '#0a1220',
    night: '#060b12',
  }

  // Determine state for each interval
  function stateAfter(key) {
    switch (key) {
      case 'sunset': return 'civil'
      case 'civil_dusk': return 'nautical'
      case 'nautical_dusk': return 'astronomical'
      case 'astro_dusk': return 'night'
      case 'astro_dawn': return 'astronomical'
      case 'nautical_dawn': return 'nautical'
      case 'civil_dawn': return 'civil'
      case 'sunrise': return 'day'
      default: return 'day'
    }
  }

  // Build timeline
  let prevTime = tStart
  let currentState = 'day'

  // If first event is a dawn event, we start in night
  if (events.length > 0) {
    const firstKey = events[0].key
    if (firstKey.includes('dawn') || firstKey === 'sunrise') {
      currentState = 'night'
    } else if (firstKey === 'astro_dusk') {
      currentState = 'astronomical'
    } else if (firstKey === 'nautical_dusk') {
      currentState = 'nautical'
    } else if (firstKey === 'civil_dusk') {
      currentState = 'civil'
    }
  }

  // Determine initial state by checking if we're past certain events
  // Simpler: check sun altitude conceptually - if time range starts after sunset, figure out state
  for (const ev of events) {
    if (ev.time > tStart && ev.time < tEnd) {
      bands.push({ start: prevTime, end: ev.time, color: colorMap[currentState] })
      currentState = stateAfter(ev.key)
      prevTime = ev.time
    } else if (ev.time <= tStart) {
      currentState = stateAfter(ev.key)
    }
  }
  bands.push({ start: prevTime, end: tEnd, color: colorMap[currentState] })

  return bands
}

function formatHM(d) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

onMounted(render)
watch(
  () => [locationStore.activeLocation, sessionStore.selectedDate, targetStore.selectedTarget],
  render,
  { deep: true }
)
</script>

<style scoped>
.altitude-curve-container {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
}

.altitude-curve-container h3 {
  font-size: 13px;
  color: #8b949e;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.curve-legend {
  font-weight: 400;
  font-size: 11px;
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.leg-target::before { content: ''; display: inline-block; width: 12px; height: 3px; background: #58a6ff; margin-right: 3px; vertical-align: middle; }
.leg-moon::before { content: ''; display: inline-block; width: 12px; height: 2px; border-top: 2px dashed #6e7681; margin-right: 3px; vertical-align: middle; }
.leg-window::before { content: ''; display: inline-block; width: 12px; height: 8px; background: rgba(63,185,80,0.3); border: 1px solid #3fb950; margin-right: 3px; vertical-align: middle; }

.leg-target { color: #58a6ff; }
.leg-moon { color: #6e7681; }
.leg-window { color: #3fb950; }

.chart {
  width: 100%;
}

.twilight-legend {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  justify-content: center;
}

.tw-item {
  font-size: 10px;
  color: #6e7681;
  display: flex;
  align-items: center;
  gap: 3px;
}

.tw-item i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  border: 1px solid #30363d;
}

:deep(.empty-msg) {
  text-align: center;
  color: #484f58;
  padding: 60px 0;
  font-size: 14px;
}
</style>
