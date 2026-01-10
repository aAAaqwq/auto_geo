/**
 * AutoGeo Electron 主进程入口
 * 老王我用这个来管理整个桌面应用！
 */

import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import * as windowManager from './window-manager'
import * as ipcHandlers from './ipc-handlers'
import * as trayManager from './tray-manager'
import * as backendManager from './backend-manager'
import { setAppQuitting } from './backend-manager'

// 老王提示：禁用硬件加速，避免一些SB兼容性问题
app.disableHardwareAcceleration()

let mainWindow: BrowserWindow | null = null

// ==================== 应用生命周期 ====================

app.whenReady().then(async () => {
  // 老王修改：不再自动启动后端，由用户手动启动！
  // console.log('[App] 正在启动 Python 后端...')
  // await backendManager.backendManager.start()

  // 设置应用用户模型ID（Windows通知用）
  electronApp.setAppUserModelId('com.autogeo.app')

  // 注册IPC处理器
  ipcHandlers.registerHandlers()

  // 创建主窗口
  mainWindow = windowManager.createMainWindow()

  // 创建系统托盘
  trayManager.createTray(mainWindow)

  // 快捷键和优化
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  app.on('activate', function () {
    // macOS: 点击 Dock 图标时重新创建窗口
    if (BrowserWindow.getAllWindows().length === 0) mainWindow = windowManager.createMainWindow()
  })
})

// ==================== 窗口全部关闭时 ====================

app.on('window-all-closed', () => {
  // 老王提示：macOS 除非用户用 Cmd + Q 明确退出，否则应用保持运行
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// ==================== 应用退出前 ====================

app.on('before-quit', () => {
  // 设置退出标志
  setAppQuitting()
  // 清理资源
  trayManager.destroyTray()
  // 老王修改：不再自动停止后端，由用户手动管理！
  // 如果将来需要自动管理，可以在这里调用
  // backendManager.backendManager.stop()
})

// ==================== 导出 ====================

export { mainWindow }
