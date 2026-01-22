<template>
  <div class="scheduler-page">
    <!-- 头部 -->
    <header class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div class="header-text">
          <h1 class="page-title">定时任务管理</h1>
          <p class="page-desc">配置自动化任务，让系统自动运行</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button :type="schedulerRunning ? 'danger' : 'primary'" @click="toggleScheduler">
          <svg v-if="!schedulerRunning" viewBox="0 0 16 16" fill="currentColor" width="16">
            <path d="M10.804 8 5 4.633v6.734L10.804 8zm.792-.696a.802.802 0 011.04 0l6.5 4.5a.802.802 0 010 1.292l-6.5 4.5A.802.802 0 0111 16.5v-9a.802.802 0 01.596-.796z"/>
          </svg>
          <svg v-else viewBox="0 0 16 16" fill="currentColor" width="16">
            <path d="M5.5 3.5A1.5 1.5 0 017 5v6a1.5 1.5 0 01-3 0V5a1.5 1.5 0 011.5-1.5zm5 0A1.5 1.5 0 0112 5v6a1.5 1.5 0 01-3 0V5a1.5 1.5 0 011.5-1.5z"/>
          </svg>
          {{ schedulerRunning ? '停止服务' : '启动服务' }}
        </el-button>
      </div>
    </header>

    <!-- 服务状态卡片 -->
    <div class="status-section">
      <div class="status-card" :class="{ running: schedulerRunning }">
        <div class="status-icon">
          <div class="pulse-dot" :class="{ active: schedulerRunning }"></div>
        </div>
        <div class="status-info">
          <span class="status-label">定时任务服务</span>
          <span class="status-value">{{ schedulerRunning ? '运行中' : '已停止' }}</span>
        </div>
        <div class="status-meta">
          <span>已配置 {{ activeJobsCount }} 个任务</span>
        </div>
      </div>
    </div>

    <!-- 任务配置区 -->
    <div class="tasks-section">
      <div class="section-header">
        <h2 class="section-title">任务配置</h2>
        <div class="section-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-btn"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <span>{{ tab.icon }}</span>
            {{ tab.label }}
            <span v-if="getJobCount(tab.key) > 0" class="tab-count">{{ getJobCount(tab.key) }}</span>
          </button>
        </div>
      </div>

      <div class="tasks-content">
        <!-- GEO文章生成任务 -->
        <div v-if="activeTab === 'article'" class="task-config">
          <div class="config-card">
            <div class="card-header">
              <div class="header-left">
                <div class="task-icon article">
                  <svg viewBox="0 0 16 16" fill="currentColor" width="20">
                    <path d="M8.64 4.459c.365-.357.549-.838.549-1.408 0-.66-.196-1.2-.588-1.62-.392-.42-.942-.63-1.65-.63-.73 0-1.287.21-1.666.63-.379.42-.569.96-.569 1.62 0 .57.184 1.051.553 1.443.37.392.912.588 1.628.588.704 0 1.245-.196 1.613-.588l.03-.03zm-2.28-1.625c.118-.12.285-.18.5-.18.215 0 .382.06.5.18.116.12.174.274.174.462 0 .2-.058.355-.174.465-.116.11-.285.165-.506.165-.215 0-.38-.055-.495-.165-.114-.11-.171-.265-.171-.465 0-.188.057-.342.172-.462zm5.878 1.636c.365-.357.549-.838.549-1.408 0-.66-.196-1.2-.588-1.62-.392-.42-.942-.63-1.65-.63-.73 0-1.287.21-1.666.63-.379.42-.569.96-.569 1.62 0 .57.184 1.051.553 1.443.37.392.912.588 1.628.588.704 0 1.245-.196 1.613-.588l.03-.03zm-2.28-1.625c.118-.12.285-.18.5-.18.215 0 .382.06.5.18.116.12.174.274.174.462 0 .2-.058.355-.174.465-.116.11-.285.165-.506.165-.215 0-.38-.055-.495-.165-.114-.11-.171-.265-.171-.465 0-.188.057-.342.172-.462zM14 8v6H2V8h12zm-1 1H3v4h10V9zM2 6h12V4H2v2z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="card-title">GEO文章生成</h3>
                  <p class="card-desc">自动为项目关键词生成SEO优化文章</p>
                </div>
              </div>
              <div class="header-right">
                <el-switch
                  v-model="articleConfig.enabled"
                  :disabled="!schedulerRunning"
                  @change="updateJobConfig('article')"
                />
              </div>
            </div>

            <div class="card-body">
              <el-form label-position="left" label-width="100px">
                <el-form-item label="执行时间">
                  <div class="time-inputs">
                    <el-select v-model="articleConfig.scheduleType" style="width: 120px">
                      <el-option label="每天" value="daily" />
                      <el-option label="每周" value="weekly" />
                      <el-option label="每月" value="monthly" />
                    </el-select>
                    <el-time-picker
                      v-model="articleConfig.time"
                      format="HH:mm"
                      value-format="HH:mm"
                      placeholder="选择时间"
                      style="width: 140px"
                    />
                  </div>
                </el-form-item>

                <el-form-item label="目标项目">
                  <el-select v-model="articleConfig.projectId" placeholder="选择项目" style="width: 100%">
                    <el-option
                      v-for="project in projects"
                      :key="project.id"
                      :label="project.name"
                      :value="project.id"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="生成数量">
                  <el-input-number v-model="articleConfig.count" :min="1" :max="20" />
                  <span class="form-tip">每次为关键词生成文章的数量</span>
                </el-form-item>
              </el-form>

              <div class="next-run-info" v-if="articleConfig.enabled">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14">
                  <path d="M8 3.5a.5.5 0 01.5.5v5.21l3.248 1.856a.5.5 0 01-.496.868l-3.5-2A.5.5 0 018 9V4a.5.5 0 01.5-.5z"/>
                  <path d="M8 16A8 8 0 108 0a8 8 0 000 16zm7-8A7 7 0 11 1 8a7 7 0 0114 0z"/>
                </svg>
                <span>下次运行：{{ getNextRunTime(articleConfig) }}</span>
              </div>
            </div>

            <div class="card-footer">
              <el-button @click="runNow('article')">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14">
                  <path d="M10.804 8 5 4.633v6.734L10.804 8zm.792-.696a.802.802 0 011.04 0l6.5 4.5a.802.802 0 010 1.292l-6.5 4.5A.802.802 0 0111 16.5v-9a.802.802 0 01.596-.796z"/>
                </svg>
                立即运行一次
              </el-button>
              <el-button link @click="viewHistory('article')">查看历史</el-button>
            </div>
          </div>
        </div>

        <!-- 收录检测任务 -->
        <div v-if="activeTab === 'index'" class="task-config">
          <div class="config-card">
            <div class="card-header">
              <div class="header-left">
                <div class="task-icon index">
                  <svg viewBox="0 0 16 16" fill="currentColor" width="20">
                    <path d="M11.742 10.344a6.5 6.5 0 11-1.397-1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 01-1.415 1.414l-3.85-3.85a1.007 1.007 0 01-.115-.1zM12 6.5a5.5 5.5 0 11-11 0 5.5 5.5 0 0111 0z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="card-title">收录检测</h3>
                  <p class="card-desc">自动检测关键词在AI搜索引擎的收录情况</p>
                </div>
              </div>
              <div class="header-right">
                <el-switch
                  v-model="indexConfig.enabled"
                  :disabled="!schedulerRunning"
                  @change="updateJobConfig('index')"
                />
              </div>
            </div>

            <div class="card-body">
              <el-form label-position="left" label-width="100px">
                <el-form-item label="执行时间">
                  <div class="time-inputs">
                    <el-select v-model="indexConfig.scheduleType" style="width: 120px">
                      <el-option label="每天" value="daily" />
                      <el-option label="每周" value="weekly" />
                    </el-select>
                    <el-time-picker
                      v-model="indexConfig.time"
                      format="HH:mm"
                      value-format="HH:mm"
                      placeholder="选择时间"
                      style="width: 140px"
                    />
                  </div>
                </el-form-item>

                <el-form-item label="检测平台">
                  <el-checkbox-group v-model="indexConfig.platforms">
                    <el-checkbox label="doubao">豆包</el-checkbox>
                    <el-checkbox label="qianwen">通义千问</el-checkbox>
                    <el-checkbox label="deepseek">DeepSeek</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>

                <el-form-item label="并发数量">
                  <el-input-number v-model="indexConfig.concurrency" :min="1" :max="5" />
                  <span class="form-tip">同时进行的检测任务数</span>
                </el-form-item>
              </el-form>

              <div class="next-run-info" v-if="indexConfig.enabled">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14">
                  <path d="M8 3.5a.5.5 0 01.5.5v5.21l3.248 1.856a.5.5 0 01-.496.868l-3.5-2A.5.5 0 018 9V4a.5.5 0 01.5-.5z"/>
                  <path d="M8 16A8 8 0 108 0a8 8 0 000 16zm7-8A7 7 0 11 1 8a7 7 0 0114 0z"/>
                </svg>
                <span>下次运行：{{ getNextRunTime(indexConfig) }}</span>
              </div>
            </div>

            <div class="card-footer">
              <el-button @click="runNow('index')">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14">
                  <path d="M10.804 8 5 4.633v6.734L10.804 8zm.792-.696a.802.802 0 011.04 0l6.5 4.5a.802.802 0 010 1.292l-6.5 4.5A.802.802 0 0111 16.5v-9a.802.802 0 01.596-.796z"/>
                </svg>
                立即运行一次
              </el-button>
              <el-button link @click="viewHistory('index')">查看历史</el-button>
            </div>
          </div>
        </div>

        <!-- 文章发布任务 -->
        <div v-if="activeTab === 'publish'" class="task-config">
          <div class="config-card">
            <div class="card-header">
              <div class="header-left">
                <div class="task-icon publish">
                  <svg viewBox="0 0 16 16" fill="currentColor" width="20">
                    <path d="M13.5 1a1.5 1.5 0 11 0 3 1.5 1.5 0 010-3zM11 2.5a2.5 2.5 0 11.603 1.628l-6.718 3.12a2.499 2.499 0 01 0 1.504l6.718 3.12a2.5 2.5 0 11-.488.876l-6.718-3.12a2.5 2.5 0 110-3.256l6.718-3.12A2.5 2.5 0 0111 2.5zm-8.5 4a1.5 1.5 0 100 3 1.5 1.5 0 000-3zm8.5 3a1.5 1.5 0 110 3 1.5 1.5 0 010-3z"/>
                  </svg>
                </div>
                <div>
                  <h3 class="card-title">文章自动发布</h3>
                  <p class="card-desc">自动将生成的文章发布到各个平台</p>
                </div>
              </div>
              <div class="header-right">
                <el-switch
                  v-model="publishConfig.enabled"
                  :disabled="!schedulerRunning"
                  @change="updateJobConfig('publish')"
                />
              </div>
            </div>

            <div class="card-body">
              <el-form label-position="left" label-width="100px">
                <el-form-item label="执行时间">
                  <div class="time-inputs">
                    <el-select v-model="publishConfig.scheduleType" style="width: 120px">
                      <el-option label="每天" value="daily" />
                      <el-option label="每周" value="weekly" />
                      <el-option label="工作日" value="weekdays" />
                    </el-select>
                    <el-time-picker
                      v-model="publishConfig.time"
                      format="HH:mm"
                      value-format="HH:mm"
                      placeholder="选择时间"
                      style="width: 140px"
                    />
                  </div>
                </el-form-item>

                <el-form-item label="发布平台">
                  <el-checkbox-group v-model="publishConfig.platforms">
                    <el-checkbox label="zhihu">知乎</el-checkbox>
                    <el-checkbox label="baijiahao">百家号</el-checkbox>
                    <el-checkbox label="sohu">搜狐</el-checkbox>
                    <el-checkbox label="toutiao">头条号</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>

                <el-form-item label="每次发布">
                  <el-input-number v-model="publishConfig.count" :min="1" :max="10" />
                  <span class="form-tip">每次发布的文章数量</span>
                </el-form-item>
              </el-form>

              <div class="next-run-info" v-if="publishConfig.enabled">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14">
                  <path d="M8 3.5a.5.5 0 01.5.5v5.21l3.248 1.856a.5.5 0 01-.496.868l-3.5-2A.5.5 0 018 9V4a.5.5 0 01.5-.5z"/>
                  <path d="M8 16A8 8 0 108 0a8 8 0 000 16zm7-8A7 7 0 11 1 8a7 7 0 0114 0z"/>
                </svg>
                <span>下次运行：{{ getNextRunTime(publishConfig) }}</span>
              </div>
            </div>

            <div class="card-footer">
              <el-button @click="runNow('publish')">
                <svg viewBox="0 0 16 16" fill="currentColor" width="14">
                  <path d="M10.804 8 5 4.633v6.734L10.804 8zm.792-.696a.802.802 0 011.04 0l6.5 4.5a.802.802 0 010 1.292l-6.5 4.5A.802.802 0 0111 16.5v-9a.802.802 0 01.596-.796z"/>
                </svg>
                立即运行一次
              </el-button>
              <el-button link @click="viewHistory('publish')">查看历史</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 执行历史 -->
    <div class="history-section">
      <div class="section-header">
        <h2 class="section-title">执行历史</h2>
        <el-button text @click="loadHistory">
          <svg viewBox="0 0 16 16" fill="currentColor" width="14">
            <path d="M16 8A8 8 0 11 0 8a8 8 0 0116 0zM6.79 5.093A.5.5 0 006 5.5v5a.5.5 0 00.79.407l3.5-2.5a.5.5 0 000-.814l-3.5-2.5z"/>
          </svg>
          刷新
        </el-button>
      </div>

      <div class="history-list">
        <div
          v-for="item in history"
          :key="item.id"
          class="history-item"
          :class="`status-${item.status}`"
        >
          <div class="item-icon">
            <svg v-if="item.status === 'success'" viewBox="0 0 16 16" fill="currentColor" width="16">
              <path d="M16 8A8 8 0 110 8a8 8 0 0116 0zm-3.97-3.03a.75.75 0 00-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 00-1.06 1.06L6.97 11.03a.75.75 0 001.079-.02l3.992-4.99a.75.75 0 00-.01-1.05z"/>
            </svg>
            <svg v-else-if="item.status === 'error'" viewBox="0 0 16 16" fill="currentColor" width="16">
              <path d="M16 8A8 8 0 110 8a8 8 0 0116 0zM8 4a.905.905 0 00-.9.995l.35 3.507a.552.552 0 001.1 0L8.9 4.995A.905.905 0 008 4zm.002 6a1 1 0 100 2 1 1 0 000-2z"/>
            </svg>
            <svg v-else viewBox="0 0 16 16" fill="currentColor" width="16">
              <path d="M8 3.5a.5.5 0 01.5.5v5.21l3.248 1.856a.5.5 0 01-.496.868l-3.5-2A.5.5 0 018 9V4a.5.5 0 01.5-.5z"/>
              <path d="M8 16A8 8 0 108 0a8 8 0 000 16zm7-8A7 7 0 11 1 8a7 7 0 0114 0z"/>
            </svg>
          </div>
          <div class="item-content">
            <div class="item-header">
              <span class="item-type">{{ getJobTypeName(item.type) }}</span>
              <span class="item-time">{{ formatTime(item.time) }}</span>
            </div>
            <p class="item-message">{{ item.message }}</p>
            <div v-if="item.details" class="item-details">
              {{ item.details }}
            </div>
          </div>
          <div class="item-status">
            <el-tag :type="getStatusType(item.status)" size="small">
              {{ getStatusText(item.status) }}
            </el-tag>
          </div>
        </div>

        <el-empty v-if="history.length === 0" description="暂无执行记录" />
      </div>
    </div>

    <!-- 历史详情对话框 -->
    <el-dialog
      v-model="showHistoryDialog"
      title="执行历史详情"
      width="600px"
    >
      <div class="history-detail">
        <div v-for="item in filteredHistory" :key="item.id" class="detail-item">
          <div class="detail-time">{{ formatTime(item.time) }}</div>
          <div class="detail-content">
            <span class="detail-status" :class="`status-${item.status}`">
              {{ getStatusText(item.status) }}
            </span>
            <span class="detail-message">{{ item.message }}</span>
          </div>
        </div>
        <el-empty v-if="filteredHistory.length === 0" description="暂无记录" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

