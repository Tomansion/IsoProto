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
  EXPLOSION_ASSET,
  TURRET_SPAWN_EXPLOSION_ASSET,
  TURRET_SPAWN_DROP_DURATION,
  TURRET_SPAWN_DROP_HEIGHT,
  TURRET_SPAWN_DROP_STRETCH_Y,
  TURRET_SPAWN_BLUR_LAYERS,
  SKYLIGHT_ASSET,
} from "../../config/mapConfig.js";

export class BuildingManager {
  constructor(scene) {
    this.scene = scene;
    this.buildings = [];
    this.turrets = []; // Track turrets separately (each is {baseSprite, headSprite})
    this.pendingTurretEffects = new Map();
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

    if (!this.scene.textures.exists(SKYLIGHT_ASSET.key)) {
      this.scene.load.image(SKYLIGHT_ASSET.key, SKYLIGHT_ASSET.url);
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
        this.renderTurret(building, mapData, { playSpawnEffect: false });
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
  renderTurret(turret, mapData, { playSpawnEffect = false } = {}) {
    const { x, y, id, orientation } = turret;
    const elevation = mapData.elevation[y][x];

    this.removePendingTurret(id, { immediate: playSpawnEffect });

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

    if (playSpawnEffect) {
      baseSprite.setAlpha(0);
      headSprite.setAlpha(0);
      this.playTurretSpawnSequence({
        baseSprite,
        headSprite,
        screenX: iso.screenX,
        screenY: iso.screenY,
        headFrame,
        depth: headDepth + 1,
      });
    }
  }

  /**
   * Play a very fast falling turret silhouette before revealing the turret.
   * @param {object} options
   * @param {Phaser.GameObjects.Sprite} options.baseSprite
   * @param {Phaser.GameObjects.Sprite} options.headSprite
   * @param {number} options.screenX
   * @param {number} options.screenY
   * @param {number} options.headFrame
   * @param {number} options.depth
   */
  playTurretSpawnSequence({
    baseSprite,
    headSprite,
    screenX,
    screenY,
    headFrame,
    depth,
  }) {
    const fallSprites = [];
    const startY = screenY - TURRET_SPAWN_DROP_HEIGHT;

    for (let index = 0; index < TURRET_SPAWN_BLUR_LAYERS; index += 1) {
      const alpha = 0.35 - index * 0.09;
      const yOffset = index * 48;
      const layerDepth = depth + TURRET_SPAWN_BLUR_LAYERS - index;

      const fallBaseSprite = this.scene.add.sprite(
        screenX,
        startY - yOffset,
        TURRET_SHEET_ASSET.key,
        TURRET_FRAMES.BASE,
      );
      fallBaseSprite.setOrigin(0.5, 0.5);
      fallBaseSprite.setDepth(layerDepth);
      fallBaseSprite.setAlpha(alpha);
      fallBaseSprite.setScale(0.5, TURRET_SPAWN_DROP_STRETCH_Y);

      const fallHeadSprite = this.scene.add.sprite(
        screenX,
        startY - yOffset,
        TURRET_SHEET_ASSET.key,
        headFrame,
      );
      fallHeadSprite.setOrigin(0.5, 0.5);
      fallHeadSprite.setDepth(layerDepth + 0.1);
      fallHeadSprite.setAlpha(alpha);
      fallHeadSprite.setScale(0.5, TURRET_SPAWN_DROP_STRETCH_Y);

      fallSprites.push(fallBaseSprite, fallHeadSprite);
    }

    this.scene.tweens.add({
      targets: fallSprites,
      y: screenY,
      duration: TURRET_SPAWN_DROP_DURATION,
      ease: "Cubic.easeIn",
      onComplete: () => {
        fallSprites.forEach((sprite) => sprite.destroy());
        baseSprite.setAlpha(1);
        headSprite.setAlpha(1);
        this.playTurretSpawnEffect(screenX, screenY, depth);
      },
    });
  }

  /**
   * Play the turret spawn explosion effect.
   * @param {number} screenX - Isometric screen X position
   * @param {number} screenY - Isometric screen Y position
   * @param {number} depth - Render depth for the effect
   */
  playTurretSpawnEffect(screenX, screenY, depth) {
    const spawnEffect = this.scene.add.sprite(
      screenX,
      screenY,
      TURRET_SPAWN_EXPLOSION_ASSET.key,
      0,
    );
    spawnEffect.setDepth(depth);
    spawnEffect.setOrigin(0.5, 0.8);
    spawnEffect.setScale(5); // Scale up for better visibility

    spawnEffect.play("turret-spawn-explosion");
    spawnEffect.on("animationcomplete", () => {
      spawnEffect.destroy();
    });
  }

  /**
   * Render the temporary beam shown while a turret is building.
   * @param {object} pendingTurret - Pending turret data {id, x, y, elevation}
   */
  renderPendingTurret(pendingTurret) {
    if (!pendingTurret || this.pendingTurretEffects.has(pendingTurret.id)) {
      return;
    }

    const { screenX, screenY } = cartesianToIsometric(
      pendingTurret.x + 1,
      pendingTurret.y + 1,
      pendingTurret.elevation || 0,
    );
    const depth =
      getDepthForTile(pendingTurret.x, pendingTurret.y) + 25000;

    const beamSprite = this.scene.add.image(
      screenX,
      screenY,
      SKYLIGHT_ASSET.key,
    );
    beamSprite.setOrigin(0.5, 1);
    beamSprite.setDepth(depth);
    beamSprite.setAlpha(0.75);

    const alphaTween = this.scene.tweens.add({
      targets: beamSprite,
      alpha: { from: 0.85, to: 0.5 },
      duration: 1200,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });

    this.pendingTurretEffects.set(pendingTurret.id, {
      sprite: beamSprite,
      tween: alphaTween,
    });
  }

  /**
   * Remove a pending turret beam by pending turret id.
   * @param {string} pendingTurretId
   */
  removePendingTurret(pendingTurretId, { immediate = false } = {}) {
    const effect = this.pendingTurretEffects.get(pendingTurretId);
    if (!effect) {
      return;
    }

    if (immediate) {
      effect.tween?.stop();
      effect.sprite?.destroy();
      this.pendingTurretEffects.delete(pendingTurretId);
      return;
    }

    // Smoothly fade out the beam before destroying
    this.scene.tweens.add({
      targets: effect.sprite,
      alpha: 0,
      duration: 300,
      onComplete: () => {
        effect.sprite.destroy();
      },
    });

    // Stop the pulsing tween
    effect.tween.stop();

    this.pendingTurretEffects.delete(pendingTurretId);
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
    this.clearPendingTurrets();
  }

  /**
   * Clear all pending turret effects.
   */
  clearPendingTurrets() {
    for (const pendingTurretId of this.pendingTurretEffects.keys()) {
      this.removePendingTurret(pendingTurretId, { immediate: true });
    }
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
  /**
   * Play shot animations for turrets.
   * @param {Array} shots - Array of shot data {turret_id, turret_x, turret_y, orientation, mob_id, damage}
   * @param {Array} mobs - Array of mob data {id, x, y, elevation, ...} to find target positions
   */
  playShotAnimations(shots, mobs = []) {
    if (!shots || shots.length === 0) return;

    // Create a map of mob IDs to their positions for quick lookup
    const mobMap = new Map();
    for (const mob of mobs) {
      mobMap.set(mob.id, mob);
    }

    for (const shot of shots) {
      // Find turret base sprite by turret_id
      const turretBase = this.buildings.find(
        (b) => b.turretId === shot.turret_id && !b.baseSprite,
      );
      if (!turretBase) continue;

      // Get the shot frame for this orientation
      const shotFrame = TURRET_SHOT_FRAMES[shot.orientation];
      if (shotFrame === undefined)
        throw new Error(
          `No shot frame defined for orientation ${shot.orientation}`,
        );

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

      // Play explosion animation at target mob location
      const targetMob = mobMap.get(shot.mob_id);
      if (targetMob) {
        const explosionIso = cartesianToIsometric(
          targetMob.x,
          targetMob.y,
          targetMob.elevation || 0,
        );
        const explosionDepth = getDepthForTile(targetMob.x, targetMob.y) + 10; // High depth to appear on top

        const explosionSprite = this.scene.add.sprite(
          explosionIso.screenX,
          explosionIso.screenY,
          EXPLOSION_ASSET.key,
          0, // Start at frame 0
        );
        explosionSprite.setDepth(explosionDepth);
        explosionSprite.setOrigin(0.5, 1);

        // Play the explosion animation, then destroy the sprite
        explosionSprite.play("explosion");
        explosionSprite.on("animationcomplete", () => {
          explosionSprite.destroy();
        });
      }
    }
  }

  /**
   * Destroy the building manager and all rendered objects.
   */
  destroy() {
    this.clearBuildings();
  }
}

export default BuildingManager;
