import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy pour éviter les problèmes CORS en dev
    proxy: {
      "/predict":       "http://localhost:8000",
      "/test":          "http://localhost:8000",
      "/history":       "http://localhost:8000",
      "/analysis":      "http://localhost:8000",
      "/anomalies":     "http://localhost:8000",
    },
  },
  build: {
    outDir: process.env.VITE_BUILD_OUT_DIR || "dist",
    emptyOutDir: true,
  },
});
