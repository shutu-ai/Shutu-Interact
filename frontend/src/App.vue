<script setup lang="ts"></script>

<template>
  <main class="app-shell">
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
