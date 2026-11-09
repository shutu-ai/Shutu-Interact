<script setup lang="ts">
import { useRouter } from "vue-router";

import CocoCharacter from "../components/CocoCharacter.vue";
import PrimaryButton from "../components/PrimaryButton.vue";

const router = useRouter();

function start(): void {
  router.push("/age");
}
</script>

<template>
  <section class="page">
    <CocoCharacter state="idle" />
    <h1 class="title">Coco English</h1>
    <p class="subtitle">你好!我是 Coco,AI 英语互动小伙伴,一起说英语吧!</p>
    <p class="privacy-note">
      本互动为匿名体验,不收集任何个人信息 · Anonymous — no personal
      information is collected.
    </p>
    <PrimaryButton @click="start">Start · 开始互动</PrimaryButton>
  </section>
</template>

<style scoped>
.privacy-note {
  font-size: 0.95rem;
  color: #8a7a5c;
  text-align: center;
  margin: 0;
  max-width: 560px;
}
</style>
