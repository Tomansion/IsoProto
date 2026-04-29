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
PERLIN_TREE_THRESHOLD = 0.6  # Noise value above this = tree

# Elevation parameters (separate Perlin noise for terrain height)
ELEVATION_SCALE = 100.0  # Lower values = larger elevation features
ELEVATION_OCTAVES = 6
ELEVATION_PERSISTENCE = 0.5
ELEVATION_LACUNARITY = 1.0
ELEVATION_MIN = 0  # Minimum elevation
ELEVATION_MAX = 50  # Maximum elevation

# Tile types
TILE_EMPTY = 0
TILE_TREE = 1

# Mob spawning configuration
MOB_SPAWN_CONFIG = {
    "initial_wave_size": 10,      # Number of mobs in the first wave
    "wave_increment": 5,           # Additional mobs per subsequent wave
    "wave_delay_ticks": 100,       # Game ticks between spawning waves (0.1s per tick)
    "spawn_rate_ticks": 5,         # Game ticks between spawning individual mobs in a sequence
    "max_mobs": 200,               # Maximum concurrent mobs on the map
    "border_distance": 2,          # Distance from map edge where mobs spawn
    "spawn_spread": 5,             # Random offset along the edge for each mob (±N)
    "total_waves": 20,             # Total number of waves to spawn
}
