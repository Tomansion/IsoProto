/**
 * Tile rendering and placement management
 * Handles placement and rendering of individual tiles on the map
 */

import { cartesianToIsometric, getDepthForTile } from "../../utils/isometricHelper.js";
import { getFrameForTileType, getTilesetKey } from "../../utils/tilesetHelper.js";
import { TILE_EMPTY, TILE_TREE, TILE_SIZE, TILESET_INDEX } from "../../config/mapConfig.js";

export class TileManager {
  constructor(scene, layerManager) {
    this.scene = scene;
    this.layerManager = layerManager;
    this.tiles = [];
  }

  /**
   * Render all tiles from map data
   * @param {object} mapData - Map data from backend {width, height, tiles: [[...]]}
   */
  renderTiles(mapData) {
    this.clearTiles();

    const { tiles, width, height } = mapData;

    // Iterate through each tile in the map
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const tileType = tiles[y][x];

        // Always render ground tile
        this.renderGroundTile(x, y);

        // Render tree if present
        if (tileType === TILE_TREE) {
          this.renderTreeTile(x, y);
        }
      }
    }
  }

  /**
   * Render a ground tile at the given coordinates
   * @param {number} x - Cartesian X coordinate
   * @param {number} y - Cartesian Y coordinate
   */
  renderGroundTile(x, y) {
    const iso = cartesianToIsometric(x, y);
    const depth = getDepthForTile(x, y);

    const sprite = this.scene.add.sprite(iso.screenX, iso.screenY, getTilesetKey(), TILESET_INDEX.GROUND);
    sprite.setDepth(depth);
    sprite.setOrigin(0.5, 0.5);
    sprite.setScale(TILE_SIZE / 32);

    this.tiles.push(sprite);
  }

  /**
   * Render a tree tile at the given coordinates (above the ground tile)
   * @param {number} x - Cartesian X coordinate
   * @param {number} y - Cartesian Y coordinate
   */
  renderTreeTile(x, y) {
    const iso = cartesianToIsometric(x, y);
    const depth = getDepthForTile(x, y) + 0.5; // Slightly higher depth for layering

    const sprite = this.scene.add.sprite(iso.screenX, iso.screenY, getTilesetKey(), TILESET_INDEX.TREE);
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
