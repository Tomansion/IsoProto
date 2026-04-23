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
    this.tileClickCallback = null;
    this.dragChecker = null;
    this.pointerStartX = null;
    this.pointerStartY = null;
    this.dragThreshold = 5;
  }

  /**
   * Set the callback for tile clicks
   * @param {function} callback - Callback function(x, y) called when a tile is clicked
   */
  setTileClickCallback(callback) {
    this.tileClickCallback = callback;
  }

  /**
   * Set a function to check if currently dragging
   * @param {function} dragChecker - Function that returns true if dragging
   */
  setDragChecker(dragChecker) {
    this.dragChecker = dragChecker;
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
        this.renderGroundTile(
          x,
          y,
          tileElevation,
          tileType !== TILE_TREE && tileElevation > 0,
        );
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
   * @param {boolean} isInteractive - Whether the tile is interactive (not a tree)
   */
  renderGroundTile(x, y, elevation = 0, isInteractive = true) {
    const iso = cartesianToIsometric(x, y, elevation);
    const depth = getDepthForTile(x, y);

    let tile;

    if (elevation == 0) tile = TILESET_INDEX.WATER;
    else if (elevation > 2) tile = TILESET_INDEX.GROUND;
    else tile = TILESET_INDEX.DIRT;

    const sprite = this.scene.add.sprite(
      iso.screenX,
      iso.screenY,
      getTilesetKey(),
      tile,
    );
    sprite.setDepth(depth);
    sprite.setOrigin(0.5, 0.5);
    sprite.setScale(TILE_SIZE / 32);

    sprite.tileX = x;
    sprite.tileY = y;
    // Make sprite interactive with custom hit area
    if (isInteractive) {
      sprite.setInteractive({
        draggable: true,
        useHandCursor: true,
        pixelPerfect: true,
        alphaTolerance: 1,
      });

      // Track pointer movement for this tile
      let tilePointerStartX = null;
      let tilePointerStartY = null;

      sprite.on("pointerdown", (pointer) => {
        tilePointerStartX = pointer.x;
        tilePointerStartY = pointer.y;
      });

      sprite.on("pointerup", (pointer) => {
        // Check if pointer moved during press (drag vs click)
        const deltaX = Math.abs(pointer.x - tilePointerStartX);
        const deltaY = Math.abs(pointer.y - tilePointerStartY);
        const wasDrag =
          deltaX > this.dragThreshold || deltaY > this.dragThreshold;

        // Only register tile click if it was a click, not a drag
        if (this.tileClickCallback && !wasDrag) {
          this.tileClickCallback(x, y);
        }

        tilePointerStartX = null;
        tilePointerStartY = null;
      });
    }

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
        tile.off("pointerdown");
        tile.off("pointerup");
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
