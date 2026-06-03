import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The SPA is served by FastAPI from `frontend/dist` at the site root.
// During local development, `npm run dev` proxies API calls to uvicorn so the
// React dev server (5173) and the FastAPI app (8000) behave like one origin.
export default defineConfig({
  plugins: [react()],
  base: "/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://127.0.0.1:8000",
      "/graph-admin": "http://127.0.0.1:8000",
      "/analyze-ticket": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
});
