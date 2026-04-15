/**
 * Isometric coordinate conversion utilities
 * Converts between cartesian (map) coordinates and isometric screen coordinates
 */

import { TILE_SIZE } from "../config/mapConfig.js";

/**
 * Convert cartesian (map) coordinates to isometric screen coordinates
 * @param {number} x - Cartesian X coordinate (column in map grid)
 * @param {number} y - Cartesian Y coordinate (row in map grid)
 * @param {number} elevation - Elevation value (default 0)
 * @returns {object} {screenX, screenY} - Screen coordinates in pixels
 */
export function cartesianToIsometric(x, y, elevation = 0) {
  const tileWidth = TILE_SIZE;
  const tileHeight = TILE_SIZE;

  // Standard isometric projection formulas
  const screenX = (x - y) * (tileWidth / 2);
  const screenY = (x + y) * (tileHeight / 4) - elevation * 3; // Elevation lifts tiles up

  return {
    screenX,
    screenY,
  };
}

/**
 * Convert isometric screen coordinates back to cartesian map coordinates
 * @param {number} screenX - Screen X coordinate in pixels
 * @param {number} screenY - Screen Y coordinate in pixels
 * @returns {object} {x, y} - Cartesian map coordinates
 */
export function isometricToCartesian(screenX, screenY) {
  const tileWidth = TILE_SIZE;
  const tileHeight = TILE_SIZE;

  // Inverse isometric projection
  const x = (screenX / (tileWidth / 2) + screenY / (tileHeight / 2)) / 2;
  const y = (screenY / (tileHeight / 2) - screenX / (tileWidth / 2)) / 2;

  return {
    x: Math.round(x),
    y: Math.round(y),
  };
}

/**
 * Get the depth (z-order) for a tile based on its position
 * Used to ensure correct visual layering in isometric view
 * @param {number} x - Cartesian X coordinate
 * @param {number} y - Cartesian Y coordinate
 * @returns {number} - Depth value for z-ordering
 */
export function getDepthForTile(x, y) {
  // In isometric view, tiles further "back" (higher y, then by x) appear behind
  return y * 10000 + x;
}

/**
 * Calculate the center/pivot point for a tile sprite
 * Isometric tiles are typically centered at their base
 * @returns {object} {x, y} - Relative pivot point (0-1 range)
 */
export function getTilePivot() {
  return {
    x: 0.5,
    y: 0.5,
  };
}

export default {
  cartesianToIsometric,
  isometricToCartesian,
  getDepthForTile,
  getTilePivot,
};
