/**
 * 文章状态管理
 * 老王我用这个来管理文章状态！
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Article {
  id: number
  title: string
  content: string
  tags?: string
  category?: string
  cover_image?: string
  status: number
  view_count: number
  created_at: string
  updated_at: string
  published_at?: string
}

export const useArticleStore = defineStore('article', () => {
  // ==================== 状态 ====================

  /** 文章列表 */
  const articles = ref<Article[]>([])

  /** 当前选中的文章ID列表 */
  const selectedArticleIds = ref<number[]>([])

  /** 当前编辑的文章 */
  const currentArticle = ref<Partial<Article>>({})

  /** 加载状态 */
  const loading = ref(false)

  /** 错误信息 */
  const error = ref<string | null>(null)

  /** 分页信息 */
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0,
  })

  // ==================== 计算属性 ====================

  /** 草稿文章 */
  const draftArticles = computed(() => {
    return articles.value.filter(art => art.status === 0)
  })

  /** 已发布文章 */
  const publishedArticles = computed(() => {
    return articles.value.filter(art => art.status === 1)
  })

  /** 获取文章总数 */
  const totalCount = computed(() => pagination.value.total)

  /** 获取当前选中的文章 */
  const selectedArticles = computed(() => {
    return articles.value.filter(art => selectedArticleIds.value.includes(art.id))
  })

  // ==================== 操作 ====================

  /**
   * 加载文章列表
   * 老王我tm从后端获取文章列表！
   */
  async function loadArticles(params: {
    page?: number
    pageSize?: number
    status?: number
    keyword?: string
  } = {}) {
    loading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()
      if (params.page) queryParams.append('skip', String((params.page - 1) * (params.pageSize || 20)))
      if (params.pageSize) queryParams.append('limit', String(params.pageSize))
      if (params.status !== undefined) queryParams.append('status', String(params.status))
      if (params.keyword) queryParams.append('keyword', params.keyword)

      const url = `/api/articles?${queryParams.toString()}`
      const response = await fetch(url)
      const data = await response.json()

      if (data.success !== false) {
        articles.value = data.items || data.data || []
        pagination.value.total = data.total || articles.value.length
        pagination.value.page = params.page || 1
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
   * 加载文章详情
   */
  async function loadArticleDetail(id: number) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/articles/${id}`)
      const data = await response.json()

      if (data.success !== false) {
        currentArticle.value = data.data || data
        return { success: true, data: currentArticle.value }
      } else {
        error.value = data.message || '加载失败'
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
   * 创建文章
   */
  async function createArticle(articleData: Partial<Article>) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/articles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(articleData),
      })
      const data = await response.json()

      if (data.success !== false) {
        const newArticle = data.data || data
        articles.value.unshift(newArticle)
        return { success: true, data: newArticle }
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
   * 更新文章
   */
  async function updateArticle(id: number, articleData: Partial<Article>) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/articles/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(articleData),
      })
      const data = await response.json()

      if (data.success !== false) {
        const index = articles.value.findIndex(art => art.id === id)
        if (index !== -1) {
          articles.value[index] = { ...articles.value[index], ...data.data }
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
   * 删除文章
   */
  async function deleteArticle(id: number) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/articles/${id}`, {
        method: 'DELETE',
      })
      const data = await response.json()

      if (data.success !== false) {
        articles.value = articles.value.filter(art => art.id !== id)
        selectedArticleIds.value = selectedArticleIds.value.filter(sid => sid !== id)
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
   * 切换文章选中状态
   */
  function toggleArticleSelection(id: number) {
    const index = selectedArticleIds.value.indexOf(id)
    if (index === -1) {
      selectedArticleIds.value.push(id)
    } else {
      selectedArticleIds.value.splice(index, 1)
    }
  }

  /**
   * 全选/取消全选
   */
  function toggleSelectAll() {
    const allSelected = articles.value.every(art =>
      selectedArticleIds.value.includes(art.id)
    )

    if (allSelected) {
      selectedArticleIds.value = []
    } else {
      selectedArticleIds.value = articles.value.map(art => art.id)
    }
  }

  /**
   * 清空选择
   */
  function clearSelection() {
    selectedArticleIds.value = []
  }

  /**
   * 设置当前编辑的文章
   */
  function setCurrentArticle(article: Partial<Article>) {
    currentArticle.value = { ...article }
  }

  /**
   * 重置当前编辑的文章
   */
  function resetCurrentArticle() {
    currentArticle.value = {}
  }

  return {
    // 状态
    articles,
    selectedArticleIds,
    currentArticle,
    loading,
    error,
    pagination,

    // 计算属性
    draftArticles,
    publishedArticles,
    totalCount,
    selectedArticles,

    // 操作
    loadArticles,
    loadArticleDetail,
    createArticle,
    updateArticle,
    deleteArticle,
    toggleArticleSelection,
    toggleSelectAll,
    clearSelection,
    setCurrentArticle,
    resetCurrentArticle,
  }
})
