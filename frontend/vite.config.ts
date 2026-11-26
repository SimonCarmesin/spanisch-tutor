/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// Das Backend läuft lokal auf Port 8000. Der Proxy macht /api und /health für den Browser
// zur selben Origin wie das Frontend: kein CORS nötig, und ein Handy im WLAN muss nur
// den Vite-Server erreichen (npm run dev:phone).
const backend = process.env.BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "Spanisch-Tutor",
        short_name: "Tutor",
        description: "Spanisch sprechen lernen im Gespräch",
        lang: "de",
        start_url: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#f4f8fd",
        theme_color: "#f4f8fd",
        icons: [
          { src: "icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icons/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        // Die App-Hülle kommt aus dem Cache, API-Aufrufe nie: Antworten des Tutors sind live
        navigateFallbackDenylist: [/^\/api/, /^\/health/],
      },
    }),
  ],
  server: {
    proxy: {
      "/api": backend,
      "/health": backend,
    },
  },
  test: {
    environment: "jsdom",
  },
});
