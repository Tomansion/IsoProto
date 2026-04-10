/**
 * Camera management for isometric view
 * Handles camera setup and isometric projection
 */

export class CameraManager {
  constructor(scene) {
    this.scene = scene;
    this.camera = scene.cameras.main;
  }

  /**
   * Set up the camera for isometric viewing
   * @param {object} mapData - Map data to determine viewport size
   */
  setupIsometricCamera(mapData) {
    if (!mapData) {
      return;
    }

    const { width, height } = mapData;
    const tileSize = 32;

    // Calculate the bounds of the map in isometric space
    // The isometric projection spreads the map, so we need extra space
    const mapWorldWidth = width * tileSize;
    const mapWorldHeight = height * tileSize;

    // Set camera bounds to allow viewing the entire map
    this.camera.setBounds(-mapWorldWidth / 2, -mapWorldHeight / 2, mapWorldWidth * 2, mapWorldHeight * 2);

    // Start at a reasonable zoom and pan
    this.zoomToFitMap(width, height);
    this.panToMapCenter(width, height);
  }

  /**
   * Zoom camera to fit the entire map in view
   * @param {number} mapWidth - Map width in tiles
   * @param {number} mapHeight - Map height in tiles
   */
  zoomToFitMap(mapWidth, mapHeight) {
    const tileSize = 32;
    const screenWidth = this.camera.width;
    const screenHeight = this.camera.height;

    // Calculate required zoom to fit map
    const mapScreenWidth = mapWidth * (tileSize / 2);
    const mapScreenHeight = mapHeight * (tileSize / 2);

    const zoomX = screenWidth / mapScreenWidth;
    const zoomY = screenHeight / mapScreenHeight;

    const zoom = Math.min(zoomX, zoomY, 1.0); // Don't zoom in, only out if needed
    this.camera.setZoom(zoom);
  }

  /**
   * Pan camera to center of map
   * @param {number} mapWidth - Map width in tiles
   * @param {number} mapHeight - Map height in tiles
   */
  panToMapCenter(mapWidth, mapHeight) {
    const tileSize = 32;
    const centerX = ((mapWidth - mapHeight) / 2) * (tileSize / 2);
    const centerY = ((mapWidth + mapHeight) / 2) * (tileSize / 2);

    this.camera.centerOn(centerX, centerY);
  }

  /**
   * Get the camera object
   * @returns {Phaser.Cameras.Scene2D.Camera} - Camera object
   */
  getCamera() {
    return this.camera;
  }

  /**
   * Reset camera to initial state
   */
  reset() {
    this.camera.setZoom(1);
    this.camera.centerOn(0, 0);
  }

  /**
   * Destroy camera manager
   */
  destroy() {
    // Camera is managed by scene, no explicit destruction needed
  }
}

export default CameraManager;
