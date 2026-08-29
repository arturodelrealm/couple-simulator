import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const usePolling = process.env.VITE_USE_POLLING === "true";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    watch: usePolling
      ? {
          usePolling: true,
          interval: 1000,
        }
      : undefined,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
});
