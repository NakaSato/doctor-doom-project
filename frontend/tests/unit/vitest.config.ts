import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './setup.ts',
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/setupTests.ts'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../src'),
      '@components': path.resolve(__dirname, '../src/components'),
      '@views': path.resolve(__dirname, '../src/views'),
      '@hooks': path.resolve(__dirname, '../src/hooks'),
      '@stores': path.resolve(__dirname, '../src/stores'),
      '@services': path.resolve(__dirname, '../src/services'),
      '@types': path.resolve(__dirname, '../src/types'),
      '@utils': path.resolve(__dirname, '../src/utils'),
      '@styles': path.resolve(__dirname, '../src/styles'),
    },
  },
});
