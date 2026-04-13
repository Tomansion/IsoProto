<template>
  <div class="game-container">
    <div class="terminal-window">
      <div class="terminal-header">game@isoproto:{{ gameId }}</div>
      <div class="terminal-main">
        <div class="game-info-bar">
          <div>{{ game?.name || "loading..." }}</div>
          <div class="info-stats">
            {{ game?.nb_players || 0 }} players
            <button @click="leaveGame" class="leave-btn">[Q] quit</button>
          </div>
        </div>

        <div class="game-content">
          <div class="game-board">
            <div v-if="loading" class="status">connecting...</div>
            <div v-else-if="error" class="status error-msg">
              error: {{ error }}
            </div>
            <div v-else id="game-canvas-container" class="phaser-container"></div>
          </div>

          <div class="players-panel">
            <div class="panel-header">PLAYERS</div>
            <div class="players-list">
              <div
                v-for="player in game?.players"
                :key="player.id"
                class="player-item"
              >
                > {{ player.username }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../services/api";
import phaserGameManager from "../services/PhaserGameManager.js";

export default {
  name: "Game",
  data() {
    return {
      gameId: this.$route.params.gameId,
      game: null,
      loading: true,
      error: null,
      playerName: "",
      websocket: null,
      map: null,
      connectionTimeout: null,
    };
  },
  mounted() {
    this.playerName = localStorage.getItem("playerName") || "Player";
    if (!this.playerName || this.playerName === "Player") {
      this.$router.push("/");
      return;
    }

    this.connectToGame();
    window.addEventListener("keydown", this.handleKeydown);
  },
  beforeUnmount() {
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
    }
    if (this.websocket) {
      this.websocket.close();
    }
    window.removeEventListener("keydown", this.handleKeydown);

    // Clean up Phaser game
    if (phaserGameManager.isInitialized()) {
      phaserGameManager.destroy();
    }
  },
  methods: {
    connectToGame() {
      try {
        this.websocket = api.connectToGame(this.gameId, this.playerName);

        // Set a timeout for connection - if it doesn't connect in 5s, show error
        this.connectionTimeout = setTimeout(() => {
          if (this.loading) {
            console.warn("Connection timeout");
            this.error = "connection timeout - server may be offline";
            this.loading = false;
          }
        }, 5000);

        this.websocket.onopen = () => {
          // Clear timeout on successful connection
          if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
          }
          this.loading = false;
          
          // Initialize Phaser game AFTER the container div is rendered
          // Use nextTick to ensure DOM is updated
          this.$nextTick(() => {
            phaserGameManager.init("game-canvas-container");
          });
        };

        this.websocket.onmessage = (event) => {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        };

        this.websocket.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.error = "failed to connect to game server";
          this.loading = false;
          if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
          }
        };

        this.websocket.onclose = () => {
          console.log("WebSocket disconnected");
        };
      } catch (err) {
        console.error("Connection error:", err);
        this.error = `connection error: ${err.message}`;
        this.loading = false;
      }
    },
    handleMessage(message) {
      switch (message.type) {
        case "welcome":
          if (message.map) {
            this.map = message.map;
            // Render map in Phaser
            phaserGameManager.renderMap(this.map);
          }
          break;
        case "game_state":
          this.game = message.data;
          break;
        case "player_joined":
          if (message.data) {
            this.game.nb_players = message.data.nb_players;
            this.game.players = message.data.players;
          }
          break;
        case "player_left":
          if (message.data) {
            this.game.nb_players = message.data.nb_players;
            this.game.players = message.data.players;
          }
          break;
        case "action":
          break;
        case "player_disconnected":
          break;
        default:
          console.log("Message:", message.type);
      }
    },
    leaveGame() {
      if (this.websocket) {
        this.websocket.close();
      }
      this.$router.push("/home");
    },
    handleKeydown(e) {
      const key = e.key.toLowerCase();
      if (key === "q") {
        this.leaveGame();
      }
    },
  },
};
</script>

<style scoped>
.game-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #000000;
  overflow: hidden;
}

.terminal-window {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
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
  flex-shrink: 0;
}

.terminal-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.game-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #00aa00;
  font-size: 13px;
  background-color: #001a00;
  flex-shrink: 0;
}

.info-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.leave-btn {
  background-color: transparent;
  border: none;
  color: #ff0000;
  cursor: pointer;
  font-family: "Courier New", monospace;
  font-size: 12px;
  padding: 0;
}

.leave-btn:hover {
  background-color: transparent;
}

.game-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.game-board {
  flex: 1;
  background-color: #000000;
  border-right: 1px solid #00aa00;
  display: block;
  overflow: hidden;
  position: relative;
}

#game-canvas {
  width: 100%;
  height: 100%;
}

.canvas-placeholder {
  width: 100%;
  height: 100%;
  background-color: #001a00;
  border: 1px dashed #00aa00;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00aa00;
  font-size: 12px;
}

.phaser-container {
  width: 100%;
  height: 100%;
}

.status {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #00ff00;
  font-size: 12px;
  text-align: center;
  background-color: rgba(0, 0, 0, 0.8);
  padding: 10px 20px;
  border: 1px solid #00aa00;
}

.error-msg {
  color: #ff0000;
}

.players-panel {
  width: 200px;
  background-color: #000000;
  border-left: 1px solid #00aa00;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
}

.panel-header {
  padding: 8px 12px;
  border-bottom: 1px solid #00aa00;
  background-color: #001a00;
  font-size: 12px;
  color: #00ff00;
  flex-shrink: 0;
}

.players-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 0;
}

.player-item {
  font-size: 12px;
  padding: 4px 0;
  color: #00ff00;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
