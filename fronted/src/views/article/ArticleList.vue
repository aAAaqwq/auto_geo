<template>
  <div class="article-list-page">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文章标题"
          clearable
          style="width: 250px"
          @change="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px" @change="handleSearch">
          <el-option label="全部" :value="undefined" />
          <el-option label="草稿" :value="0" />
          <el-option label="已发布" :value="1" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="goToCreate">
          <el-icon><Plus /></el-icon>
          新建文章
        </el-button>
      </div>
    </div>

    <!-- 文章列表 -->
    <div class="article-list">
      <div
        v-for="article in articleStore.articles"
        :key="article.id"
        class="article-item"
        :class="{ selected: articleStore.selectedArticleIds.includes(article.id) }"
        @click="toggleSelection(article.id)"
      >
        <div class="article-checkbox">
          <el-checkbox
            :model-value="articleStore.selectedArticleIds.includes(article.id)"
            @change="toggleSelection(article.id)"
            @click.stop
          />
        </div>
        <div class="article-content" @click.stop>
          <h3 class="article-title">{{ article.title }}</h3>
          <p class="article-preview">{{ getPreview(article.content) }}</p>
          <div class="article-meta">
            <el-tag :type="article.status === 1 ? 'success' : 'info'" size="small">
              {{ article.status === 1 ? '已发布' : '草稿' }}
            </el-tag>
            <span class="meta-text">{{ formatDate(article.created_at) }}</span>
            <span class="meta-text">{{ article.view_count }} 阅读</span>
          </div>
        </div>
        <div class="article-actions" @click.stop>
          <el-button text @click="editArticle(article.id)">
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button text type="danger" @click="deleteArticle(article.id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="articleStore.articles.length === 0 && !articleStore.loading" class="empty-state">
      <el-icon class="empty-icon"><Document /></el-icon>
      <p>暂无文章</p>
      <el-button type="primary" @click="goToCreate">创建第一篇文章</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Plus, Edit, Delete, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useArticleStore } from '@/stores/modules/article'

const router = useRouter()
const articleStore = useArticleStore()

const searchKeyword = ref('')
const statusFilter = ref<number | undefined>(undefined)

onMounted(() => {
  articleStore.loadArticles()
})

const handleSearch = () => {
  articleStore.loadArticles({
    keyword: searchKeyword.value,
    status: statusFilter.value,
  })
}

const goToCreate = () => {
  router.push('/articles/add')
}

const editArticle = (id: number) => {
  router.push(`/articles/edit/${id}`)
}

const deleteArticle = async (id: number) => {
  const article = articleStore.articles.find(a => a.id === id)
  if (!article) return

  try {
    await ElMessageBox.confirm(`确定要删除文章"${article.title}"吗？`, '确认删除', {
      type: 'warning',
    })

    const result = await articleStore.deleteArticle(id)
    if (result.success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message || '删除失败')
    }
  } catch {
    // 用户取消
  }
}

const toggleSelection = (id: number) => {
  articleStore.toggleArticleSelection(id)
}

const getPreview = (content: string) => {
  // 移除HTML标签
  const text = content.replace(/<[^>]*>/g, '')
  return text.length > 100 ? text.substring(0, 100) + '...' : text
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped lang="scss">
.article-list-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .toolbar-left {
    display: flex;
    gap: 12px;
  }
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-item {
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

  .article-checkbox {
    flex-shrink: 0;
  }

  .article-content {
    flex: 1;
    min-width: 0;

    .article-title {
      margin: 0 0 8px 0;
      font-size: 16px;
      font-weight: 500;
      color: var(--text-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .article-preview {
      margin: 0 0 12px 0;
      font-size: 14px;
      color: var(--text-secondary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .article-meta {
      display: flex;
      align-items: center;
      gap: 16px;

      .meta-text {
        font-size: 12px;
        color: var(--text-secondary);
      }
    }
  }

  .article-actions {
    flex-shrink: 0;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: var(--text-secondary);

  .empty-icon {
    font-size: 64px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  p {
    margin: 0 0 24px 0;
    font-size: 16px;
  }
}

// 输入框样式覆盖
:deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border-color: var(--border);
  box-shadow: none;

  &:hover,
  &.is-focus {
    border-color: var(--primary);
  }
}
</style>
