/**
 * 开发启动脚本
 * 老王我用这个来同时启动 Vite 和 Electron！
 *
 * 修复说明：
 * - 改用 npm bin 路径直接调用，避免 npx 在某些环境下找不到依赖
 * - 添加更详细的错误提示
 */

const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')

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

// 检查依赖是否安装
function checkDependencies() {
  const nodeModulesPath = path.join(rootDir, 'node_modules')
  if (!fs.existsSync(nodeModulesPath)) {
    console.error('❌ 错误: node_modules 目录不存在！')
    console.error('请先运行: npm install')
    process.exit(1)
  }

  const vitePath = path.join(rootDir, 'node_modules', '.bin', 'vite')
  const electronPath = path.join(rootDir, 'node_modules', '.bin', 'electron')

  if (!fs.existsSync(vitePath + (process.platform === 'win32' ? '.cmd' : ''))) {
    console.error('❌ 错误: vite 未正确安装！')
    console.error('请先运行: npm install')
    process.exit(1)
  }

  if (!fs.existsSync(electronPath + (process.platform === 'win32' ? '.cmd' : ''))) {
    console.error('❌ 错误: electron 未正确安装！')
    console.error('请先运行: npm install')
    process.exit(1)
  }
}

// 检查依赖
checkDependencies()

// 获取可执行文件路径
function getBinPath(pkgName) {
  const binDir = path.join(rootDir, 'node_modules', '.bin')
  const ext = process.platform === 'win32' ? '.cmd' : ''
  return path.join(binDir, pkgName + ext)
}

// 启动 Vite 开发服务器
console.log('🚀 正在启动 Vite 开发服务器...')

const viteBin = getBinPath('vite')
viteProcess = spawn(viteBin, [], {
  shell: false,
  stdio: 'inherit',
  cwd: rootDir,
  env: process.env
})

viteProcess.on('error', (err) => {
  console.error('❌ Vite 启动失败:', err.message)
  console.error('请确保已运行: npm install')
  process.exit(1)
})

// Vite 启动后再启动 Electron
setTimeout(() => {
  console.log('⚡ 正在启动 Electron...')

  const electronBin = getBinPath('electron')
  electronProcess = spawn(electronBin, ['.'], {
    shell: false,
    stdio: 'inherit',
    cwd: rootDir,
    env: { ...process.env, ELECTRON_RENDERER_URL: 'http://localhost:5173' }
  })

  electronProcess.on('error', (err) => {
    console.error('❌ Electron 启动失败:', err.message)
    console.error('请确保已运行: npm install')
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
