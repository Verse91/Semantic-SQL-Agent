import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [react()],
    // API 基础 URL
    define: {
      'process.env.API_BASE': JSON.stringify(env.VITE_API_BASE || 'http://localhost:8001')
    },
    // 开发服务器配置
    server: {
      port: 3000,
      host: true
    },
    // 构建优化
    build: {
      outDir: 'dist',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'antd'],
            utils: ['axios']
          }
        }
      }
    }
  }
})
