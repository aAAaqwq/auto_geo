/**
 * Vite 类型声明
 */

/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

/**
 * Electron API 类型声明
 */
interface ElectronAPI {
  getAppInfo(): Promise<{
    name: string
    version: string
    platform: string
    arch: string
  }>
  getVersion(): Promise<string>
  minimizeWindow(): void
  maximizeWindow(): void
  closeWindow(): void
  openExternal(url: string): Promise<void>
  openFile(options: any): Promise<any>
  saveFile(options: any): Promise<any>
  startAuth(platformId: string, authUrl: string): void
  showNotification(title: string, body: string): void
  onAuthWindowClosed(callback: (data: any) => void): () => void
  onPublishProgress(callback: (data: any) => void): () => void
  platforms: Record<string, { id: string; name: string; color: string }>
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI
  }
}

export {}
