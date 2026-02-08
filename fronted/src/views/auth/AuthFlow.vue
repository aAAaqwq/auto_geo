<template>
  <div class="auth-flow-container">
    <div class="auth-flow-header">
      <h2>AI平台授权</h2>
      <p>请完成以下平台的授权，授权后系统将自动使用这些平台进行收录查询</p>
    </div>

    <!-- 授权状态步骤 -->
    <div v-if="step === 'status'" class="auth-step">
      <h3>授权状态</h3>
      <div class="auth-status-list">
        <div 
          v-for="platform in platformStatuses" 
          :key="platform.id"
          class="platform-status-card"
          :class="platform.status"
        >
          <div class="platform-icon" :style="{ backgroundColor: platform.color + '20' }">
            <span :style="{ color: platform.color }">{{ platform.name.charAt(0) }}</span>
          </div>
          <div class="platform-info">
            <h4>{{ platform.name }}</h4>
            <p>{{ platform.url }}</p>
            <div class="status-info">
              <span class="status-badge" :class="platform.status">
                {{ getStatusText(platform.status) }}
              </span>
              <span v-if="platform.age_info" class="age-info">
                {{ getAgeText(platform.age_info) }}
              </span>
            </div>
          </div>
          <div class="platform-actions">
            <button 
              class="btn btn-primary"
              @click="reauthorizePlatform(platform.id)"
            >
              重新授权
            </button>
            <button 
              v-if="platform.status !== 'invalid'"
              class="btn btn-outline"
              @click="viewPlatformDetails(platform)"
            >
              查看详情
            </button>
          </div>
        </div>
      </div>
      <div class="auth-actions">
        <button class="btn btn-secondary" @click="refreshStatus">
          刷新状态
        </button>
        <button class="btn btn-primary" @click="startNewAuthFlow">
          开始新的授权
        </button>
      </div>
    </div>

    <!-- 平台选择步骤 -->
    <div v-else-if="step === 'platform-selection'" class="auth-step">
      <h3>选择要授权的平台</h3>
      <div class="platform-selection">
        <div 
          v-for="platform in availablePlatforms" 
          :key="platform.id"
          class="platform-card"
          :class="{ 'selected': selectedPlatforms.includes(platform.id) }"
          @click="togglePlatform(platform.id)"
        >
          <div class="platform-icon" :style="{ backgroundColor: platform.color + '20' }">
            <span :style="{ color: platform.color }">{{ platform.name.charAt(0) }}</span>
          </div>
          <div class="platform-info">
            <h4>{{ platform.name }}</h4>
            <p>{{ platform.url }}</p>
          </div>
          <div class="platform-checkbox">
            <input 
              type="checkbox" 
              :id="`platform-${platform.id}`"
              :checked="selectedPlatforms.includes(platform.id)"
              @change="togglePlatform(platform.id)"
            >
            <label :for="`platform-${platform.id}`"></label>
          </div>
        </div>
      </div>
      <div class="auth-actions">
        <button 
          class="btn btn-secondary"
          @click="backToStatus"
        >
          返回状态页
        </button>
        <button 
          class="btn btn-primary"
          :disabled="selectedPlatforms.length === 0"
          @click="startAuthFlow"
        >
          开始授权
        </button>
      </div>
    </div>

    <!-- 授权执行步骤 -->
    <div v-else-if="step === 'auth-execution'" class="auth-step">
      <h3>授权进度</h3>
      <div class="auth-progress">
        <div 
          v-for="platform in authPlatforms" 
          :key="platform.platform"
          class="platform-auth-status"
          :class="platform.status"
        >
          <div class="platform-status-header">
            <div class="platform-info">
              <div class="platform-icon" :style="{ backgroundColor: getPlatformColor(platform.platform) + '20' }">
                <span :style="{ color: getPlatformColor(platform.platform) }">{{ getPlatformName(platform.platform).charAt(0) }}</span>
              </div>
              <h4>{{ getPlatformName(platform.platform) }}</h4>
            </div>
            <div class="platform-status-badge" :class="platform.status">
              {{ getStatusText(platform.status) }}
            </div>
          </div>
          <div v-if="platform.status === 'in_progress'" class="platform-auth-details">
            <p class="auth-instruction">请在新窗口中打开以下链接，完成该平台的登录和验证：</p>
            <div class="auth-url">
              <a :href="platform.url" target="_blank" rel="noopener noreferrer">
                {{ platform.url }}
              </a>
              <button class="btn btn-sm btn-outline" @click="openAuthUrl(platform.url)">
                打开链接
              </button>
            </div>
            <p class="auth-note">完成登录后，请点击下方的"完成授权"按钮</p>
            <button class="btn btn-success" @click="completePlatformAuth(platform.platform)">
              完成授权
            </button>
          </div>
          <div v-else-if="platform.status === 'completed'" class="platform-auth-details">
            <div class="success-message">
              <span class="success-icon">✓</span>
              <p>授权成功！</p>
            </div>
          </div>
          <div v-else-if="platform.status === 'failed'" class="platform-auth-details">
            <div class="error-message">
              <span class="error-icon">✗</span>
              <p>{{ platform.error || '授权失败' }}</p>
              <button class="btn btn-outline" @click="retryPlatformAuth(platform.platform)">
                重试
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="auth-actions">
        <button 
          class="btn btn-secondary"
          @click="cancelAuthFlow"
        >
          取消
        </button>
      </div>
    </div>

    <!-- 授权完成步骤 -->
    <div v-else-if="step === 'completed'" class="auth-step">
      <div class="auth-complete">
        <div class="complete-icon">✓</div>
        <h3>授权流程完成</h3>
        <p>所有选定的平台已成功授权</p>
        <div class="completed-platforms">
          <div 
            v-for="platform in authPlatforms" 
            :key="platform.platform"
            class="completed-platform"
          >
            <div class="platform-icon" :style="{ backgroundColor: getPlatformColor(platform.platform) + '20' }">
              <span :style="{ color: getPlatformColor(platform.platform) }">{{ getPlatformName(platform.platform).charAt(0) }}</span>
            </div>
            <span>{{ getPlatformName(platform.platform) }}</span>
          </div>
        </div>
        <div class="auth-actions">
          <button class="btn btn-primary" @click="goToDashboard">
            返回首页
          </button>
          <button class="btn btn-secondary" @click="backToStatus">
            查看授权状态
          </button>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="auth-error">
      <div class="error-icon">!</div>
      <div class="error-content">
        <h4>错误</h4>
        <p>{{ error }}</p>
        <button class="btn btn-sm btn-outline" @click="clearError">
          关闭
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="auth-loading">
      <div class="loading-spinner"></div>
      <p>{{ loadingMessage || '处理中...' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { post, get } from '@/services/api'

const router = useRouter()

// 响应式数据
const step = ref('status') // status, platform-selection, auth-execution, completed
const availablePlatforms = ref([
  { id: 'doubao', name: '豆包', url: 'https://www.doubao.com', color: '#0066FF' },
  { id: 'deepseek', name: '深度求索', url: 'https://chat.deepseek.com', color: '#4D6BFE' },
  { id: 'qianwen', name: '通义千问', url: 'https://qianwen.com', color: '#FF6A00' }
])
const selectedPlatforms = ref([])
const authPlatforms = ref([])
const platformStatuses = ref([])
const authSessionId = ref('')
const loading = ref(false)
const loadingMessage = ref('')
const error = ref('')
const statusPollInterval = ref(null)
const showDetailsDialog = ref(false)
const selectedPlatform = ref(null)

// 计算属性
const hasSelectedPlatforms = computed(() => selectedPlatforms.value.length > 0)
const allPlatformsCompleted = computed(() => {
  return authPlatforms.value.every(p => 
    p.status === 'completed' || p.status === 'failed'
  )
})
const hasCompletedPlatforms = computed(() => {
  return authPlatforms.value.some(p => p.status === 'completed')
})

// 方法
const togglePlatform = (platformId) => {
  const index = selectedPlatforms.value.indexOf(platformId)
  if (index > -1) {
    selectedPlatforms.value.splice(index, 1)
  } else {
    selectedPlatforms.value.push(platformId)
  }
}

const startAuthFlow = async () => {
  if (selectedPlatforms.value.length === 0) {
    error.value = '请至少选择一个平台'
    return
  }

  loading.value = true
  loadingMessage.value = '开始授权流程...'
  error.value = ''

  try {
    // 这里应该从当前登录用户获取user_id，从路由参数或store获取project_id
    // 暂时使用固定值，实际应用中需要从上下文中获取
    const user_id = 1 // 示例值
    const project_id = 1 // 示例值

    const response = await post('/auth/start-flow', {
      user_id,
      project_id,
      platforms: selectedPlatforms.value
    })

    if (response.success) {
      authSessionId.value = response.auth_session_id
      authPlatforms.value = response.platforms.map(platform => ({
        platform,
        status: 'pending',
        url: null,
        error: null
      }))
      step.value = 'auth-execution'
      
      // 开始状态轮询
      startStatusPolling()
      
      // 开始第一个平台的授权
      if (authPlatforms.value.length > 0) {
        await startPlatformAuth(authPlatforms.value[0].platform)
      }
    } else {
      error.value = response.error || '开始授权流程失败'
    }
  } catch (err) {
    error.value = `请求失败: ${err.message || '未知错误'}`
  } finally {
    loading.value = false
    loadingMessage.value = ''
  }
}

const startPlatformAuth = async (platform) => {
  loading.value = true
  loadingMessage.value = `正在启动${getPlatformName(platform)}授权...`

  try {
    const response = await post(`/auth/start-platform/${authSessionId.value}?platform=${encodeURIComponent(platform)}`)

    if (response.success) {
      // 更新平台状态
      const platformIndex = authPlatforms.value.findIndex(p => p.platform === platform)
      if (platformIndex > -1) {
        authPlatforms.value[platformIndex].status = 'in_progress'
        authPlatforms.value[platformIndex].url = response.auth_url
      }
    } else {
      // 更新平台状态为失败
      const platformIndex = authPlatforms.value.findIndex(p => p.platform === platform)
      if (platformIndex > -1) {
        authPlatforms.value[platformIndex].status = 'failed'
        authPlatforms.value[platformIndex].error = response.error || '授权启动失败'
      }
      error.value = response.error || '启动平台授权失败'
    }
  } catch (err) {
    // 更新平台状态为失败
    const platformIndex = authPlatforms.value.findIndex(p => p.platform === platform)
    if (platformIndex > -1) {
      authPlatforms.value[platformIndex].status = 'failed'
      authPlatforms.value[platformIndex].error = err.message || '网络错误'
    }
    error.value = `请求失败: ${err.message || '未知错误'}`
  } finally {
    loading.value = false
    loadingMessage.value = ''
  }
}

const completePlatformAuth = async (platform) => {
  loading.value = true
  loadingMessage.value = `正在完成${getPlatformName(platform)}授权...`

  try {
    const response = await post(`/auth/complete-platform/${authSessionId.value}?platform=${encodeURIComponent(platform)}`)

    if (response.success) {
      // 更新平台状态
      const platformIndex = authPlatforms.value.findIndex(p => p.platform === platform)
      if (platformIndex > -1) {
        authPlatforms.value[platformIndex].status = 'completed'
        authPlatforms.value[platformIndex].error = null
      }

      // 检查是否所有平台都已完成
      if (allPlatformsCompleted.value) {
        // 停止状态轮询
        stopStatusPolling()
        step.value = 'completed'
      } else {
        // 开始下一个平台的授权
        const nextPlatform = authPlatforms.value.find(p => p.status === 'pending')
        if (nextPlatform) {
          await startPlatformAuth(nextPlatform.platform)
        }
      }
    } else {
      error.value = response.error || '完成平台授权失败'
    }
  } catch (err) {
    error.value = `请求失败: ${err.message || '未知错误'}`
  } finally {
    loading.value = false
    loadingMessage.value = ''
  }
}

const retryPlatformAuth = async (platform) => {
  // 更新平台状态为待授权
  const platformIndex = authPlatforms.value.findIndex(p => p.platform === platform)
  if (platformIndex > -1) {
    authPlatforms.value[platformIndex].status = 'pending'
    authPlatforms.value[platformIndex].error = null
  }

  // 重新开始该平台的授权
  await startPlatformAuth(platform)
}

const cancelAuthFlow = async () => {
  if (!authSessionId.value) {
    step.value = 'platform-selection'
    return
  }

  loading.value = true
  loadingMessage.value = '取消授权流程...'

  try {
    await post(`/auth/cancel/${authSessionId.value}`)
    stopStatusPolling()
    step.value = 'platform-selection'
  } catch (err) {
    error.value = `取消失败: ${err.message || '未知错误'}`
  } finally {
    loading.value = false
    loadingMessage.value = ''
  }
}

const startStatusPolling = () => {
  // 每3秒轮询一次状态
  statusPollInterval.value = setInterval(async () => {
    try {
      const response = await get(`/auth/status/${authSessionId.value}`)
      if (response.success && response.status) {
        // 更新平台状态
        const newStatus = response.status
        if (newStatus.platforms) {
          authPlatforms.value = newStatus.platforms
        }
      }
    } catch (err) {
      console.error('状态轮询失败:', err)
    }
  }, 3000)
}

const stopStatusPolling = () => {
  if (statusPollInterval.value) {
    clearInterval(statusPollInterval.value)
    statusPollInterval.value = null
  }
}

const openAuthUrl = (url) => {
  window.open(url, '_blank', 'width=1024,height=768')
}

const getPlatformName = (platformId) => {
  const platform = availablePlatforms.value.find(p => p.id === platformId)
  return platform ? platform.name : platformId
}

const getPlatformColor = (platformId) => {
  const platform = availablePlatforms.value.find(p => p.id === platformId)
  return platform ? platform.color : '#333333'
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': '待授权',
    'in_progress': '进行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消',
    'valid': '已授权',
    'expiring': '即将过期',
    'invalid': '未授权',
    'error': '错误'
  }
  return statusMap[status] || status
}

const clearError = () => {
  error.value = ''
}

const goToDashboard = () => {
  router.push('/dashboard')
}

const restartAuthFlow = () => {
  step.value = 'platform-selection'
  selectedPlatforms.value = []
  authPlatforms.value = []
  authSessionId.value = ''
  error.value = ''
}

// 授权状态相关方法
const loadPlatformStatuses = async () => {
  loading.value = true
  loadingMessage.value = '加载平台授权状态...'
  error.value = ''

  try {
    // 这里应该从当前登录用户获取user_id，从路由参数或store获取project_id
    // 暂时使用固定值，实际应用中需要从上下文中获取
    const user_id = 1 // 示例值
    const project_id = 1 // 示例值

    // 获取所有会话状态
    const response = await get('/auth/sessions', { user_id, project_id })

    if (response.success) {
      const sessions = response.data.sessions || []
      const sessionMap = {}

      // 构建会话映射
      sessions.forEach(session => {
        sessionMap[session.platform] = session
      })

      // 构建平台状态列表
      const statuses = availablePlatforms.value.map(platform => {
        const session = sessionMap[platform.id]
        return {
          ...platform,
          status: session ? 'valid' : 'invalid',
          age_info: session?.age_info
        }
      })

      // 对每个平台执行状态检查
      for (const status of statuses) {
        try {
          const statusResponse = await get('/auth/session/status', {
            user_id,
            project_id,
            platform: status.id
          })
          if (statusResponse.success) {
            status.status = statusResponse.data.status
            status.age_info = statusResponse.data.age_info
          }
        } catch (err) {
          console.error(`获取${status.name}状态失败:`, err)
        }
      }

      platformStatuses.value = statuses
    } else {
      error.value = response.error || '加载平台状态失败'
    }
  } catch (err) {
    error.value = `请求失败: ${err.message || '未知错误'}`
  } finally {
    loading.value = false
    loadingMessage.value = ''
  }
}

const getAgeText = (ageInfo) => {
  if (ageInfo.age_days) {
    return `${ageInfo.age_days}天前授权`
  } else if (ageInfo.age_hours) {
    return `${ageInfo.age_hours}小时前授权`
  } else {
    return '刚刚授权'
  }
}

const refreshStatus = () => {
  loadPlatformStatuses()
}

const startNewAuthFlow = () => {
  step.value = 'platform-selection'
}

const reauthorizePlatform = (platformId) => {
  // 导航到平台选择页面，并选择该平台
  selectedPlatforms.value = [platformId]
  step.value = 'platform-selection'
}

const viewPlatformDetails = (platform) => {
  selectedPlatform.value = platform
  showDetailsDialog.value = true
}

const backToStatus = () => {
  step.value = 'status'
  loadPlatformStatuses()
}

// 生命周期钩子
onMounted(() => {
  // 组件挂载时加载平台状态
  loadPlatformStatuses()
})

onBeforeUnmount(() => {
  // 组件卸载前清理
  stopStatusPolling()
})
</script>

<style scoped>
.auth-flow-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.auth-flow-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-flow-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.auth-flow-header p {
  font-size: 14px;
  color: #666;
}

.auth-step {
  margin-bottom: 32px;
}

.auth-step h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

/* 平台选择样式 */
.platform-selection {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.platform-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.platform-card:hover {
  border-color: #0066FF;
  box-shadow: 0 2px 8px rgba(0, 102, 255, 0.1);
}

.platform-card.selected {
  border-color: #0066FF;
  background-color: #f0f7ff;
}

.platform-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.platform-icon span {
  font-size: 20px;
  font-weight: 600;
}

.platform-info {
  flex: 1;
}

.platform-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.platform-info p {
  font-size: 12px;
  color: #666;
  margin: 0;
}

.platform-checkbox {
  position: relative;
}

.platform-checkbox input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

.platform-checkbox label {
  display: block;
  width: 20px;
  height: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 4px;
  position: relative;
  cursor: pointer;
}

.platform-checkbox input:checked + label {
  background-color: #0066FF;
  border-color: #0066FF;
}

.platform-checkbox input:checked + label::after {
  content: '';
  position: absolute;
  left: 6px;
  top: 2px;
  width: 6px;
  height: 12px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* 授权进度样式 */
.auth-progress {
  margin-bottom: 24px;
}

.platform-auth-status {
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.platform-auth-status.in_progress {
  border-left: 4px solid #4D6BFE;
  background-color: #f8f9ff;
}

.platform-auth-status.completed {
  border-left: 4px solid #28a745;
  background-color: #f8fff9;
}

.platform-auth-status.failed {
  border-left: 4px solid #dc3545;
  background-color: #fff8f8;
}

.platform-status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.platform-status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.platform-status-badge.pending {
  background-color: #ffc107;
  color: #212529;
}

.platform-status-badge.in_progress {
  background-color: #4D6BFE;
  color: #fff;
}

.platform-status-badge.completed {
  background-color: #28a745;
  color: #fff;
}

.platform-status-badge.failed {
  background-color: #dc3545;
  color: #fff;
}

.platform-auth-details {
  margin-top: 12px;
}

.auth-instruction {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.auth-url {
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  word-break: break-all;
}

.auth-url a {
  color: #0066FF;
  text-decoration: none;
}

.auth-url a:hover {
  text-decoration: underline;
}

.auth-url button {
  margin-top: 8px;
}

.auth-note {
  font-size: 12px;
  color: #999;
  margin-bottom: 16px;
}

.success-message {
  display: flex;
  align-items: center;
  color: #28a745;
}

.success-icon {
  font-size: 20px;
  font-weight: 600;
  margin-right: 8px;
}

.error-message {
  display: flex;
  flex-direction: column;
  color: #dc3545;
}

.error-icon {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

/* 授权完成样式 */
.auth-complete {
  text-align: center;
  padding: 40px 20px;
}

.complete-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: #28a745;
  color: #fff;
  font-size: 32px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.auth-complete h3 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.auth-complete p {
  font-size: 14px;
  color: #666;
  margin-bottom: 24px;
}

.completed-platforms {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px;
  margin-bottom: 32px;
}

.completed-platform {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background-color: #f8f9fa;
  border-radius: 20px;
  font-size: 14px;
}

.completed-platform .platform-icon {
  width: 32px;
  height: 32px;
  margin-right: 8px;
}

.completed-platform .platform-icon span {
  font-size: 14px;
}

/* 操作按钮样式 */
.auth-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background-color: #0066FF;
  color: #fff;
}

.btn-primary:hover {
  background-color: #0052cc;
}

.btn-primary:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #f8f9fa;
  color: #333;
  border: 1px solid #e0e0e0;
}

.btn-secondary:hover {
  background-color: #e9ecef;
}

.btn-success {
  background-color: #28a745;
  color: #fff;
}

.btn-success:hover {
  background-color: #218838;
}

.btn-outline {
  background-color: transparent;
  color: #0066FF;
  border: 1px solid #0066FF;
}

.btn-outline:hover {
  background-color: #0066FF;
  color: #fff;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* 错误提示样式 */
.auth-error {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  background-color: #fff8f8;
  border: 1px solid #dc3545;
  border-radius: 4px;
  margin-bottom: 20px;
}

.auth-error .error-icon {
  font-size: 18px;
  font-weight: 600;
  color: #dc3545;
  margin-right: 12px;
  flex-shrink: 0;
}

.auth-error .error-content {
  flex: 1;
}

.auth-error h4 {
  font-size: 14px;
  font-weight: 600;
  color: #dc3545;
  margin-bottom: 4px;
}

.auth-error p {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

/* 加载状态样式 */
.auth-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #0066FF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.auth-loading p {
  font-size: 14px;
  color: #666;
}

/* 授权状态样式 */
.auth-status-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.platform-status-card {
  display: flex;
  align-items: flex-start;
  padding: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.platform-status-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.platform-status-card.valid {
  border-color: #28a745;
  background-color: #f8fff9;
}

.platform-status-card.expiring {
  border-color: #ffc107;
  background-color: #fffbf0;
}

.platform-status-card.invalid {
  border-color: #dc3545;
  background-color: #fff8f8;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.age-info {
  font-size: 12px;
  color: #666;
}

.platform-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.platform-details {
  padding: 20px 0;
}

.detail-item {
  display: flex;
  margin-bottom: 16px;
}

.detail-item .label {
  width: 120px;
  font-weight: 500;
  color: #666;
}

.detail-item .value {
  flex: 1;
  color: #333;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .auth-flow-container {
    padding: 16px;
    margin: 16px;
  }

  .platform-selection {
    grid-template-columns: 1fr;
  }

  .auth-status-list {
    grid-template-columns: 1fr;
  }

  .platform-status-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .platform-icon {
    margin-bottom: 12px;
  }

  .platform-info {
    margin-bottom: 16px;
  }

  .platform-actions {
    width: 100%;
    flex-direction: row;
  }

  .platform-actions .btn {
    flex: 1;
  }

  .auth-actions {
    flex-direction: column;
  }

  .auth-actions .btn {
    width: 100%;
  }
}
</style>
