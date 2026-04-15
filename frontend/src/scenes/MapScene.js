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
import { BUILDING_SHEET_ASSET, TURRET_SHEET_ASSET } from "../config/mapConfig.js";
import { isometricToCartesian } from "../utils/isometricHelper.js";

export class MapScene extends Phaser.Scene {
  constructor() {
    super({ key: "MapScene" });
    this.layerManager = null;
    this.tileManager = null;
    this.cameraManager = null;
    this.buildingManager = null;
    this.mapData = null;
    this.tileClickCallback = null;
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

    // Load turret spritesheet
    if (!this.textures.exists(TURRET_SHEET_ASSET.key)) {
      this.load.spritesheet(
        TURRET_SHEET_ASSET.key,
        TURRET_SHEET_ASSET.url,
        {
          frameWidth: TURRET_SHEET_ASSET.frameWidth,
          frameHeight: TURRET_SHEET_ASSET.frameHeight,
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
   * Setup tile click detection for turret placement
   * @param {function} callback - Callback function(x, y) called when a valid tile is clicked
   */
  setupTileClickDetection(callback) {
    this.tileClickCallback = callback;

    this.input.on("pointerdown", (pointer) => {
      if (!this.mapData || !this.tileClickCallback) {
        return;
      }

      // Get world position from screen position
      const worldX = this.cameras.main.getWorldPoint(pointer.x, pointer.y).x;
      const worldY = this.cameras.main.getWorldPoint(pointer.x, pointer.y).y;

      // Convert to cartesian tile coordinates
      const { x, y } = isometricToCartesian(worldX, worldY);

      // Validate coordinates are within map
      if (
        x >= 0 &&
        x < this.mapData.width &&
        y >= 0 &&
        y < this.mapData.height
      ) {
        // Call the callback with tile coordinates
        this.tileClickCallback(x, y);
      }
    });
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

    // Store map data for tile click detection
    this.mapData = mapData;

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

    // Ensure turret sheet is loaded
    if (!this.textures.exists(TURRET_SHEET_ASSET.key)) {
      console.log("Waiting for turret sheet to load...");
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
   * Render a single turret on the map
   * Called when a turret is placed
   * @param {object} turretData - Turret data {id, x, y, building_type, orientation, player_id}
   */
  renderTurret(turretData) {
    if (!this.buildingManager || !this.mapData) {
      console.warn("Cannot render turret: building manager or map data not ready");
      return;
    }

    this.buildingManager.renderTurret(turretData, this.mapData);
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
