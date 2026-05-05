<template>
  <div class="game-container">
    <div class="terminal-window">
      <div class="terminal-main">
        <div class="game-content">
          <div class="game-panel">
            <div class="game-board">
              <div v-if="loading" class="status">connecting...</div>
              <div v-else-if="error" class="status error-msg">
                error: {{ error }}
              </div>
              <div
                v-else
                id="game-canvas-container"
                class="phaser-container"
              ></div>
            </div>
            <div class="game-toolbar">
              <div class="game-name">{{ game?.name || "loading..." }}</div>
              <div class="game-controls">
                <button @click="zoomIn" class="zoom-btn zoom-in" title="Zoom In">+</button>
                <button @click="zoomOut" class="zoom-btn zoom-out" title="Zoom Out">−</button>
                <button @click="leaveGame" class="leave-btn">[Q] quit</button>
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
      mobs: [],
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
            // Initialize mobs list from welcome message
            this.mobs = message.mobs || [];
            // Render map in Phaser
            phaserGameManager.renderMap(this.map);

            // Render initial mob positions
            if (this.mobs.length > 0) {
              phaserGameManager.updateMobs(this.mobs);
            }

            const pendingTurrets = message.pending_turrets || [];
            for (const pendingTurret of pendingTurrets) {
              phaserGameManager.renderPendingTurret(pendingTurret);
            }

            // Setup tile click detection AFTER map is ready
            // Wait for scene to be fully initialized
            setTimeout(() => {
              const mapScene = phaserGameManager.getMapScene();
              if (mapScene) {
                mapScene.setupTileClickDetection((x, y) => {
                  console.log("Tile clicked:", x, y);
                  this.handleTileClick(x, y);
                });
              }
            }, 400);
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
        case "turret_placed":
          if (message.data) {
            const turrets = Array.isArray(message.data)
              ? message.data
              : [message.data];

            for (const turret of turrets) {
              phaserGameManager.removePendingTurret(turret.id);
              phaserGameManager.renderTurret(turret);
            }
          }
          break;
        case "turret_build_started":
          if (message.data) {
            phaserGameManager.renderPendingTurret(message.data);
          }
          break;
        case "mob_update":
          // Complete mob list update - replace the entire list
          this.mobs = message.data || [];
          phaserGameManager.updateMobs(this.mobs);
          break;
        case "mob_died":
          // Remove dead mobs from the scene
          phaserGameManager.removeMobs(message.data || []);
          break;
        case "turret_rotation":
          phaserGameManager.updateTurretRotations(message.data || []);
          break;
        case "turret_shot":
          phaserGameManager.playShotAnimations(message.data || [], this.mobs);
          break;
        case "mob_spawned":
          // Add newly spawned mobs to our tracking list
          const newMobs = message.data || [];
          this.mobs = [...this.mobs, ...newMobs];
          // Always update with complete list to avoid deletion
          phaserGameManager.updateMobs(this.mobs);
          break;
        case "action_error":
          console.warn("Action error:", message.message);
          // Could add visual feedback here for failed turret placement
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
    handleTileClick(x, y) {
      // Send turret placement request to backend
      this.placeTurretAtTile(x, y);
    },
    placeTurretAtTile(x, y) {
      if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket not ready");
        return;
      }

      // Send turret placement action
      this.websocket.send(
        JSON.stringify({
          type: "player_action",
          action_type: "place_turret",
          data: {
            x: Math.floor(x),
            y: Math.floor(y),
          },
        }),
      );
    },
    zoomIn() {
      const mapScene = phaserGameManager.getMapScene();
      if (mapScene && mapScene.cameraManager) {
        mapScene.cameraManager.zoomIn();
      }
    },
    zoomOut() {
      const mapScene = phaserGameManager.getMapScene();
      if (mapScene && mapScene.cameraManager) {
        mapScene.cameraManager.zoomOut();
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
  font-family: "Courier New", monospace;
  color: #00ff00;
}

.terminal-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.game-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.game-panel {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

.game-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 16px;
  background-color: rgba(0, 26, 0, 1);
}

.game-board {
  flex: 1;
  background-color: #000000;
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
  z-index: 10;
}

.error-msg {
  color: #ff0000;
}

.game-name {
  color: #00ff00;
  font-weight: bold;
}

.game-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.player-count {
  color: #00ff00;
}

.leave-btn {
  background-color: transparent;
  border: 1px solid #aa0000;
  border-radius: 3px;
  color: #ff0000;
  cursor: pointer;
  font-family: "Courier New", monospace;
  font-size: 12px;
  padding: 8px 12px;
  transition:
    color 0.2s,
    border-color 0.2s,
    background-color 0.2s;
}

.leave-btn:hover {
  background-color: rgba(170, 0, 0, 0.15);
  color: #ff6666;
  border-color: #ff6666;
}

.zoom-btn {
  width: 36px;
  height: 36px;
  background-color: rgba(0, 26, 0, 1);
  border: 1px solid #00aa00;
  border-radius: 3px;
  color: #00ff00;
  font-family: "Courier New", monospace;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.zoom-btn:hover {
  background-color: rgba(0, 170, 0, 0.8);
  color: #55ff55;
  border-color: #55ff55;
}

.zoom-btn:active {
  transform: scale(0.95);
}
</style>
