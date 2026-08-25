import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxies /api/* requests to the FastAPI backend during local development,
// so the frontend never needs to hardcode a full backend URL or deal
// with CORS while running `npm run dev`.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
}); 