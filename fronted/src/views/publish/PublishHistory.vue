<template>
  <div class="publish-history-page">
    <h2>发布记录</h2>
    <el-table :data="records" stripe>
      <el-table-column prop="articleTitle" label="文章标题" />
      <el-table-column prop="platformName" label="平台">
        <template #default="{ row }">
          <el-tag :color="getPlatformColor(row.platform)">
            {{ row.platformName }}
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
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button v-if="row.platformUrl" text type="primary" @click="openUrl(row.platformUrl)">
            查看文章
          </el-button>
          <el-button v-else-if="row.status === 3" text type="warning" @click="retry(row)">
            重试
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { PLATFORMS } from '@/core/config/platform'

const records = ref([
  {
    articleTitle: '示例文章',
    platform: 'zhihu',
    platformName: '知乎',
    accountName: '我的账号',
    status: 2,
    platformUrl: 'https://zhuanlan.zhihu.com/p/123456',
    publishedAt: '2025-01-08 12:00',
  },
])

onMounted(async () => {
  try {
    const response = await fetch('/api/publish/records?limit=50')
    const data = await response.json()
    if (Array.isArray(data)) {
      records.value = data
    }
  } catch {
    // 使用模拟数据
  }
})

const openUrl = (url: string) => {
  window.open(url, '_blank')
}

const retry = (record: any) => {
  ElMessage.info('重试功能开发中')
}

const getPlatformColor = (platform: string) => {
  return PLATFORMS[platform]?.color || '#666'
}

const getStatusType = (status: number) => {
  const types: Record<number, string> = { 0: 'info', 1: 'warning', 2: 'success', 3: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status: number) => {
  const texts: Record<number, string> = { 0: '待发布', 1: '发布中', 2: '成功', 3: '失败' }
  return texts[status] || '未知'
}
</script>

<style scoped lang="scss">
.publish-history-page {
  display: flex;
  flex-direction: column;
  gap: 20px;

  h2 {
    margin: 0;
  }
}
</style>
