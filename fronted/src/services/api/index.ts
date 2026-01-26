/**
 * API 服务
 * 我用这个来封装所有 HTTP 请求！
 */

import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// API 基础地址
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

/**
 * 创建 axios 实例
 */
const instance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 请求拦截器
 */
instance.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 */
instance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    console.error('响应错误:', error)

    const message = error.response?.data?.message || error.message || '请求失败'

    // 不显示某些错误的提示
    if (error.config?.skipErrorNotification) {
      return Promise.reject(error)
    }

    ElMessage.error(message)

    return Promise.reject(error)
  }
)

/**
 * 通用请求方法
 */
export const request = async <T = any>(config: AxiosRequestConfig): Promise<T> => {
  return instance.request(config) as Promise<T>
}

/**
 * GET 请求
 */
export const get = <T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'GET', url, params, ...config })
}

/**
 * POST 请求
 */
export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'POST', url, data, ...config })
}

/**
 * PUT 请求
 */
export const put = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'PUT', url, data, ...config })
}

/**
 * DELETE 请求
 */
export const del = <T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'DELETE', url, params, ...config })
}

// ==================== 账号 API ====================

export const accountApi = {
  // 获取账号列表
  getList: (params?: { platform?: string }) => get<any>('/accounts', params),

  // 获取账号详情
  getDetail: (id: number) => get<any>(`/accounts/${id}`),

  // 创建账号
  create: (data: { platform: string; account_name: string; remark?: string }) =>
    post<any>('/accounts', data),

  // 更新账号
  update: (id: number, data: any) => put<any>(`/accounts/${id}`, data),

  // 删除账号
  delete: (id: number) => del<any>(`/accounts/${id}`),

  // 开始授权
  startAuth: (data: { platform: string; account_id?: number; account_name?: string }) =>
    post<any>('/accounts/auth/start', data),

  // 查询授权状态
  getAuthStatus: (taskId: string) => get<any>(`/accounts/auth/status/${taskId}`),

  // 保存授权结果
  saveAuth: (taskId: string) => post<any>(`/accounts/auth/save/${taskId}`),

  // 取消授权任务
  cancelAuth: (taskId: string) => del<any>(`/accounts/auth/task/${taskId}`),
}

// ==================== 文章 API ====================

export const articleApi = {
  // 获取文章列表
  getList: (params?: {
    skip?: number
    limit?: number
    status?: number
    keyword?: string
  }) => get<any>('/articles', params),

  // 获取文章详情
  getDetail: (id: number) => get<any>(`/articles/${id}`),

  // 创建文章
  create: (data: {
    title: string
    content: string
    tags?: string
    category?: string
    cover_image?: string
  }) => post<any>('/articles', data),

  // 更新文章
  update: (id: number, data: any) => put<any>(`/articles/${id}`, data),

  // 删除文章
  delete: (id: number) => del<any>(`/articles/${id}`),
}

// ==================== 发布 API ====================

export const publishApi = {
  // 创建发布任务
  createTask: (data: { article_ids: number[]; account_ids: number[] }) =>
    post<any>('/publish/create', data),

  // 获取发布进度
  getProgress: (taskId: string) => get<any>(`/publish/progress/${taskId}`),

  // 获取发布记录
  getRecords: (params?: {
    article_id?: number
    account_id?: number
    limit?: number
    offset?: number
  }) => get<any>('/publish/records', params),

  // 重试发布
  retry: (recordId: number) => post<any>(`/publish/retry/${recordId}`),

  // 获取支持的平台
  getPlatforms: () => get<any>('/publish/platforms'),
}

// ==================== 平台 API ====================

export const platformApi = {
  // 获取平台列表
  getList: () => get<any>('/platforms'),
}

// 导出实例
export default instance

// ==================== GEO关键词 API ====================
// 注意：后端路由是 /api/keywords/*，不是 /geo/*

export const geoKeywordApi = {
  // 获取项目列表
  getProjects: () => get<any>('/keywords/projects'),

  // 获取项目详情
  getProject: (id: number) => get<any>(`/keywords/projects/${id}`),

  // 创建项目
  createProject: (data: {
    name: string
    company_name: string
    domain_keyword?: string
    industry?: string
    description?: string
  }) => post<any>('/keywords/projects', data),

  // 更新项目
  updateProject: (id: number, data: any) => put<any>(`/keywords/projects/${id}`, data),

  // 删除项目
  deleteProject: (id: number) => del<any>(`/keywords/projects/${id}`),

  // 获取项目关键词
  getProjectKeywords: (projectId: number) => get<any>(`/keywords/projects/${projectId}/keywords`),

  // 创建关键词
  createKeyword: (projectId: number, data: { keyword: string; difficulty_score?: number }) =>
    post<any>(`/keywords/projects/${projectId}/keywords`, data),

  // 删除关键词
  deleteKeyword: (keywordId: number) => del<any>(`/keywords/keywords/${keywordId}`),

  // 关键词蒸馏
  distill: (data: {
    project_id: number
    company_name: string
    industry?: string
    description?: string
    count?: number
  }) => post<any>('/keywords/distill', data),

  // 生成问题变体
  generateQuestions: (data: { keyword_id: number; count?: number }) =>
    post<any>('/keywords/generate-questions', data),

  // 获取关键词问题
  getKeywordQuestions: (keywordId: number) => get<any>(`/keywords/keywords/${keywordId}/questions`),

  // 删除问题变体
  deleteQuestion: (questionId: number) => del<any>(`/keywords/questions/${questionId}`),
}

