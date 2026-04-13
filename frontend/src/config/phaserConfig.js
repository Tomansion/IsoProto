/**
 * Phaser game configuration for isometric map rendering
 */

import Phaser from "phaser";

export const phaserConfig = {
  type: Phaser.AUTO,
  parent: "game-canvas-container",
  width: "100%",
  height: "100%",
  expandParent: true,
  autoCenter: Phaser.Scale.CENTER_BOTH,
  render: {
    pixelArt: true,
    antialias: false,
  },
  physics: {
    default: "arcade",
    arcade: {
      debug: false,
      gravity: { y: 0 },
    },
  },
  scene: [],
};

export default phaserConfig;
