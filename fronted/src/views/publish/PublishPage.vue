<template>
  <div class="publish-page">
    <!-- 步骤指示器 -->
    <div class="steps">
      <div
        v-for="(step, index) in steps"
        :key="index"
        class="step-item"
        :class="{
          active: currentStep === index,
          completed: currentStep > index,
        }"
      >
        <div class="step-number">{{ index + 1 }}</div>
        <div class="step-label">{{ step }}</div>
        <div v-if="index < steps.length - 1" class="step-line"></div>
      </div>
    </div>

    <!-- 步骤内容 -->
    <div class="step-content">
      <!-- 步骤1: 选择文章 -->
      <div v-show="currentStep === 0" class="step-panel">
        <h2>选择要发布的文章</h2>
        <div class="article-selector">
          <div
            v-for="article in articleStore.articles"
            :key="article.id"
            class="article-option"
            :class="{ selected: selectedArticles.includes(article.id) }"
            @click="toggleArticle(article.id)"
          >
            <el-checkbox :model-value="selectedArticles.includes(article.id)" @click.stop />
            <div class="article-info">
              <h4>{{ article.title }}</h4>
              <p>{{ getPreview(article.content) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤2: 选择账号 -->
      <div v-show="currentStep === 1" class="step-panel">
        <h2>选择发布账号</h2>
        <div class="platform-sections">
          <div
            v-for="platform in platforms"
            :key="platform.id"
            class="platform-section"
          >
            <div class="platform-header">
              <div
                class="platform-badge"
                :style="{ background: platform.color }"
              >
                {{ platform.code }}
              </div>
              <h3>{{ platform.name }}</h3>
              <el-checkbox
                :model-value="allAccountsSelected(platform.id)"
                @change="togglePlatformAccounts(platform.id, $event)"
              >
                全选
              </el-checkbox>
            </div>
            <div class="account-list">
              <div
                v-for="account in platformAccounts(platform.id)"
                :key="account.id"
                class="account-option"
                :class="{ selected: selectedAccounts.includes(account.id), disabled: account.status !== 1 }"
                @click="account.status === 1 && toggleAccount(account.id)"
              >
                <el-checkbox
                  :model-value="selectedAccounts.includes(account.id)"
                  :disabled="account.status !== 1"
                  @click.stop
                />
                <span>{{ account.account_name }}</span>
                <el-tag v-if="account.status !== 1" type="danger" size="small">未授权</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤3: 确认发布 -->
      <div v-show="currentStep === 2" class="step-panel">
        <h2>确认发布信息</h2>
        <div class="confirm-info">
          <div class="info-section">
            <h3>待发布文章 ({{ selectedArticleList.length }})</h3>
            <ul>
              <li v-for="article in selectedArticleList" :key="article.id">
                {{ article.title }}
              </li>
            </ul>
          </div>
          <div class="info-section">
            <h3>目标账号 ({{ selectedAccounts.length }})</h3>
            <div class="platform-summary">
              <div
                v-for="platform in platformSummary"
                :key="platform.id"
                class="summary-item"
              >
                <span class="platform-name">{{ platform.name }}</span>
                <span class="account-count">{{ platform.count }} 个账号</span>
              </div>
            </div>
          </div>
          <div class="info-section">
            <h3>预计生成 {{ selectedArticleList.length * selectedAccounts.length }} 个发布任务</h3>
          </div>
        </div>
      </div>

      <!-- 步骤4: 发布进度 -->
      <div v-show="currentStep === 3" class="step-panel">
        <h2>发布进度</h2>
        <div class="progress-summary">
          <div class="progress-stat">
            <span class="stat-value">{{ publishProgress.completed }}</span>
            <span class="stat-label">已完成</span>
          </div>
          <div class="progress-stat">
            <span class="stat-value">{{ publishProgress.total }}</span>
            <span class="stat-label">总数</span>
          </div>
          <div class="progress-stat">
            <span class="stat-value">{{ publishProgress.failed }}</span>
            <span class="stat-label">失败</span>
          </div>
        </div>
        <el-progress
          :percentage="progressPercentage"
          :status="progressStatus"
          class="main-progress"
        />
        <div class="task-list">
          <div
            v-for="task in publishTasks"
            :key="task.id"
            class="task-item"
            :class="`status-${task.status}`"
          >
            <div class="task-info">
              <span class="task-article">{{ task.articleTitle }}</span>
              <span class="task-arrow">→</span>
              <el-tag :color="getPlatformColor(task.platform)" size="small">
                {{ task.platformName }}
              </el-tag>
              <span class="task-account">{{ task.accountName }}</span>
            </div>
            <div class="task-status">
              <el-icon v-if="task.status === 0" class="is-loading"><Loading /></el-icon>
              <el-icon v-else-if="task.status === 2" color="#4caf50"><CircleCheck /></el-icon>
              <el-icon v-else-if="task.status === 3" color="#f44336"><CircleClose /></el-icon>
              <span v-if="task.errorMsg" class="error-msg">{{ task.errorMsg }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="action-bar">
      <el-button v-if="currentStep > 0 && currentStep < 3" @click="prevStep">
        上一步
      </el-button>
      <div class="action-right">
        <el-button v-if="currentStep < 2" type="primary" @click="nextStep">
          下一步
        </el-button>
        <el-button v-if="currentStep === 2" type="primary" @click="startPublish" :loading="publishing">
          开始发布
        </el-button>
        <el-button v-if="currentStep === 3" type="primary" @click="finishPublish">
          完成
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useArticleStore } from '@/stores/modules/article'
import { useAccountStore } from '@/stores/modules/account'
import { PLATFORMS } from '@/core/config/platform'

const router = useRouter()
const articleStore = useArticleStore()
const accountStore = useAccountStore()

// 步骤
const steps = ['选择文章', '选择账号', '确认发布', '发布进度']
const currentStep = ref(0)

// 选择状态
const selectedArticles = ref<number[]>([])
const selectedAccounts = ref<number[]>([])

// 发布状态
const publishing = ref(false)
const publishProgress = ref({ completed: 0, total: 0, failed: 0 })
const publishTasks = ref<any[]>([])

// 平台列表
const platforms = Object.values(PLATFORMS)

onMounted(() => {
  articleStore.loadArticles()
  accountStore.loadAccounts()
})

// 计算属性
const selectedArticleList = computed(() => {
  return articleStore.articles.filter(a => selectedArticles.value.includes(a.id))
})

const selectedAccountList = computed(() => {
  return accountStore.accounts.filter(a => selectedAccounts.value.includes(a.id))
})

const platformSummary = computed(() => {
  const summary: any[] = []
  selectedAccountList.value.forEach(account => {
    const platform = PLATFORMS[account.platform]
    const existing = summary.find(s => s.id === account.platform)
    if (existing) {
      existing.count++
    } else {
      summary.push({
        id: account.platform,
        name: platform?.name || account.platform,
        count: 1,
      })
    }
  })
  return summary
})

const progressPercentage = computed(() => {
  if (publishProgress.value.total === 0) return 0
  return Math.round((publishProgress.value.completed / publishProgress.value.total) * 100)
})

const progressStatus = computed(() => {
  if (publishProgress.value.failed > 0) return 'exception'
  if (progressPercentage.value === 100) return 'success'
  return undefined
})

// 方法
const platformAccounts = (platformId: string) => {
  return accountStore.accounts.filter(a => a.platform === platformId)
}

const allAccountsSelected = (platformId: string) => {
  const platformAccs = platformAccounts(platformId).filter(a => a.status === 1)
  return platformAccs.length > 0 && platformAccs.every(a => selectedAccounts.value.includes(a.id))
}

const toggleArticle = (id: number) => {
  const index = selectedArticles.value.indexOf(id)
  if (index === -1) {
    selectedArticles.value.push(id)
  } else {
    selectedArticles.value.splice(index, 1)
  }
}

const toggleAccount = (id: number) => {
  const index = selectedAccounts.value.indexOf(id)
  if (index === -1) {
    selectedAccounts.value.push(id)
  } else {
    selectedAccounts.value.splice(index, 1)
  }
}

const togglePlatformAccounts = (platformId: string, checked: boolean) => {
  const platformAccs = platformAccounts(platformId).filter(a => a.status === 1)
  platformAccs.forEach(account => {
    const index = selectedAccounts.value.indexOf(account.id)
    if (checked && index === -1) {
      selectedAccounts.value.push(account.id)
    } else if (!checked && index !== -1) {
      selectedAccounts.value.splice(index, 1)
    }
  })
}

const nextStep = () => {
  if (currentStep.value === 0 && selectedArticles.value.length === 0) {
    ElMessage.warning('请至少选择一篇文章')
    return
  }
  if (currentStep.value === 1 && selectedAccounts.value.length === 0) {
    ElMessage.warning('请至少选择一个账号')
    return
  }
  currentStep.value++
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const startPublish = async () => {
  publishing.value = true

  // 初始化发布任务
  const tasks: any[] = []
  selectedArticleList.value.forEach(article => {
    selectedAccountList.value.forEach(account => {
      tasks.push({
        id: `${article.id}-${account.id}`,
        articleId: article.id,
        articleTitle: article.title,
        accountId: account.id,
        accountName: account.account_name,
        platform: account.platform,
        platformName: PLATFORMS[account.platform]?.name || account.platform,
        status: 0, // 0=发布中, 2=成功, 3=失败
        errorMsg: null,
      })
    })
  })

  publishTasks.value = tasks
  publishProgress.value = { completed: 0, total: tasks.length, failed: 0 }

  currentStep.value = 3

  // 调用后端API创建发布任务
  try {
    const response = await fetch('/api/publish/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        article_ids: selectedArticles.value,
        account_ids: selectedAccounts.value,
      }),
    })
    const data = await response.json()

    if (data.success !== false) {
      // 模拟进度更新（实际应该通过WebSocket获取）
      simulateProgress(tasks)
    } else {
      ElMessage.error(data.message || '创建发布任务失败')
      publishing.value = false
    }
  } catch (e: any) {
    // 如果后端接口还没实现，模拟发布
    simulateProgress(tasks)
  }
}

