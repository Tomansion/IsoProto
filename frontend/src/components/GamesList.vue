<template>
  <div class="games-container">
    <div class="terminal-window">
      <div class="terminal-header">games@isoproto:~$</div>
      <div class="terminal-content">
        <button @click="goHome" class="terminal-btn back-btn">[B] back</button>
        
        <p class="terminal-text">> AVAILABLE GAMES:</p>

        <div v-if="loading" class="terminal-output">
          loading games...
        </div>

        <div v-else-if="games.length === 0" class="terminal-output">
          no games available
        </div>

        <div v-else class="games-list">
          <div v-for="game in games" :key="game.id" class="game-row">
            <div class="game-info">
              <span class="game-name">{{ game.name }}</span>
              <span class="game-stats">{{ game.nb_players }} players</span>
            </div>
            <button
              @click="joinGame(game.id)"
              class="terminal-btn join-btn"
              :disabled="joining === game.id"
            >
              {{ joining === game.id ? "..." : "join" }}
            </button>
          </div>
        </div>

        <p v-if="error" class="terminal-error">> ERROR: {{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../services/api";

export default {
  name: "GamesList",
  data() {
    return {
      games: [],
      loading: true,
      error: null,
      joining: null,
      playerName: "",
    };
  },
  mounted() {
    this.playerName = localStorage.getItem("playerName") || "Player";
    if (!this.playerName || this.playerName === "Player") {
      this.$router.push("/");
      return;
    }
    this.loadGames();
  },
  methods: {
    async loadGames() {
      try {
        this.loading = true;
        this.error = null;
        this.games = await api.getGames();
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    async joinGame(gameId) {
      try {
        this.joining = gameId;
        this.error = null;
        const game = await api.joinGame(gameId, this.playerName);
        localStorage.setItem("lastGameId", game.id);
        this.$router.push(`/game/${game.id}`);
      } catch (err) {
        this.error = err.message;
        this.joining = null;
      }
    },
    goHome() {
      this.$router.push("/home");
    },
  },
};
</script>

<style scoped>
.games-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  background-color: #000000;
  padding: 20px;
  overflow-y: auto;
}

.terminal-window {
  width: 100%;
  max-width: 800px;
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

.back-btn {
  margin-bottom: 12px;
}

.terminal-text {
  margin: 8px 0;
  font-size: 13px;
}

.terminal-output {
  margin: 12px 0;
  padding: 8px;
  background-color: #001a00;
  border: 1px solid #00aa00;
  font-size: 12px;
  min-height: 30px;
}

.games-list {
  margin: 12px 0;
  border: 1px solid #00aa00;
}

.game-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-bottom: 1px solid #003300;
  font-size: 12px;
}

.game-row:last-child {
  border-bottom: none;
}

.game-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.game-name {
  font-weight: bold;
  color: #00ff00;
}

.game-stats {
  font-size: 11px;
  color: #00aa00;
}

.terminal-btn {
  background-color: #001a00;
  border: 1px solid #00ff00;
  color: #00ff00;
  padding: 6px 12px;
  font-family: "Courier New", monospace;
  font-size: 12px;
  cursor: pointer;
  margin: 0 4px;
}

.terminal-btn:hover:not(:disabled) {
  background-color: #003300;
}

.terminal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.join-btn {
  min-width: 60px;
}

.terminal-error {
  color: #ff0000;
  margin-top: 12px;
  font-size: 12px;
}
</style>
