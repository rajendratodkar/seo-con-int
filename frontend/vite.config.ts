import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Backend runs on 127.0.0.1:8317 (SCI_BACKEND_PORT). Vite proxies /api in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8317",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
