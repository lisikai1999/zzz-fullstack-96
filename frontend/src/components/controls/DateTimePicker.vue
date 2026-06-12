<template>
  <div class="date-picker">
    <input type="date" :value="sessionStore.selectedDate" @input="onChange" />
  </div>
</template>

<script setup>
import { useSessionStore } from '../../stores/session'

const sessionStore = useSessionStore()

function onChange(e) {
  sessionStore.setDate(e.target.value)
}
</script>

<style scoped>
.date-picker input {
  width: 150px;
}
</style>
