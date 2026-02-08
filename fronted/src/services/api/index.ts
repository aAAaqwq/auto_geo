/**
 * API 服务 - 完整加固版 v2.2
 * 修复记录：
 * 1. 补全 accountApi.delete (修复删除账号报错)
 * 2. 补全 accountApi.getAuthStatus (修复授权轮询报错)
 * 3. 补全 accountApi.update (修复编辑账号功能)
 * 4. 保持了 reportsApi 和 geoArticleApi 的正确命名
 */

import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// API 基础地址
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api'

/**
 * 创建 axios 实例
 */
const instance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 300000, // 增加到5分钟超时，适应AI检测的长耗时
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 响应拦截器
 */
instance.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token
    return config
  },
  (error) => Promise.reject(error)
)

instance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    console.error('响应错误:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || error.message || '请求失败'
    
    // 如果是 500 错误，在控制台详细打印以便调试
    if (error.response?.status === 500) {
        console.error("🚨 后端 500 错误详情:", error.response.data);
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 通用请求方法封装
export const request = async <T = any>(config: AxiosRequestConfig): Promise<T> => {
  return instance.request(config) as Promise<T>
}

export const get = <T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'GET', url, params, ...config })
}

export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'POST', url, data, ...config })
}

export const put = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'PUT', url, data, ...config })
}

export const del = <T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'DELETE', url, params, ...config })
}

// ==================== 1. 账号管理 API (重点修复区域) ====================
export const accountApi = {
  // 获取列表
  getList: (params?: any) => get('/accounts', params),
  
  // 发起授权 (启动浏览器)
  startAuth: (data: any) => post('/accounts/auth/start', data),
  
  // 🌟 [新增] 查询授权状态 (AccountList.vue 轮询需要)
  getAuthStatus: (taskId: string) => get(`/accounts/auth/status/${taskId}`),
  
  // 🌟 [新增] 更新账号备注/名称
  update: (id: number, data: any) => put(`/accounts/${id}`, data),
  
  // 🌟 [新增] 删除账号 (修复之前的报错)
  delete: (id: number) => del(`/accounts/${id}`)
}

// ==================== 2. GEO 关键词 API ====================
export const geoKeywordApi = {
  getProjects: () => get('/keywords/projects'),
  getProject: (id: number) => get(`/keywords/projects/${id}`),
  getProjectKeywords: (projectId: number) => get(`/keywords/projects/${projectId}/keywords`),
  
  createProject: (data: any) => post('/keywords/projects', data),
  createKeyword: (projectId: number, data: any) => post(`/keywords/projects/${projectId}/keywords`, data),
  
  distill: (data: any) => post('/keywords/distill', data),
  generateQuestions: (data: any) => post('/keywords/generate-questions', data)
}

// ==================== 3. GEO 文章 API ====================
export const geoArticleApi = {
  // 获取文章列表 (对应 Articles.vue)
  getArticles: (params?: any) => get('/geo/articles', params),
  
  // 生成文章 (5分钟超时)
  generate: (data: { keyword_id: number; platform: string; company_name?: string }) => 
    post('/geo/generate', data, { timeout: 300000 }),
    
  // 质检
  checkQuality: (id: number) => post(`/geo/articles/${id}/check-quality`),
  
  // 手动检测收录状态
  checkIndex: (id: number) => post(`/geo/articles/${id}/check-index`),
    
  getDetail: (id: number) => get(`/geo/articles/${id}`),
  delete: (id: number) => del(`/geo/articles/${id}`)
}

// ==================== 4. 收录检测 API (监控页) ====================
export const indexCheckApi = {
  // 执行收录检测
  checkKeyword: (data: { keyword_id: number; company_name: string; platforms?: string[] }) =>
    post<any>('/index-check/check', data),

  // 批量检测
  batchCheck: (data: { project_id?: number; keyword_ids?: number[]; company_name?: string }) =>
    post<any>('/index-check/batch/check', data),

  // 获取检测记录
  getRecords: (params?: {
    keyword_id?: number
    platform?: string
    limit?: number
    skip?: number
    keyword_found?: boolean
    company_found?: boolean
    start_date?: string
    end_date?: string
    question?: string
  }) => get<any>('/index-check/records', params),

  // 删除单条记录
  deleteRecord: (id: number) => del<any>(`/index-check/records/${id}`),

  // 批量删除记录
  batchDeleteRecords: (recordIds: number[]) => post<any>('/index-check/records/batch-delete', { record_ids: recordIds }),

  // 获取关键词趋势
  getKeywordTrend: (keywordId: number, days?: number) =>
    get<any>(`/index-check/keywords/${keywordId}/trend`, { days }),

  // 获取项目统计
  getProjectStats: (projectId: number) => get<any>(`/index-check/projects/${projectId}/analytics`),

  // 兼容 Monitor.vue 的 runCheck
  check: (data: { keyword_id: number; company_name: string; platforms?: string[] }) => 
    post('/index-check/check', data),
  
  getTrend: (keywordId: number, days = 7) => get(`/index-check/trend/${keywordId}`, { days })
}

// ==================== 5. 报表 API ====================
export const reportsApi = {
  // 获取总览数据
  getOverview: () => get<any>('/reports/overview'),

  // 获取收录趋势
  getIndexTrend: (params?: { project_id?: number; days?: number; platform?: string }) =>
    get<any>('/reports/trends', params),

  // 获取平台分布
  getPlatformDistribution: (params?: { project_id?: number }) =>
    get<any>('/reports/distribution/platform', params),

  // 获取关键词排名
  getKeywordRanking: (params?: { project_id?: number; limit?: number }) =>
    get<any>('/reports/ranking/keywords', params),

  // 获取项目统计
  getProjectStats: (projectId: number) => get<any>(`/reports/stats/project/${projectId}`),

  // 趋势图数据 (Monitor.vue 使用)
  getTrends: (days: number = 30) => get('/reports/trends', { days }),
  
  // 🌟 [新增] 数据总览卡片
  getStats: (params: { project_id?: number; days?: number }) => get('/reports/stats', params),
  
  // 🌟 [新增] AI 平台对比分析
  getPlatformComparison: (params: { project_id?: number; days?: number }) => get('/reports/platform-comparison', params),
  
  // 🌟 [新增] 项目影响力排行榜
  getProjectLeaderboard: (params: { days?: number }) => get('/reports/project-leaderboard', params),
  
  // 🌟 [新增] 高贡献内容分析
  getContentAnalysis: (params: { project_id?: number; days?: number }) => get('/reports/content-analysis', params)
}

// ==================== 6. 定时任务 API ====================
export const schedulerApi = {
  getJobs: () => get('/scheduler/jobs'),
  start: () => post('/scheduler/start', {}),
  stop: () => post('/scheduler/stop', {})
}

// 导出统一的api对象
export const api = {
  account: accountApi,
  geoKeyword: geoKeywordApi,
  geoArticle: geoArticleApi,
  indexCheck: indexCheckApi,
  reports: reportsApi,
  scheduler: schedulerApi
}

// 导出默认实例
export default instance
