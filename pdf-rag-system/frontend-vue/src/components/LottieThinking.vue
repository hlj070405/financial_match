<template>
  <div class="thinking-dots" :style="{ '--dot-size': dotSize + 'px', '--dot-color': color, '--gap': gap + 'px' }">
    <span class="dot"></span>
    <span class="dot"></span>
    <span class="dot"></span>
  </div>
</template>

<script setup>
const props = defineProps({
  size: { type: Number, default: 24 },
  color: { type: String, default: '#6366f1' },
  speed: { type: Number, default: 1 }
})

const dotSize = Math.max(Math.round(props.size * 0.28), 4)
const gap = Math.max(Math.round(props.size * 0.12), 2)
</script>

<style scoped>
.thinking-dots {
  display: inline-flex;
  align-items: center;
  gap: var(--gap);
  height: var(--dot-size);
}

.dot {
  width: var(--dot-size);
  height: var(--dot-size);
  border-radius: 50%;
  background: var(--dot-color);
  opacity: 0.35;
  animation: dotPulse 1.4s ease-in-out infinite;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotPulse {
  0%, 80%, 100% {
    opacity: 0.35;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1.2);
  }
}
</style>
