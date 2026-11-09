<script setup lang="ts">
import { useRouter } from "vue-router";

import CocoCharacter from "../components/CocoCharacter.vue";
import PrimaryButton from "../components/PrimaryButton.vue";
import { useSessionStore } from "../stores/session";

const router = useRouter();
const store = useSessionStore();

function home(): void {
  store.reset();
  router.replace("/");
}
</script>

<template>
  <section class="page">
    <CocoCharacter state="thumbsup" />
    <h1 class="title">You did a great job! 你真棒!</h1>
    <PrimaryButton @click="home">再来一次 · Back to Home</PrimaryButton>
  </section>
</template>
