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
  frameWidth: 32*5,
  frameHeight: 32*5,
};


// Turret frame mapping: orientation -> head sprite frame (base is always 0)
export const TURRET_FRAMES = {
  BASE: 0,
  0: 8, // DOWN
  1: 1, // DOWN_LEFT
  2: 2, // LEFT
  3: 3, // UP_LEFT
  4: 4, // UP
  5: 5, // UP_RIGHT
  6: 6, // RIGHT
  7: 7, // DOWN_RIGHT
};

// Turret shot fire effect frames: orientation -> shot sprite frame (second row)
// Each orientation has a matching shot effect frame
export const TURRET_SHOT_FRAMES = {
  0: 9,  // DOWN
  1: 10, // DOWN_LEFT
  2: 11, // LEFT
  3: 12, // UP_LEFT
  4: 13, // UP
  5: 14, // UP_RIGHT
  6: 15, // RIGHT
  7: 16, // DOWN_RIGHT
};

// Zombie (mob) spritesheet asset — 6 frames, left-to-right walk animation
export const ZOMBIE_ASSET = {
  key: "zombie",
  url: "/images/entities/zombie.png",
  frameWidth: 32,
  frameHeight: 32,
};

export const ZOMBIE_ANIM_FRAMERATE = 8;

// Explosion spritesheet asset — 10 frames of 96x96px explosion animation
export const EXPLOSION_ASSET = {
  key: "explosion",
  url: "/images/explosion-sheet.png",
  frameWidth: 96,
  frameHeight: 96,
};

export const EXPLOSION_ANIM_FRAMERATE = 12;

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
  TURRET_FRAMES,
  TURRET_SHOT_FRAMES,
  ZOMBIE_ASSET,
  ZOMBIE_ANIM_FRAMERATE,
  EXPLOSION_ASSET,
  EXPLOSION_ANIM_FRAMERATE,
};
