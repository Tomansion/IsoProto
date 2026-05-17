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
  WALL_ASSET,
  BUILDING_TYPES,
  TURRET_FRAMES,
  TURRET_SHOT_FRAMES,
  EXPLOSION_ASSET,
  TURRET_SPAWN_EXPLOSION_ASSET,
  BUILDING_SPAWN_CONFIG,
  SKYLIGHT_ASSET,
} from "../../config/mapConfig.js";

export class BuildingManager {
  constructor(scene) {
    this.scene = scene;
    this.buildings = [];
    this.pendingBuildingEffects = new Map();
  }

  /**
   * Load building assets.
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

    if (!this.scene.textures.exists(WALL_ASSET.key)) {
      this.scene.load.image(WALL_ASSET.key, WALL_ASSET.url);
    }

    if (!this.scene.textures.exists(SKYLIGHT_ASSET.key)) {
      this.scene.load.image(SKYLIGHT_ASSET.key, SKYLIGHT_ASSET.url);
    }
  }

  /**
   * Get spawn visuals for a building type.
   * @param {string} buildingType
   * @returns {object}
   */
  getSpawnConfig(buildingType) {
    return (
      BUILDING_SPAWN_CONFIG[buildingType] ||
      BUILDING_SPAWN_CONFIG[BUILDING_TYPES.TURRET]
    );
  }

  /**
   * Render all buildings from map data.
   * @param {object} mapData
   */
  renderBuildings(mapData) {
    const buildingsData = mapData.buildings;
    this.clearBuildings();

    if (!buildingsData || buildingsData.length === 0) {
      console.warn("No buildings data provided");
      return;
    }

    for (const building of buildingsData) {
      this.renderBuilding(building, mapData, { playSpawnEffect: false });
    }
  }

  /**
   * Render a building using its type.
   * @param {object} building
   * @param {object} mapData
   * @param {object} options
   */
  renderBuilding(building, mapData, { playSpawnEffect = false } = {}) {
    switch (building.building_type) {
      case BUILDING_TYPES.TURRET:
        return this.renderTurret(building, mapData, { playSpawnEffect });
      case BUILDING_TYPES.WALL:
        return this.renderWall(building, mapData, { playSpawnEffect });
      default:
        return this.renderBaseBuilding(building, mapData);
    }
  }

  /**
   * Render a base building from the building sheet.
   * @param {object} building
   * @param {object} mapData
   */
  renderBaseBuilding(building, mapData) {
    const { x, y, building_id, id } = building;
    const elevation = mapData.elevation[y][x];
    const iso = cartesianToIsometric(x - 2, y - 2, elevation);
    const depth = getDepthForTile(x + 10, y + 10);

    const sprite = this.scene.add.sprite(
      iso.screenX,
      iso.screenY,
      BUILDING_SHEET_ASSET.key,
      building_id,
    );
    sprite.setDepth(depth);
    sprite.setOrigin(0.5, 0.5);
    sprite.setScale(96 / BUILDING_SHEET_ASSET.frameWidth);
    sprite.buildingId = id;
    sprite.buildingType = building.building_type;

    this.buildings.push(sprite);
    return sprite;
  }

  /**
   * Render a wall.
   * @param {object} wall
   * @param {object} mapData
   * @param {object} options
   */
  renderWall(wall, mapData, { playSpawnEffect = false } = {}) {
    const { x, y, id } = wall;
    const elevation = mapData.elevation[y][x];

    this.removePendingBuilding(id, { immediate: playSpawnEffect });

    const iso = cartesianToIsometric(x, y, elevation);
    const wallY = iso.screenY - 8;
    const depth = getDepthForTile(x, y) + 5000;

    const wallSprite = this.scene.add.image(iso.screenX, wallY, WALL_ASSET.key);
    wallSprite.setDepth(depth);
    wallSprite.setOrigin(0.5, 0.78);
    wallSprite.buildingId = id;
    wallSprite.buildingType = BUILDING_TYPES.WALL;

    this.buildings.push(wallSprite);

    if (playSpawnEffect) {
      wallSprite.setAlpha(0);
      this.playWallSpawnSequence({
        wallSprite,
        screenX: iso.screenX,
        screenY: wallY,
        depth: depth + 1,
      });
    }

    return wallSprite;
  }