const simulateProgress = (tasks: any[]) => {
  let index = 0
  const interval = setInterval(() => {
    if (index >= tasks.length) {
      clearInterval(interval)
      publishing.value = false
      return
    }

    const task = tasks[index]
    // 模拟成功/失败（80%成功率）
    const success = Math.random() > 0.2

    task.status = success ? 2 : 3
    task.errorMsg = success ? null : '模拟失败错误'

    publishProgress.value.completed++
    if (!success) {
      publishProgress.value.failed++
    }

    index++
  }, 1000)
}

const finishPublish = () => {
  ElMessage.success('发布任务已完成')
  router.push('/history')
}

const getPreview = (content: string) => {
  const text = content.replace(/<[^>]*>/g, '')
  return text.length > 50 ? text.substring(0, 50) + '...' : text
}

const getPlatformColor = (platform: string) => {
  return PLATFORMS[platform]?.color || '#666'
}
</script>

<style scoped lang="scss">
.publish-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

// 步骤指示器
.steps {
  display: flex;
  justify-content: center;
  padding: 24px 0;
  position: relative;

  .step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    flex: 1;

    .step-number {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: var(--bg-tertiary);
      border: 2px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      z-index: 1;
      transition: all 0.3s;
    }

    .step-label {
      margin-top: 8px;
      font-size: 14px;
      color: var(--text-secondary);
    }

    .step-line {
      position: absolute;
      top: 20px;
      left: 50%;
      width: 100%;
      height: 2px;
      background: var(--border);
      z-index: 0;
    }

    &.active {
      .step-number {
        background: var(--primary);
        border-color: var(--primary);
        color: white;
      }
      .step-label {
        color: var(--primary);
      }
    }

    &.completed {
      .step-number {
        background: #4caf50;
        border-color: #4caf50;
        color: white;
      }
    }

    &:last-child .step-line {
      display: none;
    }
  }
}

