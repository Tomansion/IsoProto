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

export default {
  TILE_EMPTY,
  TILE_TREE,
  TILESET_INDEX,
  building_id,
  TILE_SIZE,
  LAYERS,
  TILESET_ASSET,
  BUILDING_SHEET_ASSET,
};
