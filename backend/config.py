"""Configuration constants for the game."""

# Map generation
MAP_SIZE = 100
MAP_CENTER = MAP_SIZE // 2
BASE_RADIUS = 5  # Clear area around the base

# Perlin noise parameters
PERLIN_SCALE = 50.0  # Lower values = larger features
PERLIN_FREQUENCY = 1.0
PERLIN_OCTAVES = 3
PERLIN_PERSISTENCE = 0.65
PERLIN_LACUNARITY = 2.0
PERLIN_TREE_THRESHOLD = 0.4  # Noise value above this = tree

# Tile types
TILE_EMPTY = 0
TILE_TREE = 1