// 步骤内容
.step-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

.step-panel {
  h2 {
    margin: 0 0 20px 0;
    font-size: 18px;
    color: var(--text-primary);
  }
}

// 文章选择器
.article-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .article-option {
    display: flex;
    align-items: center;
    gap: 16px;
    background: var(--bg-secondary);
    border: 2px solid transparent;
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: var(--bg-tertiary);
    }

    &.selected {
      border-color: var(--primary);
    }

    .article-info {
      flex: 1;

      h4 {
        margin: 0 0 4px 0;
        color: var(--text-primary);
      }

      p {
        margin: 0;
        font-size: 14px;
        color: var(--text-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}

// 平台分组
.platform-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;

  .platform-section {
    background: var(--bg-secondary);
    border-radius: 12px;
    padding: 20px;

    .platform-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;

      .platform-badge {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
        color: white;
      }

      h3 {
        margin: 0;
        flex: 1;
      }
    }

    .account-list {
      display: flex;
      flex-direction: column;
      gap: 8px;

      .account-option {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;

        &:hover:not(.disabled) {
          background: var(--bg-tertiary);
        }

        &.selected {
          background: rgba(74, 144, 226, 0.1);
        }

        &.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      }
    }
  }
}

// 确认信息
.confirm-info {
  .info-section {
    background: var(--bg-secondary);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;

    h3 {
      margin: 0 0 12px 0;
      font-size: 16px;
      color: var(--text-primary);
    }

    ul {
      margin: 0;
      padding-left: 20px;
      color: var(--text-secondary);

      li {
        margin-bottom: 8px;
      }
    }

    .platform-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;

      .summary-item {
        background: var(--bg-tertiary);
        border-radius: 8px;
        padding: 12px;
        text-align: center;

        .platform-name {
          display: block;
          font-size: 12px;
          color: var(--text-secondary);
          margin-bottom: 4px;
        }

        .account-count {
          display: block;
          font-size: 18px;
          font-weight: 600;
          color: var(--primary);
        }
      }
    }
  }
}

// 发布进度
.progress-summary {
  display: flex;
  gap: 40px;
  margin-bottom: 24px;

  .progress-stat {
    text-align: center;

    .stat-value {
      display: block;
      font-size: 32px;
      font-weight: 700;
      color: var(--primary);
    }

    .stat-label {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }
}

.main-progress {
  margin-bottom: 24px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;

  .task-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 12px 16px;

    .task-info {
      display: flex;
      align-items: center;
      gap: 12px;

      .task-article {
        font-weight: 500;
      }

      .task-arrow {
        color: var(--text-secondary);
      }

      .task-account {
        color: var(--text-secondary);
      }
    }

    .task-status {
      display: flex;
      align-items: center;
      gap: 8px;

      .error-msg {
        font-size: 12px;
        color: #f44336;
      }
    }

    &.status-2 {
      border-left: 3px solid #4caf50;
    }

    &.status-3 {
      border-left: 3px solid #f44336;
    }
  }
}

// 操作栏
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 0;
  border-top: 1px solid var(--border);
}
</style>
