/**
 * Mob rendering and management
 * Handles spawning, updating, and removing enemy sprites on the isometric map
 */

import { ZOMBIE_ASSET, ZOMBIE_ANIM_FRAMERATE } from "../../config/mapConfig.js";
import {
  cartesianToIsometric,
  getDepthForTile,
} from "../../utils/isometricHelper.js";

export class MobManager {
  constructor(scene) {
    this.scene = scene;
    this.mobSprites = {}; // mob.id -> Phaser.GameObjects.Sprite
  }

  /**
   * Load mob spritesheet assets (call in scene preload)
   */
  loadAssets() {
    if (!this.scene.textures.exists(ZOMBIE_ASSET.key)) {
      this.scene.load.spritesheet(ZOMBIE_ASSET.key, ZOMBIE_ASSET.url, {
        frameWidth: ZOMBIE_ASSET.frameWidth,
        frameHeight: ZOMBIE_ASSET.frameHeight,
      });
    }
  }

  /**
   * Create Phaser animations for mobs (call in scene create)
   */
  createAnimations() {
    if (!this.scene.anims.exists("zombie-walk")) {
      this.scene.anims.create({
        key: "zombie-walk",
        frames: this.scene.anims.generateFrameNumbers(ZOMBIE_ASSET.key, {
          start: 0,
          end: 5,
        }),
        frameRate: ZOMBIE_ANIM_FRAMERATE,
        repeat: -1,
      });
    }
  }

  /**
   * Update all mob sprites based on the latest server data.
   * Creates new sprites for new mobs, updates positions for existing ones,
   * and removes sprites for mobs that are no longer present.
   *
   * @param {Array} mobs - Array of mob data objects {id, x, y, hp, mob_type, elevation}
   */
  updateMobs(mobs) {
    // Track which mob IDs are still active
    const activeMobIds = new Set(mobs.map((m) => m.id));

    // Destroy sprites for mobs that are gone (reached target or died)
    for (const id of Object.keys(this.mobSprites)) {
      if (!activeMobIds.has(id)) {
        this.mobSprites[id].destroy();
        delete this.mobSprites[id];
      }
    }

    // Update or create sprites for each active mob
    for (const mob of mobs) {
      const { screenX, screenY } = cartesianToIsometric(
        mob.x,
        mob.y,
        mob.elevation || 0,
      );
      // Add a small offset so mobs appear above the tile surface
      const depth = getDepthForTile(Math.floor(mob.x), Math.floor(mob.y)) + 15000;

      const flipX = mob.direction_x < 0;

      if (this.mobSprites[mob.id]) {
        // Move existing sprite
        const sprite = this.mobSprites[mob.id];
        sprite.setPosition(screenX, screenY);
        sprite.setDepth(depth);
        sprite.setFlipX(flipX);
      } else {
        // Spawn new sprite
        const sprite = this.scene.add.sprite(screenX, screenY, ZOMBIE_ASSET.key);
        sprite.setOrigin(0.5, 1.25); // Anchor near the feet for better isometric look
        sprite.setDepth(depth);
        sprite.setFlipX(flipX);
        sprite.play("zombie-walk");
        this.mobSprites[mob.id] = sprite;
      }
    }
  }

  /**
   * Remove all mob sprites from the scene
   */
  clearMobs() {
    for (const sprite of Object.values(this.mobSprites)) {
      sprite.destroy();
    }
    this.mobSprites = {};
  }

  /**
   * Destroy the mob manager and all its sprites
   */
  destroy() {
    this.clearMobs();
  }
}

export default MobManager;
