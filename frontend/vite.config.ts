import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      react: 'react',
      'react-dom': 'react-dom',
    },
    dedupe: ['react', 'react-dom'],
  },
  optimizeDeps: {},

  // Reduce large bundle warnings by improving vendor/common chunking.
  // This helps keep JS bundles smaller and speeds up initial load.
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id) return undefined;

          // Split React into its own chunk
          if (id.includes('node_modules/react')) return 'react-vendor';
          if (id.includes('node_modules/react-dom')) return 'react-dom-vendor';

          // Split MUI into its own chunk (often large)
          if (id.includes('node_modules/@mui')) return 'mui-vendor';

          // Split React Router / React Query together
          if (id.includes('node_modules/@tanstack')) return 'tanstack-vendor';
          if (id.includes('node_modules/react-router-dom')) return 'router-vendor';

          // Generic vendor split
          if (id.includes('node_modules')) return 'vendor';

          return undefined;
        },
      },
    },
  },
})


