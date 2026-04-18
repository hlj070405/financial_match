<template>
  <div ref="vantaRef" class="vanta-container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import GLOBE from 'vanta/dist/vanta.globe.min'

const vantaRef = ref(null)
let vantaEffect = null

onMounted(() => {
  if (vantaRef.value) {
    vantaEffect = GLOBE({
      el: vantaRef.value,
      THREE: THREE,
      mouseControls: true,
      touchControls: true,
      gyroControls: false,
      minHeight: 200.00,
      minWidth: 200.00,
      scale: 1.00,
      scaleMobile: 1.00,
      color: 0x3fafff,
      color2: 0xff6b9d,
      backgroundColor: 0x0a0e27
    })
  }
})

onBeforeUnmount(() => {
  if (vantaEffect) {
    vantaEffect.destroy()
  }
})
</script>

<style scoped>
.vanta-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}
</style>