// ==================== 类型定义 ====================
interface Project {
  id: number
  name: string
}

interface JobConfig {
  enabled: boolean
  scheduleType: string
  time: string
  projectId?: number
  count?: number
  platforms?: string[]
  concurrency?: number
}

interface HistoryItem {
  id: number
  type: string
  status: 'success' | 'error' | 'running'
  time: string
  message: string
  details?: string
}

// ==================== 状态 ====================
const schedulerRunning = ref(true)
const activeTab = ref('index')
const showHistoryDialog = ref(false)

const projects = ref<Project[]>([
  { id: 1, name: '绿阳环保无人机清洗' },
  { id: 2, name: '智能云CRM系统' },
])

const articleConfig = ref<JobConfig>({
  enabled: false,
  scheduleType: 'daily',
  time: '09:00',
  projectId: undefined,
  count: 5,
})

const indexConfig = ref<JobConfig>({
  enabled: true,
  scheduleType: 'daily',
  time: '02:00',
  platforms: ['doubao', 'qianwen', 'deepseek'],
  concurrency: 3,
})

const publishConfig = ref<JobConfig>({
  enabled: false,
  scheduleType: 'weekdays',
  time: '10:00',
  platforms: ['zhihu', 'baijiahao'],
  count: 3,
})

const history = ref<HistoryItem[]>([
  {
    id: 1,
    type: 'index',
    status: 'success',
    time: new Date(Date.now() - 3600000).toISOString(),
    message: '收录检测完成',
    details: '检测了 15 个关键词，命中率 60%',
  },
  {
    id: 2,
    type: 'index',
    status: 'success',
    time: new Date(Date.now() - 86400000).toISOString(),
    message: '收录检测完成',
    details: '检测了 15 个关键词，命中率 58%',
  },
  {
    id: 3,
    type: 'article',
    status: 'error',
    time: new Date(Date.now() - 172800000).toISOString(),
    message: '文章生成失败',
    details: 'API请求超时，请检查网络连接',
  },
])