  /**
   * Render a turret with base and head sprites.
   * @param {object} turret
   * @param {object} mapData
   * @param {object} options
   */
  renderTurret(turret, mapData, { playSpawnEffect = false } = {}) {
    const { x, y, id, orientation } = turret;
    const elevation = mapData.elevation[y][x];

    this.removePendingBuilding(id, { immediate: playSpawnEffect });

    const iso = cartesianToIsometric(x - 2, y - 2, elevation);
    const baseDepth = getDepthForTile(x + 10, y + 10);
    const headDepth = baseDepth + 1;

    const baseSprite = this.scene.add.sprite(
      iso.screenX,
      iso.screenY,
      TURRET_SHEET_ASSET.key,
      TURRET_FRAMES.BASE,
    );
    baseSprite.setDepth(baseDepth);
    baseSprite.setOrigin(0.5, 0.5);
    baseSprite.turretId = id;
    baseSprite.buildingType = BUILDING_TYPES.TURRET;

    const headFrame = TURRET_FRAMES[orientation] || TURRET_FRAMES[0];
    const headSprite = this.scene.add.sprite(
      iso.screenX,
      iso.screenY,
      TURRET_SHEET_ASSET.key,
      headFrame,
    );
    headSprite.setDepth(headDepth);
    headSprite.setOrigin(0.5, 0.5);
    headSprite.turretId = id;
    headSprite.baseSprite = baseSprite;
    headSprite.buildingType = BUILDING_TYPES.TURRET;
    baseSprite.headSprite = headSprite;

    this.buildings.push(baseSprite, headSprite);

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

    return { baseSprite, headSprite };
  }

  /**
   * Create a stretched ghost sprite used during spawn falling effects.
   * @param {object} options
   * @param {number} options.screenX
   * @param {number} options.screenY
   * @param {number} options.depth
   * @param {number} options.alpha
   * @param {number} options.stretchY
   * @param {string} options.textureKey
   * @param {number} [options.frame]
   * @param {number} [options.originY=0.5]
   * @param {number} [options.scaleX=1]
   * @returns {Phaser.GameObjects.Image|Phaser.GameObjects.Sprite}
   */
  createGhostSprite({
    screenX,
    screenY,
    depth,
    alpha,
    stretchY,
    textureKey,
    frame,
    originY = 0.5,
    scaleX = 1,
  }) {
    const sprite =
      frame === undefined
        ? this.scene.add.image(screenX, screenY, textureKey)
        : this.scene.add.sprite(screenX, screenY, textureKey, frame);

    sprite.setOrigin(0.5, originY);
    sprite.setDepth(depth);
    sprite.setAlpha(alpha);
    sprite.setScale(scaleX, stretchY);
    return sprite;
  }

  /**
   * Play the falling turret spawn sequence.
   * @param {object} options
   */
  playTurretSpawnSequence({
    baseSprite,
    headSprite,
    screenX,
    screenY,
    headFrame,
    depth,
  }) {
    const spawnConfig = this.getSpawnConfig(BUILDING_TYPES.TURRET);
    const fallSprites = [];
    const startY = screenY - spawnConfig.dropHeight;

    for (let index = 0; index < spawnConfig.blurLayers; index += 1) {
      const alpha = Math.max(0.14, 0.35 - index * 0.09);
      const yOffset = index * spawnConfig.blurSpacing;
      const layerDepth = depth + spawnConfig.blurLayers - index;

      fallSprites.push(
        this.createGhostSprite({
          screenX,
          screenY: startY - yOffset,
          depth: layerDepth,
          alpha,
          stretchY: spawnConfig.stretchY,
          textureKey: TURRET_SHEET_ASSET.key,
          frame: TURRET_FRAMES.BASE,
          scaleX: 0.5,
        }),
      );
      fallSprites.push(
        this.createGhostSprite({
          screenX,
          screenY: startY - yOffset,
          depth: layerDepth + 0.1,
          alpha,
          stretchY: spawnConfig.stretchY,
          textureKey: TURRET_SHEET_ASSET.key,
          frame: headFrame,
          scaleX: 0.5,
        }),
      );
    }

    this.scene.tweens.add({
      targets: fallSprites,
      y: screenY,
      duration: spawnConfig.dropDuration,
      ease: "Cubic.easeIn",
      onComplete: () => {
        fallSprites.forEach((sprite) => sprite.destroy());
        baseSprite.setAlpha(1);
        headSprite.setAlpha(1);
        this.playBuildingSpawnEffect(
          BUILDING_TYPES.TURRET,
          screenX,
          screenY,
          depth,
        );
      },
    });
  }

