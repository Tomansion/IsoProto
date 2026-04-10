import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./assets/css/main.scss";
import Phaser from "phaser";

// Make Phaser globally available
window.Phaser = Phaser;

createApp(App).use(router).mount("#app");
