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
                <button
                  @click="zoomIn"
                  class="zoom-btn zoom-in"
                  title="Zoom In"
                >
                  +
                </button>
                <button
                  @click="zoomOut"
                  class="zoom-btn zoom-out"
                  title="Zoom Out"
                >
                  −
                </button>
                <button @click="leaveGame" class="leave-btn">[Q] quit</button>
              </div>
            </div>
          </div>
          <aside class="building-menu">
            <div class="building-menu-title">buildings</div>
            <div class="building-menu-list">
              <button
                v-for="building in buildingOptions"
                :key="building.type"
                class="building-card"
                :class="{ selected: selectedBuildingType === building.type }"
                @click="selectedBuildingType = building.type"
              >
                <div class="building-card-header">
                  <span class="building-card-name">{{ building.label }}</span>
                  <span class="building-card-size">{{
                    building.footprint
                  }}</span>
                </div>
                <div class="building-card-desc">{{ building.description }}</div>
                <div class="building-card-time">
                  spawn: {{ formatBuildTime(building.buildTimeMs) }}
                </div>
              </button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../services/api";
import phaserGameManager from "../services/PhaserGameManager.js";
import { BUILDING_UI_CONFIG, BUILDING_TYPES } from "../config/mapConfig.js";

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
      selectedBuildingType: BUILDING_TYPES.TURRET,
      buildingOptions: Object.entries(BUILDING_UI_CONFIG).map(
        ([type, config]) => ({
          type,
          ...config,
        }),
      ),
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

            const pendingBuildings =
              message.pending_buildings || message.pending_turrets || [];
            for (const pendingBuilding of pendingBuildings) {
              phaserGameManager.renderPendingBuilding(pendingBuilding);
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
        case "building_placed":
        case "turret_placed":
          if (message.data) {
            const buildings = Array.isArray(message.data)
              ? message.data
              : [message.data];

            for (const building of buildings) {
              phaserGameManager.removePendingBuilding(building.id);
              phaserGameManager.renderPlacedBuilding(building);
            }
          }
          break;
        case "building_build_started":
        case "turret_build_started":
          if (message.data) {
            phaserGameManager.renderPendingBuilding(message.data);
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
      this.placeBuildingAtTile(x, y);
    },
    placeBuildingAtTile(x, y) {
      if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket not ready");
        return;
      }

      this.websocket.send(
        JSON.stringify({
          type: "player_action",
          action_type: "place_building",
          data: {
            x: Math.floor(x),
            y: Math.floor(y),
            building_type: this.selectedBuildingType,
          },
        }),
      );
    },
    formatBuildTime(buildTimeMs) {
      return `${(buildTimeMs / 1000).toFixed(1)}s`;
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
  min-width: 0;
}

.game-panel {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
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

.building-menu {
  width: 260px;
  min-width: 260px;
  border-left: 1px solid #00aa00;
  background-color: rgba(0, 18, 0, 1);
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 12px;
}

.building-menu-title {
  color: #55ff55;
  font-size: 12px;
  font-weight: bold;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.building-menu-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.building-card {
  width: 100%;
  text-align: left;
  background-color: rgba(0, 26, 0, 0.9);
  border: 1px solid #007700;
  border-radius: 4px;
  color: #00ff00;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  font-family: "Courier New", monospace;
  transition:
    border-color 0.2s,
    background-color 0.2s,
    transform 0.2s;
}

.building-card:hover {
  border-color: #33cc33;
  background-color: rgba(0, 40, 0, 0.95);
}

.building-card.selected {
  border-color: #55ff55;
  background-color: rgba(0, 60, 0, 1);
  transform: translateY(-1px);
}

.building-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.building-card-name {
  font-size: 14px;
  font-weight: bold;
}

.building-card-size,
.building-card-time {
  color: #88ff88;
  font-size: 11px;
}

.building-card-desc {
  color: #c4ffc4;
  font-size: 12px;
  line-height: 1.35;
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

@media (max-width: 900px) {
  .game-content {
    flex-direction: column;
  }

  .building-menu {
    width: 100%;
    min-width: 0;
    border-left: 0;
    border-top: 1px solid #00aa00;
  }

  .building-menu-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
