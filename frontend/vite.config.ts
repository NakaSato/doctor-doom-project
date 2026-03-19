import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@views': path.resolve(__dirname, './src/views'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@services': path.resolve(__dirname, './src/services'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@styles': path.resolve(__dirname, './src/styles'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          maps: ['mapbox-gl', 'deck.gl'],
          charts: ['recharts', 'd3'],
          three: ['three', '@react-three/fiber', '@react-three/drei'],
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/unit/setup.ts',
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
  optimizeDeps: {
    include: ['mapbox-gl'],
  },
});
