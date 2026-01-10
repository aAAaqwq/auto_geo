/**
 * 开发启动脚本
 * 老王我用这个来同时启动 Vite 和 Electron！
 */

const { spawn } = require('child_process')
const path = require('path')

// 设置环境变量
process.env.ELECTRON_RENDERER_URL = 'http://localhost:5173'

let viteProcess = null
let electronProcess = null

// 清理函数
function cleanup() {
  if (viteProcess) viteProcess.kill()
  if (electronProcess) electronProcess.kill()
}

// 退出时清理
process.on('SIGINT', cleanup)
process.on('SIGTERM', cleanup)
process.on('exit', cleanup)

// 启动 Vite 开发服务器
console.log('🚀 正在启动 Vite 开发服务器...')
viteProcess = spawn('npx', ['vite'], {
  shell: true,
  stdio: 'inherit',
  cwd: path.join(__dirname, '..'),
  env: process.env
})

viteProcess.on('error', (err) => {
  console.error('Vite 启动失败:', err)
  process.exit(1)
})

// Vite 启动后再启动 Electron
setTimeout(() => {
  console.log('⚡ 正在启动 Electron...')
  electronProcess = spawn('npx', ['electron', '.'], {
    shell: true,
    stdio: 'inherit',
    cwd: path.join(__dirname, '..'),
    env: { ...process.env, ELECTRON_RENDERER_URL: 'http://localhost:5173' }
  })

  electronProcess.on('error', (err) => {
    console.error('Electron 启动失败:', err)
    viteProcess.kill()
    process.exit(1)
  })

  electronProcess.on('close', (code) => {
    console.log(`Electron 退出，代码: ${code}`)
    cleanup()
    process.exit(code || 0)
  })
}, 3000)

viteProcess.on('close', (code) => {
  console.log(`Vite 退出，代码: ${code}`)
  cleanup()
  process.exit(code || 0)
})
