/**
 * Camera management for isometric view
 * Handles camera setup, movement, and zoom
 */

export class CameraManager {
  constructor(scene) {
    this.scene = scene;
    this.camera = scene.cameras.main;
    this.isDragging = false;
    this.dragStartX = 0;
    this.dragStartY = 0;
    this.cursors = null;
    this.cameraMoveSpeed = 10;
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
    const mapWorldWidth = width * tileSize;
    const mapWorldHeight = height * tileSize;

    // Set camera bounds to allow viewing the entire map
    this.camera.setBounds(
      -mapWorldWidth,
      -mapWorldHeight,
      mapWorldWidth * 2,
      mapWorldHeight * 2,
    );

    // Start at a reasonable zoom and pan
    this.zoomToFitMap(width, height);
    this.panToMapCenter(width, height);

    // Setup input after camera is initialized
    this.setupArrowKeys();
    this.setupMiddleClickDrag();
    this.setupZoom();
  }

  /**
   * Setup arrow key input for camera movement
   */
  setupArrowKeys() {
    if (this.scene.input.keyboard) {
      this.cursors = this.scene.input.keyboard.createCursorKeys();
    }
  }

  /**
   * Setup mouse drag for camera movement
   */
  setupMiddleClickDrag() {
    this.scene.input.on("pointerdown", (pointer) => {
      this.isDragging = true;
      this.dragStartX = pointer.x;
      this.dragStartY = pointer.y;
    });

    this.scene.input.on("pointermove", (pointer) => {
      if (this.isDragging) {
        // Scale by zoom for 1:1 feeling regardless of zoom level
        const deltaX = (this.dragStartX - pointer.x) / this.camera.zoom;
        const deltaY = (this.dragStartY - pointer.y) / this.camera.zoom;

        this.camera.scrollX += deltaX;
        this.camera.scrollY += deltaY;

        // Update drag start for next frame to get smooth incremental movement
        this.dragStartX = pointer.x;
        this.dragStartY = pointer.y;
      }
    });

    this.scene.input.on("pointerup", () => {
      this.isDragging = false;
    });
  }

  /**
   * Setup mouse wheel zoom
   */
  setupZoom() {
    this.scene.input.on("wheel", (pointer, gameObjects, deltaX, deltaY) => {
      const oldZoom = this.camera.zoom;
      const zoomAmount = deltaY > 0 ? -0.1 : 0.1;
      const newZoom = Math.max(0.5, Math.min(3.0, oldZoom + zoomAmount));

      if (newZoom === oldZoom) return;

      // Get the pointer position relative to camera center
      const centerX = this.camera.width / 2;
      const centerY = this.camera.height / 2;

      // Distance from pointer to center of screen
      const offsetX = pointer.x - centerX;
      const offsetY = pointer.y - centerY;

      // World position under cursor before zoom
      const worldX = this.camera.scrollX + offsetX / oldZoom;
      const worldY = this.camera.scrollY + offsetY / oldZoom;

      // Apply new zoom
      this.camera.setZoom(newZoom);

      // Adjust scroll so the same world point stays under cursor
      this.camera.scrollX = worldX - offsetX / newZoom;
      this.camera.scrollY = worldY - offsetY / newZoom;
    });
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
    const centerY = ((mapWidth + mapHeight) / 2) * (tileSize / 4);

    this.camera.centerOn(centerX, centerY);
  }

  /**
   * Update camera with arrow key input
   */
  update() {
    if (!this.cursors) return;

    const speed = this.cameraMoveSpeed / this.camera.zoom;

    if (this.cursors.left.isDown) {
      this.camera.scrollX -= speed;
    }
    if (this.cursors.right.isDown) {
      this.camera.scrollX += speed;
    }
    if (this.cursors.up.isDown) {
      this.camera.scrollY -= speed;
    }
    if (this.cursors.down.isDown) {
      this.camera.scrollY += speed;
    }
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
