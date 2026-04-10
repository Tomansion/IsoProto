/**
 * Layer management for the isometric map
 * Handles creation and management of ground and tree layers
 */

import { LAYERS } from "../../config/mapConfig.js";

export class LayerManager {
  constructor(scene) {
    this.scene = scene;
    this.layers = {};
  }

  /**
   * Create all layers for the map
   */
  createLayers() {
    // Create graphics objects to act as tile layers
    this.layers.ground = this.scene.make.graphics(
      { x: 0, y: 0, depth: LAYERS.GROUND.depth },
      false
    );

    this.layers.trees = this.scene.make.graphics(
      { x: 0, y: 0, depth: LAYERS.TREES.depth },
      false
    );
  }

  /**
   * Get a specific layer by name
   * @param {string} layerName - Layer name (e.g., 'ground', 'trees')
   * @returns {Phaser.GameObjects.Graphics} - Graphics layer object
   */
  getLayer(layerName) {
    return this.layers[layerName];
  }

  /**
   * Get all layers
   * @returns {object} - All layers keyed by name
   */
  getAllLayers() {
    return this.layers;
  }

  /**
   * Clear all layers
   */
  clearLayers() {
    Object.values(this.layers).forEach((layer) => {
      if (layer) {
        layer.clear();
      }
    });
  }

  /**
   * Destroy all layers
   */
  destroy() {
    Object.values(this.layers).forEach((layer) => {
      if (layer) {
        layer.destroy();
      }
    });
    this.layers = {};
  }
}

export default LayerManager;
