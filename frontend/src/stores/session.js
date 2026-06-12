import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSessionStore = defineStore('session', () => {
  const today = new Date().toISOString().split('T')[0]
  const selectedDate = ref(today)
  const focalLength = ref(800)
  const sensorWidth = ref(23.5)
  const sensorHeight = ref(15.6)
  const fovRotation = ref(0)

  function setDate(date) {
    selectedDate.value = date
  }

  function setEquipment(fl, sw, sh) {
    focalLength.value = fl
    sensorWidth.value = sw
    sensorHeight.value = sh
  }

  return { selectedDate, focalLength, sensorWidth, sensorHeight, fovRotation, setDate, setEquipment }
})
