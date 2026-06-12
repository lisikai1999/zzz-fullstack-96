<template>
  <div class="location-selector">
    <select v-model="selected" @change="onChange">
      <option v-for="loc in locationStore.locations" :key="loc.id" :value="loc.id">
        {{ loc.name }}
      </option>
    </select>
    <button @click="showAdd = true" title="Add location">+</button>
    <div v-if="showAdd" class="add-form">
      <input v-model="form.name" placeholder="Name" />
      <input v-model.number="form.latitude" type="number" step="0.001" placeholder="Lat" />
      <input v-model.number="form.longitude" type="number" step="0.001" placeholder="Lon" />
      <input v-model.number="form.elevation" type="number" placeholder="Elev (m)" />
      <input v-model="form.timezone" placeholder="Timezone" />
      <button class="primary" @click="addLocation">Save</button>
      <button @click="showAdd = false">Cancel</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useLocationStore } from '../../stores/location'

const locationStore = useLocationStore()
const selected = ref(null)
const showAdd = ref(false)
const form = ref({ name: '', latitude: 40, longitude: 116, elevation: 50, timezone: 'Asia/Shanghai' })

watch(() => locationStore.activeLocation, (loc) => {
  if (loc) selected.value = loc.id
}, { immediate: true })

function onChange() {
  const loc = locationStore.locations.find((l) => l.id === selected.value)
  if (loc) locationStore.setActive(loc)
}

async function addLocation() {
  await locationStore.add(form.value)
  showAdd.value = false
  form.value = { name: '', latitude: 40, longitude: 116, elevation: 50, timezone: 'Asia/Shanghai' }
}
</script>

<style scoped>
.location-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.add-form {
  position: absolute;
  top: 100%;
  right: 0;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 100;
  min-width: 220px;
}

.add-form input {
  width: 100%;
}
</style>