// ==================== GEO文章 API ====================

export const geoArticleApi = {
  // 获取GEO文章列表
  getList: (params?: { project_id?: number; keyword_id?: number; status?: string; limit?: number; offset?: number }) =>
    get<any>('/geo/articles', params),

  // 获取文章详情
  getDetail: (id: number) => get<any>(`/geo/articles/${id}`),

  // 创建GEO文章
  create: (data: {
    project_id: number
    keyword_id: number
    title: string
    content: string
    platform_tags?: string
  }) => post<any>('/geo/articles', data),

  // 更新文章
  update: (id: number, data: any) => put<any>(`/geo/articles/${id}`, data),

  // 删除文章
  delete: (id: number) => del<any>(`/geo/articles/${id}`),

  // 批量生成文章
  batchGenerate: (data: { project_id: number; keyword_ids?: number[]; count_per_keyword?: number }) =>
    post<any>('/geo/articles/batch-generate', data),

  // 发布文章
  publish: (articleId: number, data: { platform: string; account_id?: number }) =>
    post<any>(`/geo/articles/${articleId}/publish`, data),

  // 获取发布状态
  getPublishStatus: (articleId: number) => get<any>(`/geo/articles/${articleId}/publish-status`),
}

// ==================== 收录检测 API ====================

export const indexCheckApi = {
  // 执行收录检测
  checkKeyword: (data: { keyword_id: number; company_name: string }) =>
    post<any>('/index-check/check', data),

  // 批量检测
  batchCheck: (data: { project_id?: number; keyword_ids?: number[]; company_name?: string }) =>
    post<any>('/index-check/batch-check', data),

  // 获取检测记录
  getRecords: (params?: {
    keyword_id?: number
    project_id?: number
    platform?: string
    limit?: number
    offset?: number
  }) => get<any>('/index-check/records', params),

  // 获取关键词趋势
  getKeywordTrend: (keywordId: number, days?: number) =>
    get<any>(`/index-check/trend/${keywordId}`, { days }),

  // 获取项目统计
  getProjectStats: (projectId: number) => get<any>(`/index-check/stats/project/${projectId}`),
}

// ==================== 报表 API ====================

export const reportsApi = {
  // 获取总览数据
  getOverview: () => get<any>('/reports/overview'),

  // 获取全面数据概览（新增：包含文章、发布、收录等）
  getComprehensiveOverview: (params?: { project_id?: number }) =>
    get<any>('/reports/comprehensive', params),

  // 获取每日趋势数据（新增：包含文章生成、发布、收录趋势）
  getDailyTrends: (params?: { project_id?: number; days?: number }) =>
    get<any>('/reports/daily-trends', params),

  // 获取收录趋势
  getIndexTrend: (params?: { project_id?: number; days?: number }) =>
    get<any>('/reports/trend/index', params),

  // 获取平台分布
  getPlatformDistribution: (params?: { project_id?: number }) =>
    get<any>('/reports/distribution/platform', params),

  // 获取关键词排名
  getKeywordRanking: (params?: { project_id?: number; limit?: number }) =>
    get<any>('/reports/ranking/keywords', params),

  // 获取项目统计
  getProjectStats: (projectId: number) => get<any>(`/reports/stats/project/${projectId}`),

  // 获取平台对比分析（新增）
  getPlatformComparison: (params?: { project_id?: number; days?: number }) =>
    get<any>('/reports/platform-comparison', params),

  // 获取项目对比分析（新增）
  getProjectComparison: (params?: { project_ids?: string; days?: number }) =>
    get<any>('/reports/project-comparison', params),

  // 获取TOP项目排行榜（新增）
  getTopProjects: (params?: { project_id?: number; limit?: number }) =>
    get<any>('/reports/top-projects', params),
}

// ==================== 预警通知 API ====================

export const notificationApi = {
  // 检查预警
  checkAlerts: (params?: { project_id?: number }) => post<any>('/notifications/check', params),

  // 获取预警汇总
  getSummary: () => get<any>('/notifications/summary'),

  // 获取预警规则
  getRules: () => get<any>('/notifications/rules'),

  // 测试预警
  testAlert: () => post<any>('/notifications/trigger-test', {}),
}

// ==================== 定时任务 API ====================

export const schedulerApi = {
  // 获取定时任务列表
  getJobs: () => get<any>('/scheduler/jobs'),

  // 获取服务状态
  getStatus: () => get<any>('/scheduler/status'),

  // 启动服务
  start: () => post<any>('/scheduler/start', {}),

  // 停止服务
  stop: () => post<any>('/scheduler/stop', {}),

  // 触发收录检测
  triggerCheck: () => post<any>('/scheduler/trigger-check', {}),

  // 触发预警检查
  triggerAlert: () => post<any>('/scheduler/trigger-alert', {}),
}
