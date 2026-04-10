/**
 * Phaser game lifecycle manager
 * Manages Phaser game instance creation, lifecycle, and provides high-level API
 */

import Phaser from "phaser";
import { phaserConfig } from "../config/phaserConfig.js";
import MapScene from "../scenes/MapScene.js";

export class PhaserGameManager {
  constructor() {
    this.game = null;
    this.mapScene = null;
  }

  /**
   * Initialize and start the Phaser game
   * @param {string} containerId - ID of the DOM element to contain the game canvas
   */
  init(containerId) {
    if (this.game) {
      console.warn("Phaser game already initialized");
      return;
    }

    // Create game config with the container ID
    const config = {
      ...phaserConfig,
      parent: containerId,
      scene: [MapScene],
    };

    // Create the Phaser game instance
    this.game = new Phaser.Game(config);

    // Wait for the scene to be ready before storing reference
    // Use a small timeout to ensure scene initialization
    setTimeout(() => {
      this.mapScene = this.game.scene.getScene("MapScene");
      if (this.mapScene) {
        console.log("MapScene initialized");
      }
    }, 100);
  }

  /**
   * Render a map with the given map data
   * @param {object} mapData - Map data from backend
   */
  renderMap(mapData) {
    if (!this.mapScene) {
      // Retry after a short delay if scene not ready yet
      console.warn("MapScene not ready yet, retrying...");
      setTimeout(() => {
        this.renderMap(mapData);
      }, 100);
      return;
    }

    this.mapScene.renderMap(mapData);
  }

  /**
   * Destroy the Phaser game instance
   * Clean up all resources
   */
  destroy() {
    if (this.game) {
      this.game.destroy(true);
      this.game = null;
      this.mapScene = null;
    }
  }

  /**
   * Check if game is initialized
   * @returns {boolean}
   */
  isInitialized() {
    return this.game !== null;
  }

  /**
   * Get the Phaser game instance
   * @returns {Phaser.Game}
   */
  getGame() {
    return this.game;
  }

  /**
   * Get the map scene
   * @returns {MapScene}
   */
  getMapScene() {
    return this.mapScene;
  }
}

// Export singleton instance
export default new PhaserGameManager();
