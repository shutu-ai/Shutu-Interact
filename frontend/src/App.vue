<script setup lang="ts">
import FullscreenToggle from "./components/FullscreenToggle.vue";
</script>

<template>
  <main class="app-shell">
    <FullscreenToggle />
    <RouterView />
  </main>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 24px;
}
</style>
