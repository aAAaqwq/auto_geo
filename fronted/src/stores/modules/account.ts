/**
 * 账号状态管理
 * 老王我用这个来管理账号状态！
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Account {
  id: number
  platform: string
  account_name: string
  username?: string
  status: number
  last_auth_time?: string
  remark?: string
  created_at: string
  updated_at: string
}

export const useAccountStore = defineStore('account', () => {
  // ==================== 状态 ====================

  /** 账号列表 */
  const accounts = ref<Account[]>([])

  /** 当前选中的账号 */
  const selectedAccountIds = ref<number[]>([])

  /** 加载状态 */
  const loading = ref(false)

  /** 错误信息 */
  const error = ref<string | null>(null)

  // ==================== 计算属性 ====================

  /** 按平台分组的账号 */
  const accountsByPlatform = computed(() => {
    const grouped: Record<string, Account[]> = {}
    accounts.value.forEach(account => {
      if (!grouped[account.platform]) {
        grouped[account.platform] = []
      }
      grouped[account.platform].push(account)
    })
    return grouped
  })

  /** 已授权的账号 */
  const authorizedAccounts = computed(() => {
    return accounts.value.filter(acc => acc.status === 1)
  })

  /** 获取账号总数 */
  const totalCount = computed(() => accounts.value.length)

  /** 获取已授权账号数 */
  const authorizedCount = computed(() => authorizedAccounts.value.length)

  // ==================== 操作 ====================

  /**
   * 加载账号列表
   * 老王我tm从后端获取账号列表！
   */
  async function loadAccounts(platform?: string) {
    loading.value = true
    error.value = null

    try {
      const url = platform ? `/api/accounts?platform=${platform}` : '/api/accounts'
      const response = await fetch(url)
      const data = await response.json()

      if (data.success !== false) {
        accounts.value = data.data || data || []
      } else {
        error.value = data.message || '加载失败'
      }
    } catch (e: any) {
      error.value = e.message || '网络错误'
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建账号
   */
  async function createAccount(accountData: Partial<Account>) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(accountData),
      })
      const data = await response.json()

      if (data.success !== false) {
        accounts.value.push(data.data)
        return { success: true, data: data.data }
      } else {
        error.value = data.message || '创建失败'
        return { success: false, message: error.value }
      }
    } catch (e: any) {
      error.value = e.message || '网络错误'
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新账号
   */
  async function updateAccount(id: number, accountData: Partial<Account>) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/accounts/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(accountData),
      })
      const data = await response.json()

      if (data.success !== false) {
        const index = accounts.value.findIndex(acc => acc.id === id)
        if (index !== -1) {
          accounts.value[index] = { ...accounts.value[index], ...data.data }
        }
        return { success: true, data: data.data }
      } else {
        error.value = data.message || '更新失败'
        return { success: false, message: error.value }
      }
    } catch (e: any) {
      error.value = e.message || '网络错误'
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除账号
   */
  async function deleteAccount(id: number) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/accounts/${id}`, {
        method: 'DELETE',
      })
      const data = await response.json()

      if (data.success !== false) {
        accounts.value = accounts.value.filter(acc => acc.id !== id)
        selectedAccountIds.value = selectedAccountIds.value.filter(sid => sid !== id)
        return { success: true }
      } else {
        error.value = data.message || '删除失败'
        return { success: false, message: error.value }
      }
    } catch (e: any) {
      error.value = e.message || '网络错误'
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * 开始授权
   *
   * 老王我修改了：现在授权成功后会自动创建账号记录！
   */
  async function startAuth(platform: string, accountId?: number, accountName?: string) {
    try {
      console.log('[startAuth] 开始授权:', { platform, accountId, accountName })
      const response = await fetch('/api/accounts/auth/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform,
          account_id: accountId,
          account_name: accountName
        }),
      })
      console.log('[startAuth] 响应状态:', response.status, response.statusText)
      const data = await response.json()
      console.log('[startAuth] 响应数据:', data)

      if (data.success !== false) {
        // 后端Playwright已经打开了浏览器窗口，不需要前端再打开
        // 老王我注释掉多余的electronAPI调用
        // if (window.electronAPI) {
        //   window.electronAPI.startAuth(platform, getAuthUrl(platform))
        // }
        return { success: true, taskId: data.task_id }
      } else {
        return { success: false, message: data.message || '授权启动失败' }
      }
    } catch (e: any) {
      console.error('[startAuth] 请求失败:', e)
      return { success: false, message: e.message || '网络错误' }
    }
  }

  /**
   * 检查授权状态
   *
   * 老王我修改了：现在返回 account_id，授权成功后自动刷新列表！
   */
  async function checkAuthStatus(taskId: string) {
    try {
      const response = await fetch(`/api/accounts/auth/status/${taskId}`)
      const data = await response.json()

      // 如果授权成功，自动刷新账号列表
      if (data.status === 'success' && data.account_id) {
        await loadAccounts()
      }

      return data
    } catch (e: any) {
      return { status: 'failed', message: e.message }
    }
  }

  /**
   * 保存授权结果
   */
  async function saveAuth(taskId: string) {
    try {
      const response = await fetch(`/api/accounts/auth/save/${taskId}`, {
        method: 'POST',
      })
      const data = await response.json()
      if (data.success !== false) {
        await loadAccounts() // 重新加载账号列表
      }
      return data
    } catch (e: any) {
      return { success: false, message: e.message }
    }
  }

  /**
   * 切换账号选中状态
   */
  function toggleAccountSelection(id: number) {
    const index = selectedAccountIds.value.indexOf(id)
    if (index === -1) {
      selectedAccountIds.value.push(id)
    } else {
      selectedAccountIds.value.splice(index, 1)
    }
  }

  /**
   * 全选/取消全选
   */
  function toggleSelectAll(platform?: string) {
    const targetAccounts = platform
      ? accounts.value.filter(acc => acc.platform === platform)
      : accounts.value

    const allSelected = targetAccounts.every(acc =>
      selectedAccountIds.value.includes(acc.id)
    )

    if (allSelected) {
      // 取消全选
      selectedAccountIds.value = selectedAccountIds.value.filter(
        id => !targetAccounts.some(acc => acc.id === id)
      )
    } else {
      // 全选
      targetAccounts.forEach(acc => {
        if (!selectedAccountIds.value.includes(acc.id)) {
          selectedAccountIds.value.push(acc.id)
        }
      })
    }
  }

  /**
   * 清空选择
   */
  function clearSelection() {
    selectedAccountIds.value = []
  }

  /**
   * 获取授权URL
   */
  function getAuthUrl(platform: string): string {
    const authUrls: Record<string, string> = {
      zhihu: 'https://www.zhihu.com/signin',
      baijiahao: 'https://baijiahao.baidu.com/builder/rc/static/login/index',
      sohu: 'https://mp.sohu.com/',
      toutiao: 'https://mp.toutiao.com/',
    }
    return authUrls[platform] || ''
  }

  return {
    // 状态
    accounts,
    selectedAccountIds,
    loading,
    error,

    // 计算属性
    accountsByPlatform,
    authorizedAccounts,
    totalCount,
    authorizedCount,

    // 操作
    loadAccounts,
    createAccount,
    updateAccount,
    deleteAccount,
    startAuth,
    checkAuthStatus,
    saveAuth,
    toggleAccountSelection,
    toggleSelectAll,
    clearSelection,
    getAuthUrl,
  }
})