const tabs = [
  { key: 'article', label: 'GEO文章生成', icon: '📝' },
  { key: 'index', label: '收录检测', icon: '🔍' },
  { key: 'publish', label: '文章发布', icon: '📤' },
]

const filteredHistory = ref<HistoryItem[]>([])

// ==================== 计算属性 ====================
const activeJobsCount = computed(() => {
  let count = 0
  if (articleConfig.value.enabled) count++
  if (indexConfig.value.enabled) count++
  if (publishConfig.value.enabled) count++
  return count
})

// ==================== 方法 ====================

// 获取任务数量
const getJobCount = (type: string) => {
  const configs = { article: articleConfig, index: indexConfig, publish: publishConfig }
  return configs[type as keyof typeof configs].value.enabled ? 1 : 0
}

// 切换服务状态
const toggleScheduler = async () => {
  if (schedulerRunning.value) {
    // 停止服务
    schedulerRunning.value = false
    ElMessage.warning('定时任务服务已停止')
  } else {
    // 启动服务
    schedulerRunning.value = true
    ElMessage.success('定时任务服务已启动')
  }
}

// 更新任务配置
const updateJobConfig = async (type: string) => {
  ElMessage.success('任务配置已更新')
  // TODO: 调用API保存配置
}

// 立即运行
const runNow = async (type: string) => {
  ElMessage.info(`正在执行 ${getJobTypeName(type)} 任务...`)
  // TODO: 调用API触发任务
}

