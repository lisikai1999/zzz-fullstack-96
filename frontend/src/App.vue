<template>
  <div class="app">
    <header class="app-header">
      <h1>Deep Sky Planner</h1>
      <nav>
        <router-link to="/planner">Planner</router-link>
        <router-link to="/calendar">Calendar</router-link>
      </nav>
      <div class="header-controls">
        <LocationSelector />
        <DateTimePicker />
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useLocationStore } from './stores/location'
import LocationSelector from './components/controls/LocationSelector.vue'
import DateTimePicker from './components/controls/DateTimePicker.vue'

const locationStore = useLocationStore()
onMounted(() => locationStore.load())
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0d1117;
  color: #c9d1d9;
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
}

.app-header h1 {
  font-size: 18px;
  color: #58a6ff;
  white-space: nowrap;
}

.app-header nav {
  display: flex;
  gap: 12px;
}

.app-header nav a {
  color: #8b949e;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
}

.app-header nav a.router-link-active {
  color: #f0f6fc;
  background: #21262d;
}

.header-controls {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.app-main {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

input, select, button {
  font-family: inherit;
  font-size: 14px;
}

input, select {
  background: #0d1117;
  border: 1px solid #30363d;
  color: #c9d1d9;
  padding: 6px 10px;
  border-radius: 6px;
}

input:focus, select:focus {
  outline: none;
  border-color: #58a6ff;
}

button {
  background: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
}

button:hover {
  background: #30363d;
}

button.primary {
  background: #238636;
  border-color: #2ea043;
  color: #fff;
}

button.primary:hover {
  background: #2ea043;
}
</style>
