/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path'; // Import path module
import dotenv from 'dotenv'; // Import dotenv

// Load .env.local file
dotenv.config({ path: '.env.local' });

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts', // Pointing to the setup file we'll create next
    css: true, // If your components import CSS files
  },
  resolve: { // Added resolve configuration
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
}); 