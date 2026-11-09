<script setup lang="ts">
defineEmits<{ click: [] }>();
</script>

<template>
  <button type="button" class="primary-button" @click="$emit('click')">
    <slot />
  </button>
</template>

<style scoped>
.primary-button {
  min-width: 280px;
  min-height: 88px;
  padding: 16px 32px;
  font-size: 1.6rem;
  font-weight: 700;
  border-radius: 24px;
  border: none;
  background: #2f6fed;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 6px 0 #1d4fb8;
  transition:
    transform 0.05s ease,
    box-shadow 0.05s ease;
}

.primary-button:active {
  transform: translateY(4px);
  box-shadow: 0 2px 0 #1d4fb8;
}

.primary-button:disabled {
  opacity: 0.55;
  cursor: wait;
}
</style>
