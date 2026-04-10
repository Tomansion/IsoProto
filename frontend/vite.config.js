module.exports = (async () => {
  const { defineConfig } = await import("vite");
  const vue = (await import("@vitejs/plugin-vue")).default;

  return defineConfig({
    plugins: [vue()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
        },
        "/ws": {
          target: "ws://localhost:8000",
          ws: true,
        },
      },
    },
    build: {
      outDir: "dist",
    },
  });
})();
