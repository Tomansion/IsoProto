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
    this.resizeHandler = null;
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
    // Use a timeout to ensure scene initialization
    // Phaser scenes initialize asynchronously, so we need to wait long enough
    setTimeout(() => {
      this.mapScene = this.game.scene.getScene("MapScene");
    }, 300);

    // Add window resize listener
    this.resizeHandler = () => this.handleWindowResize();
    window.addEventListener("resize", this.resizeHandler);
  }

  /**
   * Handle window resize events
   */
  handleWindowResize() {
    if (this.game) {
      const container = document.getElementById(this.game.config.parent);
      if (container) {
        this.game.scale.resize(container.clientWidth, container.clientHeight);
      }
    }
  }

  /**
   * Render a map with the given map data
   * @param {object} mapData - Map data from backend
   */
  renderMap(mapData) {
    if (!this.mapScene) {
      // Retry after a short delay if scene not ready yet
      setTimeout(() => {
        this.renderMap(mapData);
      }, 100);
      return;
    }

    this.mapScene.renderMap(mapData);
  }

  /**
   * Update mob sprites with the latest positions from server
   * @param {Array} mobs - Array of mob data {id, x, y, hp, mob_type, elevation}
   */
  updateMobs(mobs) {
    if (!this.mapScene) {
      setTimeout(() => this.updateMobs(mobs), 100);
      return;
    }
    this.mapScene.updateMobs(mobs);
  }

  /**
   * Update turret rotations
   * @param {Array} rotations - Array of turret rotation data {id, orientation}
   */
  updateTurretRotations(rotations) {
    if (!this.mapScene) {
      setTimeout(() => this.updateTurretRotations(rotations), 100);
      return;
    }
    this.mapScene.updateTurretRotations(rotations);
  }

  /**
   * Play turret shot animations
   * @param {Array} shots - Array of shot data {turret_id, turret_x, turret_y, orientation, mob_id, damage}
   * @param {Array} mobs - Array of mob data {id, x, y, elevation, ...} for explosion locations
   */
  playShotAnimations(shots, mobs = []) {
    if (!this.mapScene) {
      setTimeout(() => this.playShotAnimations(shots, mobs), 100);
      return;
    }
    this.mapScene.playShotAnimations(shots, mobs);
  }

  /**
   * Remove mobs from the scene (when they die)
   * @param {Array} mobIds - Array of mob IDs to remove
   */
  removeMobs(mobIds) {
    if (!this.mapScene) {
      setTimeout(() => this.removeMobs(mobIds), 100);
      return;
    }
    this.mapScene.removeMobs(mobIds);
  }

  /**
   * Destroy the Phaser game instance
   * Clean up all resources
   */
  destroy() {
    // Remove resize listener
    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
      this.resizeHandler = null;
    }

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
