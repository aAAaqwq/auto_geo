<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div
        v-for="stat in stats"
        :key="stat.key"
        class="stat-card"
        :class="`gradient-${stat.color}`"
      >
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">{{ stat.label }}</div>
        <div class="stat-trend" v-if="stat.trend">
          <el-icon><TrendCharts /></el-icon>
          <span>{{ stat.trend }}</span>
        </div>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="section">
      <h2 class="section-title">快速操作</h2>
      <div class="quick-actions">
        <el-button type="primary" size="large" @click="goToAccounts">
          <el-icon><User /></el-icon>
          添加账号
        </el-button>
        <el-button type="success" size="large" @click="goToArticleEdit">
          <el-icon><DocumentAdd /></el-icon>
          新建文章
        </el-button>
        <el-button type="warning" size="large" @click="goToPublish">
          <el-icon><Promotion /></el-icon>
          批量发布
        </el-button>
      </div>
    </div>

    <!-- 最近发布 -->
    <div class="section">
      <h2 class="section-title">最近发布</h2>
      <el-table :data="recentPublishes" stripe style="width: 100%">
        <el-table-column prop="articleTitle" label="文章标题" />
        <el-table-column prop="platform" label="平台">
          <template #default="{ row }">
            <el-tag :color="getPlatformColor(row.platform)">
              {{ getPlatformName(row.platform) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="accountName" label="账号" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="publishedAt" label="发布时间" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { TrendCharts, User, DocumentAdd, Promotion } from '@element-plus/icons-vue'
import { useAccountStore } from '@/stores/modules/account'
import { useArticleStore } from '@/stores/modules/article'

const router = useRouter()
const accountStore = useAccountStore()
const articleStore = useArticleStore()

// 统计数据
const stats = ref([
  { key: 'accounts', label: '已授权账号', value: 0, color: 'blue', trend: null },
  { key: 'articles', label: '文章总数', value: 0, color: 'green', trend: null },
  { key: 'published', label: '已发布文章', value: 0, color: 'orange', trend: null },
  { key: 'pending', label: '待发布', value: 0, color: 'purple', trend: null },
])

// 最近发布记录
const recentPublishes = ref([
  {
    articleTitle: '示例文章标题',
    platform: 'zhihu',
    accountName: '我的知乎账号',
    status: 2,
    publishedAt: '2025-01-08 12:00',
  },
])

// 加载数据
onMounted(async () => {
  await accountStore.loadAccounts()
  await articleStore.loadArticles({ pageSize: 100 })

  stats.value[0].value = accountStore.authorizedCount
  stats.value[1].value = articleStore.totalCount
  stats.value[2].value = articleStore.publishedArticles.length
  stats.value[3].value = articleStore.draftArticles.length
})

// 导航方法
const goToAccounts = () => router.push('/accounts')
const goToArticleEdit = () => router.push('/articles/add')
const goToPublish = () => router.push('/publish')

// 工具方法
const getPlatformColor = (platform: string) => {
  const colors: Record<string, string> = {
    zhihu: '#0084FF',
    baijiahao: '#E53935',
    sohu: '#FF6B00',
    toutiao: '#333333',
  }
  return colors[platform] || '#666'
}

const getPlatformName = (platform: string) => {
  const names: Record<string, string> = {
    zhihu: '知乎',
    baijiahao: '百家号',
    sohu: '搜狐号',
    toutiao: '头条号',
  }
  return names[platform] || platform
}

const getStatusType = (status: number) => {
  const types: Record<number, string> = {
    0: 'info',
    1: 'warning',
    2: 'success',
    3: 'danger',
  }
  return types[status] || 'info'
}

const getStatusText = (status: number) => {
  const texts: Record<number, string> = {
    0: '待发布',
    1: '发布中',
    2: '成功',
    3: '失败',
  }
  return texts[status] || '未知'
}
</script>

<style scoped lang="scss">
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

// 统计卡片
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  border-radius: 16px;
  padding: 24px;
  color: white;
  position: relative;
  overflow: hidden;

  &.gradient-blue {
    background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  }

  &.gradient-green {
    background: linear-gradient(135deg, #4caf50 0%, #3d8b40 100%);
  }

  &.gradient-orange {
    background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  }

  &.gradient-purple {
    background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  }

  .stat-value {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .stat-label {
    font-size: 14px;
    opacity: 0.9;
  }

  .stat-trend {
    position: absolute;
    top: 16px;
    right: 16px;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    opacity: 0.8;
  }
}

// 区块
.section {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 24px;

  .section-title {
    margin: 0 0 16px 0;
    font-size: 16px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .quick-actions {
    display: flex;
    gap: 16px;
  }
}

// 表格样式覆盖
:deep(.el-table) {
  background: transparent;
  color: var(--text-primary);

  .el-table__header {
    th {
      background: var(--bg-tertiary);
      color: var(--text-secondary);
    }
  }

  .el-table__body {
    tr {
      background: transparent;

      &:hover td {
        background: var(--bg-tertiary);
      }
    }

    td {
      border-color: var(--border);
    }
  }
}
</style>