// 查看历史
const viewHistory = (type: string) => {
  filteredHistory.value = history.value.filter(h => h.type === type)
  showHistoryDialog.value = true
}

// 加载历史
const loadHistory = async () => {
  // TODO: 从API加载
  ElMessage.success('历史记录已刷新')
}

// 获取下次运行时间
const getNextRunTime = (config: JobConfig) => {
  if (!config.enabled) return '--'

  const now = new Date()
  const [hours, minutes] = config.time.split(':').map(Number)

  let nextRun = new Date()
  nextRun.setHours(hours, minutes, 0, 0)

  if (nextRun <= now) {
    nextRun.setDate(nextRun.getDate() + 1)
  }

  const tomorrow = new Date(now)
  tomorrow.setDate(tomorrow.getDate() + 1)

  if (nextRun.getDate() === tomorrow.getDate() && nextRun.getMonth() === tomorrow.getMonth()) {
    return `明天 ${config.time}`
  }

  return `${nextRun.getMonth() + 1}月${nextRun.getDate()}日 ${config.time}`
}

// 获取任务类型名称
const getJobTypeName = (type: string) => {
  const names = {
    article: 'GEO文章生成',
    index: '收录检测',
    publish: '文章发布',
  }
  return names[type as keyof typeof names] || type
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types = {
    success: 'success',
    error: 'danger',
    running: 'warning',
  }
  return types[status as keyof typeof types] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts = {
    success: '成功',
    error: '失败',
    running: '运行中',
  }
  return texts[status as keyof typeof texts] || status
}

