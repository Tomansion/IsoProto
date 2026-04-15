/**
 * Map tile and layer configuration
 */

// Tile types
export const TILE_EMPTY = 0;
export const TILE_TREE = 1;

// Tileset sprite indices
export const TILESET_INDEX = {
  GROUND: 0,
  TREE: 48,
  DIRT: 36,
  WATER: 13,
};

// Building types and indices
export const building_id = {
  BASE: 0,
};

// Tile size in pixels
export const TILE_SIZE = 32;

// Layer definitions with z-indexes
export const LAYERS = {
  GROUND: {
    name: "ground",
    depth: 0,
  },
  TREES: {
    name: "trees",
    depth: 1,
  },
  BUILDINGS: {
    name: "buildings",
    depth: 2,
  },
};

// Tileset asset
export const TILESET_ASSET = {
  key: "isometric-tileset",
  url: "/images/isometric-sandbox-sheet.png",
  tileWidth: TILE_SIZE,
  tileHeight: TILE_SIZE,
};

// Building spritesheet asset
export const BUILDING_SHEET_ASSET = {
  key: "building-sheet",
  url: "/images/building-sheet.png",
  frameWidth: TILE_SIZE * 3,
  frameHeight: TILE_SIZE * 3,
};

// Turret spritesheet asset
export const TURRET_SHEET_ASSET = {
  key: "turret-sheet",
  url: "/images/turrets-sheet.png",
  frameWidth: 96,
  frameHeight: 96,
};

// Turret orientation constants
export const TURRET_ORIENTATIONS = {
  DOWN: 0,
  DOWN_LEFT: 1,
  LEFT: 2,
  UP_LEFT: 3,
  UP: 4,
  UP_RIGHT: 5,
  RIGHT: 6,
  DOWN_RIGHT: 7,
};

// Turret frame mapping: orientation -> head sprite frame (base is always 0)
export const TURRET_FRAMES = {
  BASE: 0,
  0: 1, // DOWN
  1: 2, // DOWN_LEFT
  2: 3, // LEFT
  3: 4, // UP_LEFT
  4: 5, // UP
  5: 6, // UP_RIGHT
  6: 7, // RIGHT
  7: 8, // DOWN_RIGHT
};

export default {
  TILE_EMPTY,
  TILE_TREE,
  TILESET_INDEX,
  building_id,
  TILE_SIZE,
  LAYERS,
  TILESET_ASSET,
  BUILDING_SHEET_ASSET,
  TURRET_SHEET_ASSET,
  TURRET_ORIENTATIONS,
  TURRET_FRAMES,
};
