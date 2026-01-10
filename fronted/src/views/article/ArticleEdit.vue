<template>
  <div class="article-edit-page">
    <div class="toolbar">
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div class="toolbar-right">
        <el-button @click="saveDraft">保存草稿</el-button>
        <el-button type="primary" @click="publish">发布</el-button>
      </div>
    </div>

    <div class="editor-container">
      <el-input
        v-model="article.title"
        placeholder="请输入文章标题"
        size="large"
        class="title-input"
      />

      <div class="editor-wrapper">
        <textarea
          v-model="article.content"
          placeholder="请输入文章内容..."
          class="content-editor"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useArticleStore } from '@/stores/modules/article'

const router = useRouter()
const route = useRoute()
const articleStore = useArticleStore()

const article = ref({
  title: '',
  content: '',
  tags: '',
  category: '',
})

onMounted(async () => {
  const id = route.params.id as string
  if (id && id !== 'add') {
    await articleStore.loadArticleDetail(Number(id))
    if (articleStore.currentArticle.id) {
      article.value = { ...articleStore.currentArticle }
    }
  }
})

const saveDraft = async () => {
  if (!article.value.title) {
    ElMessage.warning('请输入标题')
    return
  }
  const result = await articleStore.createArticle({ ...article.value, status: 0 })
  if (result.success) {
    ElMessage.success('保存成功')
    router.push('/articles')
  }
}

const publish = async () => {
  if (!article.value.title || !article.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  const result = await articleStore.createArticle({ ...article.value, status: 1 })
  if (result.success) {
    ElMessage.success('发布成功')
    router.push('/articles')
  }
}
</script>

<style scoped lang="scss">
.article-edit-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}

.editor-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;

  .title-input {
    :deep(.el-input__wrapper) {
      background: transparent;
      border: none;
      border-bottom: 2px solid var(--border);
      border-radius: 0;
      padding: 12px 0;

      input {
        font-size: 24px;
        font-weight: 500;
      }
    }
  }

  .editor-wrapper {
    flex: 1;
    background: var(--bg-secondary);
    border-radius: 12px;
    padding: 20px;
    overflow: hidden;

    .content-editor {
      width: 100%;
      height: 100%;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-primary);
      font-size: 16px;
      line-height: 1.8;
      resize: none;
      font-family: inherit;
    }
  }
}
</style>
