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
    this.tileSprites = new Map();
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

    // Iterate through each tile in the map
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        this.renderTileAt(mapData, x, y);
      }
    }
  }

  /**
   * Update only changed tiles without redrawing the full map.
   * @param {object} mapData - Full map data from backend
   * @param {Array} changedTiles - Array of tile updates {x, y, tile}
   */
  updateTiles(mapData, changedTiles) {
    if (!mapData || !Array.isArray(changedTiles) || changedTiles.length === 0) {
      return;
    }

    for (const changedTile of changedTiles) {
      const { x, y } = changedTile;
      this.clearTileAt(x, y);
      this.renderTileAt(mapData, x, y);
    }
  }

  getTileKey(x, y) {
    return `${x},${y}`;
  }

  renderTileAt(mapData, x, y) {
    const tileType = mapData.tiles[y][x];
    const tileElevation =
      mapData.elevation && mapData.elevation[y] ? mapData.elevation[y][x] : 0;

    const groundSprite = this.renderGroundTile(
      x,
      y,
      tileElevation,
      tileElevation > 0,
    );
    let treeSprite = null;

    if (tileType === TILE_TREE) {
      treeSprite = this.renderTreeTile(x, y, tileElevation);
    }

    this.tileSprites.set(this.getTileKey(x, y), {
      groundSprite,
      treeSprite,
    });
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
    return sprite;
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
    return sprite;
  }

  destroyTileSprite(sprite) {
    if (!sprite) {
      return;
    }

    sprite.off("pointerdown");
    sprite.off("pointerup");
    sprite.destroy();

    this.tiles = this.tiles.filter((tile) => tile !== sprite);
  }

  clearTileAt(x, y) {
    const tileEntry = this.tileSprites.get(this.getTileKey(x, y));
    if (!tileEntry) {
      return;
    }

    this.destroyTileSprite(tileEntry.groundSprite);
    this.destroyTileSprite(tileEntry.treeSprite);
    this.tileSprites.delete(this.getTileKey(x, y));
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
    this.tileSprites.clear();
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
