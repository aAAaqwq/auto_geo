/**
 * 开发启动脚本
 * 老王我用这个来同时启动 Vite 和 Electron！
 */

const { spawn } = require('child_process')
const path = require('path')

// 获取项目根目录
const rootDir = path.join(__dirname, '..')

// 设置环境变量
process.env.ELECTRON_RENDERER_URL = 'http://localhost:5173'

let viteProcess = null
let electronProcess = null

// 清理函数
function cleanup() {
  console.log('\n🛑 正在清理进程...')
  if (viteProcess) {
    viteProcess.kill('SIGTERM')
    viteProcess = null
  }
  if (electronProcess) {
    electronProcess.kill('SIGTERM')
    electronProcess = null
  }
  setTimeout(() => process.exit(0), 500)
}

// 退出时清理
process.on('SIGINT', cleanup)
process.on('SIGTERM', cleanup)
process.on('exit', cleanup)

// 启动 Vite 开发服务器
console.log('🚀 正在启动 Vite 开发服务器...')

// 使用 npm run 来启动，跨平台最可靠
viteProcess = spawn('npm', ['run', '--silent', 'vite:dev'], {
  shell: true,
  stdio: 'inherit',
  cwd: rootDir,
  env: process.env
})

viteProcess.on('error', (err) => {
  console.error('❌ Vite 启动失败:', err.message)
  process.exit(1)
})

// Vite 启动后再启动 Electron
setTimeout(() => {
  console.log('⚡ 正在启动 Electron...')

  electronProcess = spawn('npm', ['run', '--silent', 'electron:dev'], {
    shell: true,
    stdio: 'inherit',
    cwd: rootDir,
    env: { ...process.env, ELECTRON_RENDERER_URL: 'http://localhost:5173' }
  })

  electronProcess.on('error', (err) => {
    console.error('❌ Electron 启动失败:', err.message)
    if (viteProcess) viteProcess.kill()
    process.exit(1)
  })

  electronProcess.on('close', (code) => {
    console.log(`\nElectron 退出，代码: ${code}`)
    cleanup()
  })
}, 3000)

viteProcess.on('close', (code) => {
  console.log(`\nVite 退出，代码: ${code}`)
  cleanup()
})
