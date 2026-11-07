import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'

// mode "static" : un seul fichier HTML autonome avec les résultats intégrés (démo sans serveur)
export default defineConfig(({ mode }) => ({
  plugins: mode === 'static' ? [react(), viteSingleFile()] : [react()],
  build: { outDir: mode === 'static' ? 'dist-static' : 'dist', chunkSizeWarningLimit: 3000 },
  server: { proxy: { '/api': 'http://localhost:8000' } },
}))
