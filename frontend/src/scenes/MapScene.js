/**
 * Main Phaser scene for rendering the isometric map
 * Orchestrates all managers (LayerManager, TileManager, CameraManager, BuildingManager)
 */

import Phaser from "phaser";
import LayerManager from "../phaser/managers/LayerManager.js";
import TileManager from "../phaser/managers/TileManager.js";
import CameraManager from "../phaser/managers/CameraManager.js";
import BuildingManager from "../phaser/managers/BuildingManager.js";
import { loadTileset } from "../utils/tilesetHelper.js";
import { BUILDING_SHEET_ASSET } from "../config/mapConfig.js";

export class MapScene extends Phaser.Scene {
  constructor() {
    super({ key: "MapScene" });
    this.layerManager = null;
    this.tileManager = null;
    this.cameraManager = null;
    this.buildingManager = null;
  }

  preload() {
    // Load the tileset image
    loadTileset(this);

    // Load building spritesheet
    if (!this.textures.exists(BUILDING_SHEET_ASSET.key)) {
      this.load.spritesheet(
        BUILDING_SHEET_ASSET.key,
        BUILDING_SHEET_ASSET.url,
        {
          frameWidth: BUILDING_SHEET_ASSET.frameWidth,
          frameHeight: BUILDING_SHEET_ASSET.frameHeight,
        },
      );
    }
  }

  create() {
    // Initialize all managers
    this.layerManager = new LayerManager(this);
    this.layerManager.createLayers();

    this.tileManager = new TileManager(this, this.layerManager);
    this.buildingManager = new BuildingManager(this);

    this.cameraManager = new CameraManager(this);

    // Set background color
    this.cameras.main.setBackgroundColor("#1a1a1a");
  }

  /**
   * Update loop - called every frame
   */
  update() {
    if (this.cameraManager) {
      this.cameraManager.update();
    }
  }

  /**
   * Render the map with the given map data
   * This is the main public API for rendering
   * @param {object} mapData - Map data {width, height, tiles: [[...]], elevation: [[...]], buildings: [{...}]}
   */
  renderMap(mapData) {
    if (!mapData || !mapData.tiles) {
      console.error("Invalid map data", mapData);
      return;
    }

    // Ensure tileset is loaded
    if (!this.textures.exists("isometric-tileset")) {
      setTimeout(() => this.renderMap(mapData), 100);
      return;
    }

    // Ensure building sheet is loaded
    if (!this.textures.exists(BUILDING_SHEET_ASSET.key)) {
      console.log("Waiting for building sheet to load...");
      setTimeout(() => this.renderMap(mapData), 100);
      return;
    }

    // Clear previous tiles
    this.tileManager.clearTiles();
    this.buildingManager.clearBuildings();

    // Render new tiles
    this.tileManager.renderTiles(mapData);

    // Render buildings
    this.buildingManager.renderBuildings(mapData);

    // Set up camera to view the map
    this.cameraManager.setupIsometricCamera(mapData);
  }

  /**
   * Clean up scene resources
   */
  shutdown() {
    if (this.tileManager) this.tileManager.destroy();
    if (this.buildingManager) this.buildingManager.destroy();
    if (this.layerManager) this.layerManager.destroy();
    if (this.cameraManager) this.cameraManager.destroy();
  }
}

export default MapScene;