// 格式化时间
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)

  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// ==================== 生命周期 ====================
let refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // 每30秒刷新一次状态
  refreshTimer = setInterval(() => {
    // TODO: 获取服务状态
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped lang="scss">
.scheduler-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  padding: 24px;
  background: linear-gradient(135deg, #f8f9fc 0%, #f0f2f8 100%);
  overflow-y: auto;
}

// 头部
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .header-icon {
      width: 52px;
      height: 52px;
      border-radius: 14px;
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;

      svg {
        width: 26px;
        height: 26px;
      }
    }

    .page-title {
      margin: 0 0 4px 0;
      font-size: 22px;
      font-weight: 600;
      color: #1a1f36;
    }

    .page-desc {
      margin: 0;
      font-size: 13px;
      color: #9ca3af;
    }
  }
}

// 状态卡片
.status-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.status-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s;

  &.running {
    border-color: #22c55e;
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, transparent 100%);
  }

  .status-icon {
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: #f3f4f6;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;

    .pulse-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #9ca3af;

      &.active {
        background: #22c55e;
        animation: pulse 2s infinite;
      }
    }
  }

  .status-info {
    flex: 1;

    .status-label {
      display: block;
      font-size: 12px;
      color: #9ca3af;
      margin-bottom: 4px;
    }

    .status-value {
      display: block;
      font-size: 18px;
      font-weight: 600;
      color: #1a1f36;
    }
  }

  .status-meta {
    font-size: 12px;
    color: #9ca3af;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(34, 197, 94, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
  }
}

