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
  TURRET_SHOT_FRAMES,
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
    const iso = cartesianToIsometric(x - 2, y - 2, elevation);
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
   * Update turret head sprites to show new orientations.
   * @param {Array} rotations - Array of turret rotation data {id, orientation}
   */
  updateTurretRotations(rotations) {
    if (!rotations || rotations.length === 0) return;

    // Create a map of building IDs to rotation data for quick lookup
    const rotationMap = new Map();
    for (const rotation of rotations) {
      rotationMap.set(rotation.id, rotation);
    }

    // Find and update turret head sprites
    for (const building of this.buildings) {
      if (!building.turretId) continue;

      const rotation = rotationMap.get(building.turretId);
      if (!rotation) continue;

      // Only update head sprites (they have a baseSprite reference)
      if (building.baseSprite) {
        // This is a head sprite, update its frame
        const newFrame =
          TURRET_FRAMES[rotation.orientation] || TURRET_FRAMES[0];
        building.setFrame(newFrame);
      }
    }
  }

  /**
   * Play shot animations for turrets.
   * @param {Array} shots - Array of shot data {turret_id, turret_x, turret_y, orientation, mob_id, damage}
   */
  playShotAnimations(shots) {
    if (!shots || shots.length === 0) return;

    for (const shot of shots) {
      // Find turret base sprite by turret_id
      const turretBase = this.buildings.find(
        (b) => b.turretId === shot.turret_id && !b.baseSprite,
      );
      if (!turretBase) continue;

      // Get the shot frame for this orientation
      const shotFrame = TURRET_SHOT_FRAMES[shot.orientation];
      if (shotFrame === undefined) throw new Error(`No shot frame defined for orientation ${shot.orientation}`);

      // Create a temporary shot effect sprite at the turret location
      const shotSprite = this.scene.add.sprite(
        turretBase.x,
        turretBase.y,
        TURRET_SHEET_ASSET.key,
        shotFrame,
      );
      shotSprite.setDepth(turretBase.depth + 1);
      shotSprite.setOrigin(0.5, 0.5);

      // Hold the frame for 200ms then destroy
      this.scene.time.delayedCall(200, () => {
        shotSprite.destroy();
      });
    }
  }
}

export default BuildingManager;
