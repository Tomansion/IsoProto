<template>
  <div class="home-container">
    <div class="terminal-window">
      <div class="terminal-header">{{ playerName }}@isoproto:~$</div>
      <div class="terminal-content">
        <p class="terminal-text">> MAIN MENU</p>
        <div class="button-group">
          <button @click="goToListGames" class="terminal-btn">
            [L] list-games
          </button>
          <button @click="createNewGame" class="terminal-btn" :disabled="creating">
            [C] create-game {{ creating ? "..." : "" }}
          </button>
          <button @click="handleLogout" class="terminal-btn logout">
            [Q] logout
          </button>
        </div>
        <p v-if="error" class="terminal-error">> ERROR: {{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../services/api";

export default {
  name: "Home",
  data() {
    return {
      playerName: "",
      creating: false,
      error: null,
    };
  },
  mounted() {
    this.playerName = localStorage.getItem("playerName") || "Player";
    if (!this.playerName || this.playerName === "Player") {
      this.$router.push("/");
    }
    window.addEventListener("keydown", this.handleKeydown);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeydown);
  },
  methods: {
    async createNewGame() {
      try {
        this.creating = true;
        this.error = null;
        const game = await api.createGame(this.playerName);
        localStorage.setItem("lastGameId", game.id);
        this.$router.push(`/game/${game.id}`);
      } catch (err) {
        this.error = err.message;
        this.creating = false;
      }
    },
    goToListGames() {
      this.$router.push("/games");
    },
    handleLogout() {
      localStorage.removeItem("playerName");
      this.$router.push("/");
    },
    handleKeydown(e) {
      const key = e.key.toLowerCase();
      if (key === "l") {
        this.goToListGames();
      } else if (key === "c" && !this.creating) {
        this.createNewGame();
      } else if (key === "q") {
        this.handleLogout();
      }
    },
  },
};
</script>

<style scoped>
.home-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #000000;
  padding: 20px;
}

.terminal-window {
  width: 100%;
  max-width: 600px;
  background-color: #000000;
  border: 1px solid #00ff00;
  font-family: "Courier New", monospace;
  color: #00ff00;
}

.terminal-header {
  background-color: #001a00;
  border-bottom: 1px solid #00ff00;
  padding: 8px 12px;
  font-size: 12px;
  color: #00aa00;
}

.terminal-content {
  padding: 16px;
}

.terminal-text {
  margin: 0 0 16px 0;
  font-size: 13px;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.terminal-btn {
  background-color: #001a00;
  border: 1px solid #00ff00;
  color: #00ff00;
  padding: 8px 12px;
  font-family: "Courier New", monospace;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}

.terminal-btn:hover {
  background-color: #003300;
}

.terminal-btn.logout {
  color: #ff0000;
  border-color: #ff0000;
}

.terminal-btn.logout:hover {
  background-color: #330000;
}

.terminal-error {
  color: #ff0000;
  margin-top: 16px;
  font-size: 12px;
}
</style>
