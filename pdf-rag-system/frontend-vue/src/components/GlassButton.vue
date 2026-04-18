<template>
  <div 
    class="glass-button-container" 
    ref="containerRef"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
    :class="{ 'opacity-50 pointer-events-none': disabled }"
  >
    <button 
      class="glass-button-content"
      :class="[contentClass]"
      :disabled="disabled"
      @click="$emit('click', $event)"
    >
      <slot></slot>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  contentClass: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['click'])

const containerRef = ref(null)

const handleMouseMove = (e) => {
  if (!containerRef.value) return
  
  const rect = containerRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  containerRef.value.style.setProperty('--x', `${x}px`)
  containerRef.value.style.setProperty('--y', `${y}px`)
}

const handleMouseLeave = () => {
  if (!containerRef.value) return
  // Optional: Reset or fade out effect
  // For now, we keep the last position or could move it out of view
}
</script>

<style scoped>
.glass-button-container {
  /* Set default values to center or off-screen */
  --x: 50%;
  --y: 50%;
}
</style>
