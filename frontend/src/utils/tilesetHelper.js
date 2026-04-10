/**
 * Tileset asset and frame management utilities
 */

import { TILESET_ASSET, TILESET_INDEX, TILE_EMPTY, TILE_TREE } from "../config/mapConfig.js";

/**
 * Load the tileset image and create sprite frames
 * @param {Phaser.Scene} scene - Phaser scene to load the tileset into
 */
export function loadTileset(scene) {
  if (!scene.textures.exists(TILESET_ASSET.key)) {
    // Load as spritesheet with 32x32 tile frames
    scene.load.spritesheet(
      TILESET_ASSET.key,
      TILESET_ASSET.url,
      {
        frameWidth: TILESET_ASSET.tileWidth,
        frameHeight: TILESET_ASSET.tileHeight,
      }
    );
  }
}

/**
 * Get the tileset frame index for a given tile type
 * @param {number} tileType - Tile type constant (TILE_EMPTY, TILE_TREE, etc.)
 * @returns {number} - Tileset sprite index
 */
export function getFrameForTileType(tileType) {
  switch (tileType) {
    case TILE_EMPTY:
      return TILESET_INDEX.GROUND;
    case TILE_TREE:
      return TILESET_INDEX.TREE;
    default:
      return TILESET_INDEX.GROUND;
  }
}

/**
 * Get the tileset key for sprite creation
 * @returns {string} - Tileset key
 */
export function getTilesetKey() {
  return TILESET_ASSET.key;
}

/**
 * Get the tileset URL
 * @returns {string} - Tileset image URL
 */
export function getTilesetUrl() {
  return TILESET_ASSET.url;
}

export default {
  loadTileset,
  getFrameForTileType,
  getTilesetKey,
  getTilesetUrl,
};
