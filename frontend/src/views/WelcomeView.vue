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
    <PrimaryButton @click="start">Start · 开始互动</PrimaryButton>
  </section>
</template>