  /**
   * Play the falling wall spawn sequence.
   * @param {object} options
   */
  playWallSpawnSequence({ wallSprite, screenX, screenY, depth }) {
    const spawnConfig = this.getSpawnConfig(BUILDING_TYPES.WALL);
    const fallSprites = [];
    const startY = screenY - spawnConfig.dropHeight;

    for (let index = 0; index < spawnConfig.blurLayers; index += 1) {
      const alpha = Math.max(0.14, 0.34 - index * 0.09);
      const yOffset = index * spawnConfig.blurSpacing;
      const layerDepth = depth + spawnConfig.blurLayers - index;

      fallSprites.push(
        this.createGhostSprite({
          screenX,
          screenY: startY - yOffset,
          depth: layerDepth,
          alpha,
          stretchY: spawnConfig.stretchY,
          textureKey: WALL_ASSET.key,
          originY: 0.78,
        }),
      );
    }

    this.scene.tweens.add({
      targets: fallSprites,
      y: screenY,
      duration: spawnConfig.dropDuration,
      ease: "Cubic.easeIn",
      onComplete: () => {
        fallSprites.forEach((sprite) => sprite.destroy());
        wallSprite.setAlpha(1);
        this.playBuildingSpawnEffect(
          BUILDING_TYPES.WALL,
          screenX,
          screenY,
          depth,
        );
      },
    });
  }

  /**
   * Play the spawn explosion effect for a building.
   * @param {string} buildingType
   * @param {number} screenX
   * @param {number} screenY
   * @param {number} depth
   */
  playBuildingSpawnEffect(buildingType, screenX, screenY, depth) {
    const spawnConfig = this.getSpawnConfig(buildingType);
    const spawnEffect = this.scene.add.sprite(
      screenX,
      screenY,
      TURRET_SPAWN_EXPLOSION_ASSET.key,
      0,
    );
    spawnEffect.setDepth(depth);
    spawnEffect.setOrigin(0.5, spawnConfig.explosionOriginY);
    spawnEffect.setScale(spawnConfig.explosionScale);
    spawnEffect.play("turret-spawn-explosion");
    spawnEffect.on("animationcomplete", () => {
      spawnEffect.destroy();
    });
  }

  /**
   * Render the temporary skylight shown while a building is being built.
   * @param {object} pendingBuilding
   */
  renderPendingBuilding(pendingBuilding) {
    if (
      !pendingBuilding ||
      this.pendingBuildingEffects.has(pendingBuilding.id)
    ) {
      return;
    }

    const spawnConfig = this.getSpawnConfig(pendingBuilding.building_type);
    const { screenX, screenY } = cartesianToIsometric(
      pendingBuilding.x + spawnConfig.pendingOffsetX,
      pendingBuilding.y + spawnConfig.pendingOffsetY,
      pendingBuilding.elevation || 0,
    );
    const depth =
      getDepthForTile(pendingBuilding.x, pendingBuilding.y) +
      spawnConfig.pendingDepthBoost;

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

    this.pendingBuildingEffects.set(pendingBuilding.id, {
      sprite: beamSprite,
      tween: alphaTween,
    });
  }

