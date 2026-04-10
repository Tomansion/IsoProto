import { createRouter, createWebHistory } from "vue-router";
import Login from "./components/Login.vue";
import Home from "./components/Home.vue";
import GamesList from "./components/GamesList.vue";
import Game from "./components/Game.vue";

const routes = [
  { path: "/", component: Login, name: "Login" },
  { path: "/home", component: Home, name: "Home" },
  { path: "/games", component: GamesList, name: "GamesList" },
  { path: "/game/:gameId", component: Game, name: "Game" },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
