import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useLocationStore = defineStore('location', () => {
  const locations = ref([])
  const activeLocation = ref(null)

  async function load() {
    locations.value = await api.getLocations()
    if (!activeLocation.value && locations.value.length > 0) {
      activeLocation.value = locations.value[0]
    }
  }

  async function add(data) {
    const loc = await api.createLocation(data)
    locations.value.push(loc)
    activeLocation.value = loc
  }

  async function remove(id) {
    await api.deleteLocation(id)
    locations.value = locations.value.filter((l) => l.id !== id)
    if (activeLocation.value?.id === id) {
      activeLocation.value = locations.value[0] || null
    }
  }

  function setActive(loc) {
    activeLocation.value = loc
  }

  return { locations, activeLocation, load, add, remove, setActive }
})
