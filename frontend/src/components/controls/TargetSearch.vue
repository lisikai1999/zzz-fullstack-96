<template>
  <div class="target-search">
    <input
      v-model="query"
      placeholder="Search DSO (M31, NGC7000...)"
      @input="onInput"
      @focus="showResults = true"
    />
    <div v-if="showResults && results.length" class="results-dropdown">
      <div
        v-for="t in results"
        :key="t.id"
        class="result-item"
        @click="selectTarget(t)"
      >
        <span class="des">{{ t.designation }}</span>
        <span class="name">{{ t.common_name || t.object_type }}</span>
        <span class="mag">{{ t.magnitude ? t.magnitude.toFixed(1) : '--' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useTargetStore } from '../../stores/targets'

const targetStore = useTargetStore()
const query = ref('')
const results = ref([])
const showResults = ref(false)
let timeout = null

function onInput() {
  clearTimeout(timeout)
  timeout = setTimeout(async () => {
    if (query.value.length < 1) { results.value = []; return }
    await targetStore.search(query.value)
    results.value = targetStore.searchResults
  }, 200)
}

function selectTarget(t) {
  targetStore.select(t)
  query.value = t.designation
  showResults.value = false
}
</script>

<style scoped>
.target-search {
  position: relative;
}

.target-search input {
  width: 100%;
}

.results-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 0 0 6px 6px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 50;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  cursor: pointer;
  font-size: 13px;
}

.result-item:hover {
  background: #21262d;
}

.result-item .des {
  font-weight: 600;
  min-width: 60px;
}

.result-item .name {
  flex: 1;
  color: #8b949e;
}

.result-item .mag {
  color: #8b949e;
  font-size: 12px;
}
</style>