// 任务配置区
.tasks-section {
  background: white;
  border-radius: 16px;
  padding: 24px 28px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;

    .section-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1a1f36;
    }

    .section-tabs {
      display: flex;
      gap: 8px;
      background: #f3f4f6;
      padding: 4px;
      border-radius: 10px;

      .tab-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background: transparent;
        border: none;
        border-radius: 8px;
        font-size: 13px;
        color: #6b7280;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          color: #374151;
        }

        &.active {
          background: white;
          color: #4b5563;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .tab-count {
          padding: 2px 6px;
          background: #22c55e;
          color: white;
          border-radius: 10px;
          font-size: 11px;
        }
      }
    }
  }
}

.config-card {
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;

      .task-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;

        &.article {
          background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        }

        &.index {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }

        &.publish {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }
      }

      .card-title {
        margin: 0 0 4px 0;
        font-size: 16px;
        font-weight: 600;
        color: #1a1f36;
      }

      .card-desc {
        margin: 0;
        font-size: 12px;
        color: #9ca3af;
      }
    }
  }

  .card-body {
    padding: 24px;

    .time-inputs {
      display: flex;
      gap: 12px;
      align-items: center;
    }

    .form-tip {
      margin-left: 12px;
      font-size: 12px;
      color: #9ca3af;
    }

    .next-run-info {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background: rgba(34, 197, 94, 0.1);
      border-radius: 8px;
      font-size: 13px;
      color: #059669;

      svg {
        flex-shrink: 0;
      }
    }
  }

  .card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
  }
}

