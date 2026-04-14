/**
 * Tile rendering and placement management
 * Handles placement and rendering of individual tiles on the map
 */

import {
  cartesianToIsometric,
  getDepthForTile,
} from "../../utils/isometricHelper.js";
import {
  getFrameForTileType,
  getTilesetKey,
} from "../../utils/tilesetHelper.js";
import {
  TILE_EMPTY,
  TILE_TREE,
  TILE_SIZE,
  TILESET_INDEX,
} from "../../config/mapConfig.js";

export class TileManager {
  constructor(scene, layerManager) {
    this.scene = scene;
    this.layerManager = layerManager;
    this.tiles = [];
  }

  /**
   * Render all tiles from map data
   * @param {object} mapData - Map data from backend {width, height, tiles: [[...]], elevation: [[...]]}
   */
  renderTiles(mapData) {
    this.clearTiles();

    const { tiles, elevation, width, height } = mapData;

    let groundCount = 0;
    let treeCount = 0;

    // Iterate through each tile in the map
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const tileType = tiles[y][x];
        const tileElevation = elevation && elevation[y] ? elevation[y][x] : 0;

        // Always render ground tile
        this.renderGroundTile(x, y, tileElevation);
        groundCount++;

        // Render tree if present
        if (tileType === TILE_TREE) {
          this.renderTreeTile(x, y, tileElevation);
          treeCount++;
        }
      }
    }
  }

  /**
   * Render a ground tile at the given coordinates
   * @param {number} x - Cartesian X coordinate
   * @param {number} y - Cartesian Y coordinate
   * @param {number} elevation - Elevation value
   */
  renderGroundTile(x, y, elevation = 0) {
    const iso = cartesianToIsometric(x, y, elevation);
    const depth = getDepthForTile(x, y);

    const sprite = this.scene.add.sprite(
      iso.screenX,
      iso.screenY,
      getTilesetKey(),
      TILESET_INDEX.GROUND,
    );
    sprite.setDepth(depth);
    sprite.setOrigin(0.5, 0.5);
    sprite.setScale(TILE_SIZE / 32);

    this.tiles.push(sprite);
  }

  /**
   * Render a tree tile at the given coordinates (above the ground tile)
   * @param {number} x - Cartesian X coordinate
   * @param {number} y - Cartesian Y coordinate
   * @param {number} elevation - Elevation value
   */
  renderTreeTile(x, y, elevation = 0) {
    // Trees are offset and should sit on the elevated ground
    const randomOffsetX = (Math.random() - 0.5) * 5; // Random horizontal offset for natural look
    const randomOffsetY = (Math.random() - 0.5) * 4; // Random vertical offset for natural look
    const iso = cartesianToIsometric(x - 1, y - 1, elevation);
    const depth = getDepthForTile(x, y) + 100000; // higher depth for layering

    const sprite = this.scene.add.sprite(
      iso.screenX + randomOffsetX,
      iso.screenY + randomOffsetY,
      getTilesetKey(),
      TILESET_INDEX.TREE,
    );
    sprite.setDepth(depth);
    sprite.setOrigin(0.5, 0.5);
    sprite.setScale(TILE_SIZE / 32);

    this.tiles.push(sprite);
  }

  /**
   * Clear all rendered tiles
   */
  clearTiles() {
    this.tiles.forEach((tile) => {
      if (tile) {
        tile.destroy();
      }
    });
    this.tiles = [];
  }

  /**
   * Get all rendered tile sprites
   * @returns {array} - Array of tile sprites
   */
  getTiles() {
    return this.tiles;
  }

  /**
   * Destroy tile manager
   */
  destroy() {
    this.clearTiles();
  }
}

export default TileManager;