  /**
   * Remove a pending building skylight.
   * @param {string} pendingBuildingId
   * @param {object} options
   */
  removePendingBuilding(pendingBuildingId, { immediate = false } = {}) {
    const effect = this.pendingBuildingEffects.get(pendingBuildingId);
    if (!effect) {
      return;
    }

    if (immediate) {
      effect.tween?.stop();
      effect.sprite?.destroy();
      this.pendingBuildingEffects.delete(pendingBuildingId);
      return;
    }

    this.scene.tweens.add({
      targets: effect.sprite,
      alpha: 0,
      duration: 300,
      onComplete: () => {
        effect.sprite.destroy();
      },
    });

    effect.tween?.stop();
    this.pendingBuildingEffects.delete(pendingBuildingId);
  }

  /**
   * Clear all rendered buildings.
   */
  clearBuildings() {
    this.buildings.forEach((building) => {
      if (building) {
        building.destroy();
      }
    });
    this.buildings = [];
    this.clearPendingBuildings();
  }

  /**
   * Clear all pending building effects.
   */
  clearPendingBuildings() {
    for (const pendingBuildingId of this.pendingBuildingEffects.keys()) {
      this.removePendingBuilding(pendingBuildingId, { immediate: true });
    }
  }

  /**
   * Backward-compatible pending turret clear wrapper.
   */
  clearPendingTurrets() {
    this.clearPendingBuildings();
  }

  /**
   * Get all rendered building sprites.
   * @returns {array}
   */
  getBuildings() {
    return this.buildings;
  }

  /**
   * Update turret head sprites to show new orientations.
   * @param {Array} rotations
   */
  updateTurretRotations(rotations) {
    if (!rotations || rotations.length === 0) return;

    const rotationMap = new Map();
    for (const rotation of rotations) {
      rotationMap.set(rotation.id, rotation);
    }

    for (const building of this.buildings) {
      if (!building.turretId) continue;

      const rotation = rotationMap.get(building.turretId);
      if (!rotation) continue;

      if (building.baseSprite) {
        const newFrame =
          TURRET_FRAMES[rotation.orientation] || TURRET_FRAMES[0];
        building.setFrame(newFrame);
      }
    }
  }

  /**
   * Play shot animations for turrets.
   * @param {Array} shots
   * @param {Array} mobs
   */
  playShotAnimations(shots, mobs = []) {
    if (!shots || shots.length === 0) return;

    const mobMap = new Map();
    for (const mob of mobs) {
      mobMap.set(mob.id, mob);
    }

    for (const shot of shots) {
      const turretBase = this.buildings.find(
        (building) =>
          building.turretId === shot.turret_id && !building.baseSprite,
      );
      if (!turretBase) continue;

      const shotFrame = TURRET_SHOT_FRAMES[shot.orientation];
      if (shotFrame === undefined) {
        throw new Error(
          `No shot frame defined for orientation ${shot.orientation}`,
        );
      }

      const shotSprite = this.scene.add.sprite(
        turretBase.x,
        turretBase.y,
        TURRET_SHEET_ASSET.key,
        shotFrame,
      );
      shotSprite.setDepth(turretBase.depth + 1);
      shotSprite.setOrigin(0.5, 0.5);

      this.scene.time.delayedCall(200, () => {
        shotSprite.destroy();
      });

      const targetMob = mobMap.get(shot.mob_id);
      if (targetMob) {
        const explosionIso = cartesianToIsometric(
          targetMob.x,
          targetMob.y,
          targetMob.elevation || 0,
        );
        const explosionDepth = getDepthForTile(targetMob.x, targetMob.y) + 10;

        const explosionSprite = this.scene.add.sprite(
          explosionIso.screenX,
          explosionIso.screenY,
          EXPLOSION_ASSET.key,
          0,
        );
        explosionSprite.setDepth(explosionDepth);
        explosionSprite.setOrigin(0.5, 1);
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
