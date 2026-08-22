import { defineConfig } from "vitest/config";
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
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "text-summary", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/test-setup.ts",
        "src/**/*.test.{ts,tsx}",
        "src/**/*.d.ts",
        "src/types/**",
      ],
    },
  },
});
