/**
 * Building rendering and management
 * Handles placement and rendering of buildings on the map
 */

import {
  cartesianToIsometric,
  getDepthForTile,
} from "../../utils/isometricHelper.js";
import {
  BUILDING_SHEET_ASSET,
  TURRET_SHEET_ASSET,
  TURRET_FRAMES,
} from "../../config/mapConfig.js";

export class BuildingManager {
  constructor(scene) {
    this.scene = scene;
    this.buildings = [];
    this.turrets = []; // Track turrets separately (each is {baseSprite, headSprite})
  }

  /**
   * Load building and turret spritesheet assets
   */
  loadAssets() {
    if (!this.scene.textures.exists(BUILDING_SHEET_ASSET.key)) {
      this.scene.load.spritesheet(
        BUILDING_SHEET_ASSET.key,
        BUILDING_SHEET_ASSET.url,
        {
          frameWidth: BUILDING_SHEET_ASSET.frameWidth,
          frameHeight: BUILDING_SHEET_ASSET.frameHeight,
        },
      );
    }
    
    if (!this.scene.textures.exists(TURRET_SHEET_ASSET.key)) {
      this.scene.load.spritesheet(
        TURRET_SHEET_ASSET.key,
        TURRET_SHEET_ASSET.url,
        {
          frameWidth: TURRET_SHEET_ASSET.frameWidth,
          frameHeight: TURRET_SHEET_ASSET.frameHeight,
        },
      );
    }
  }

  /**
   * Render all buildings from map data
   * @param {object} mapData - Map data from backend {buildings: [{id, x, y, building_id, elevation}, ...]}
   */
  renderBuildings(mapData) {
    const buildingsData = mapData.buildings;
    this.clearBuildings();

    if (!buildingsData || buildingsData.length === 0) {
      console.warn("No buildings data provided");
      return;
    }

    // Render each building
    for (const building of buildingsData) {
      // Check building type and render accordingly
      if (building.building_type === "turret") {
        this.renderTurret(building, mapData);
      } else {
        this.renderBuilding(building, mapData);
      }
    }
  }

  /**
   * Render a single building
   * @param {object} building - Building data {id, x, y, building_id, elevation}
   * @param {object} mapData - Map data from backend {width, height, tiles, elevation, buildings}
   */
  renderBuilding(building, mapData) {
    const { x, y, building_id, id } = building;
    const elevation = mapData.elevation[y][x];

    // Convert to isometric coordinates
    // Buildings are 96x96 px (3x3 tiles), offset them to sit on the ground properly
    const iso = cartesianToIsometric(x - 2, y - 2, elevation);
    const depth = getDepthForTile(x + 10, y + 10); // Higher depth than trees

    // Create sprite
    const sprite = this.scene.add.sprite(
      iso.screenX,
      iso.screenY,
      BUILDING_SHEET_ASSET.key,
      building_id,
    );
    sprite.setDepth(depth);
    sprite.setOrigin(0.5, 0.5);
    sprite.setScale(96 / BUILDING_SHEET_ASSET.frameWidth); // Scale to 96px

    // Store building reference
    sprite.buildingId = id;
    this.buildings.push(sprite);
  }

  /**
   * Render a single turret with base and head sprites
   * @param {object} turret - Turret data {id, x, y, building_type, orientation, player_id}
   * @param {object} mapData - Map data from backend {width, height, tiles, elevation, buildings}
   */
  renderTurret(turret, mapData) {
    const { x, y, id, orientation } = turret;
    const elevation = mapData.elevation[y][x];

    // Convert to isometric coordinates
    // Turrets are 96x96 px (3x3 tiles), offset them to sit on the ground properly
    const iso = cartesianToIsometric(x - 2, y-2 , elevation);
    const baseDepth = getDepthForTile(x + 10, y + 10); 
    const headDepth = baseDepth + 1; // Head always in front of base

    // Create turret base sprite (always frame 0)
    const baseSprite = this.scene.add.sprite(
      iso.screenX,
      iso.screenY,
      TURRET_SHEET_ASSET.key,
      TURRET_FRAMES.BASE,
    );
    baseSprite.setDepth(baseDepth);
    baseSprite.setOrigin(0.5, 0.5);
    baseSprite.setScale(96 / TURRET_SHEET_ASSET.frameWidth); // Scale to 96px

    // Create turret head sprite (rotates based on orientation)
    const headFrame = TURRET_FRAMES[orientation] || TURRET_FRAMES[0];
    const headSprite = this.scene.add.sprite(
      iso.screenX,
      iso.screenY,
      TURRET_SHEET_ASSET.key,
      headFrame,
    );
    headSprite.setDepth(headDepth);
    headSprite.setOrigin(0.5, 0.5);
    headSprite.setScale(96 / TURRET_SHEET_ASSET.frameWidth); // Scale to 96px

    // Link sprites together
    baseSprite.turretId = id;
    baseSprite.headSprite = headSprite;
    headSprite.turretId = id;
    headSprite.baseSprite = baseSprite;

    // Store both sprites
    this.buildings.push(baseSprite);
    this.buildings.push(headSprite);
  }

  /**
   * Clear all rendered buildings
   */
  clearBuildings() {
    this.buildings.forEach((building) => {
      if (building) {
        building.destroy();
      }
    });
    this.buildings = [];
  }

  /**
   * Get all rendered building sprites
   * @returns {array} - Array of building sprites
   */
  getBuildings() {
    return this.buildings;
  }

  /**
   * Destroy building manager
   */
  destroy() {
    this.clearBuildings();
  }
}

export default BuildingManager;
