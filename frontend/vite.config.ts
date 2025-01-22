import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,  // Разрешить доступ снаружи контейнера
    port: 5173,  // Порт для разработки
    watch: {
      usePolling: true,  // Использовать polling для отслеживания изменений
    },
  },
})