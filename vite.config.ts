import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  // Используем ключ из .env или запасной вариант
  const openWeatherApiKey = env.OPENWEATHER_API_KEY || "demo_key";

  return {
    plugins: [react()],
    define: {
      // Pass environment variables to browser
      'process.env.OPENWEATHER_API_KEY': JSON.stringify(openWeatherApiKey)
    }
  };
});