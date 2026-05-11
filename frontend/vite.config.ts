import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendTarget = process.env.VITE_BACKEND_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,  // Bind to 0.0.0.0 — required for Docker dev
    proxy: {
      "/api": backendTarget,
      "/admin": backendTarget,
      "/media": backendTarget,
    },
  },
});
