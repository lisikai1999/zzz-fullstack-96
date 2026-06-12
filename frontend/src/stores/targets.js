import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useTargetStore = defineStore('targets', () => {
  const searchResults = ref([])
  const selectedTarget = ref(null)
  const tonightTargets = ref([])

  async function search(query) {
    const res = await api.searchTargets({ search: query, limit: 50 })
    searchResults.value = res.items
  }

  function select(target) {
    selectedTarget.value = target
  }

  async function loadTonight(locationId, date) {
    const res = await api.getTonight(locationId, date)
    tonightTargets.value = res.targets
  }

  return { searchResults, selectedTarget, tonightTargets, search, select, loadTonight }
})
