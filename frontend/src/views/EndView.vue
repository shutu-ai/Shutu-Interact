<script setup lang="ts">
import { useRouter } from "vue-router";

import CocoCharacter from "../components/CocoCharacter.vue";
import PrimaryButton from "../components/PrimaryButton.vue";
import { useSessionStore } from "../stores/session";

const router = useRouter();
const store = useSessionStore();

// Spec §8.3: 会话结束必须清理上下文 — the natural finish goes through
// endSession so the server-side session (with child texts) is deleted too.
async function home(): Promise<void> {
  await store.endSession();
  router.replace("/");
}
</script>

<template>
  <section class="page">
    <CocoCharacter state="thumbsup" />
    <h1 class="title">You did a great job! 你真棒!</h1>
    <p v-if="store.endReason === 'timeout' || store.endReason === 'idle'" class="timeup">
      Time for a little break! 休息一下,下次再玩!
    </p>
    <PrimaryButton @click="home">再来一次 · Back to Home</PrimaryButton>
  </section>
</template>

<style scoped>
.timeup {
  font-size: 1.1rem;
  color: #8a7a5c;
  margin: 0;
}
</style>
