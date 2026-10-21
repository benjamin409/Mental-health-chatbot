import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The client is built into web/dist, which the Express server serves in
// production. During development Vite runs its own server on 5173 and proxies
// /api to Express on 3000, so there is no CORS configuration to explain.
export default defineConfig({
  root: "client",
  plugins: [react()],
  build: {
    outDir: "../dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:3000",
        changeOrigin: true,
      },
    },
  },
});