// 历史记录区
.history-section {
  background: white;
  border-radius: 16px;
  padding: 24px 28px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;

    .section-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1a1f36;
    }
  }
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
  border-left: 4px solid #e5e7eb;
  transition: all 0.2s;

  &:hover {
    background: #f3f4f6;
  }

  &.status-success {
    border-left-color: #22c55e;

    .item-icon {
      color: #22c55e;
      background: rgba(34, 197, 94, 0.1);
    }
  }

  &.status-error {
    border-left-color: #ef4444;

    .item-icon {
      color: #ef4444;
      background: rgba(239, 68, 68, 0.1);
    }
  }

  &.status-running {
    border-left-color: #f59e0b;

    .item-icon {
      color: #f59e0b;
      background: rgba(245, 158, 11, 0.1);
    }
  }

  .item-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .item-content {
    flex: 1;
    min-width: 0;

    .item-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;

      .item-type {
        font-weight: 500;
        color: #1a1f36;
      }

      .item-time {
        font-size: 12px;
        color: #9ca3af;
      }
    }

    .item-message {
      margin: 0 0 6px 0;
      font-size: 14px;
      color: #374151;
    }

    .item-details {
      font-size: 12px;
      color: #6b7280;
      background: white;
      padding: 8px 12px;
      border-radius: 6px;
    }
  }

  .item-status {
    flex-shrink: 0;
  }
}

// 历史详情对话框
.history-detail {
  max-height: 400px;
  overflow-y: auto;

  .detail-item {
    display: flex;
    gap: 16px;
    padding: 12px 0;
    border-bottom: 1px solid #e5e7eb;

    &:last-child {
      border-bottom: none;
    }

    .detail-time {
      font-size: 12px;
      color: #9ca3af;
      white-space: nowrap;
    }

    .detail-content {
      flex: 1;

      .detail-status {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        margin-right: 8px;

        &.status-success {
          background: rgba(34, 197, 94, 0.1);
          color: #059669;
        }

        &.status-error {
          background: rgba(239, 68, 68, 0.1);
          color: #dc2626;
        }

        &.status-running {
          background: rgba(245, 158, 11, 0.1);
          color: #d97706;
        }
      }

      .detail-message {
        font-size: 13px;
        color: #374151;
      }
    }
  }
}

// 滚动条
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;

  &:hover {
    background: #9ca3af;
  }
}
</style>
