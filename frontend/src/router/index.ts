import { createRouter, createWebHistory } from "vue-router";

import { useSessionStore } from "../stores/session";
import AgeSelectView from "../views/AgeSelectView.vue";
import EndView from "../views/EndView.vue";
import SessionView from "../views/SessionView.vue";
import TopicSelectView from "../views/TopicSelectView.vue";
import WelcomeView from "../views/WelcomeView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "welcome", component: WelcomeView },
    { path: "/age", name: "age", component: AgeSelectView },
    {
      path: "/topic",
      name: "topic",
      component: TopicSelectView,
      beforeEnter: () => {
        const store = useSessionStore();
        return store.ageGroup ? true : "/";
      },
    },
    {
      path: "/session",
      name: "session",
      component: SessionView,
      beforeEnter: () => {
        const store = useSessionStore();
        return store.sessionId ? true : "/topic";
      },
    },
    {
      path: "/end",
      name: "end",
      component: EndView,
      beforeEnter: () => {
        const store = useSessionStore();
        return store.finished ? true : "/";
      },
    },
  ],
});
