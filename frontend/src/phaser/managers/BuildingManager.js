/**
 * Building rendering and management
 * Handles placement and rendering of buildings on the map
 */

import {
  cartesianToIsometric,
  getDepthForTile,
} from "../../utils/isometricHelper.js";
import { BUILDING_SHEET_ASSET } from "../../config/mapConfig.js";

export class BuildingManager {
  constructor(scene) {
    this.scene = scene;
    this.buildings = [];
  }

  /**
   * Load building spritesheet asset
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
  }

  /**
   * Render all buildings from building data
   * @param {object[]} buildingsData - Array of building data {id, x, y, building_id, elevation}
   */
  renderBuildings(buildingsData) {
    this.clearBuildings();

    if (!buildingsData || buildingsData.length === 0) {
      console.warn("No buildings data provided");
      return;
    }

    // Render each building
    for (const building of buildingsData) {
      this.renderBuilding(building);
    }
  }

  /**
   * Render a single building
   * @param {object} building - Building data {id, x, y, building_id, elevation}
   */
  renderBuilding(building) {
    const { x, y, building_id, id, elevation } = building;

    // Convert to isometric coordinates
    // Buildings are 96x96 px (3x3 tiles), offset them to sit on the ground properly
    const iso = cartesianToIsometric(x - 1, y -1, elevation);
    const depth = getDepthForTile(x, y+4); // Higher depth than trees

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
