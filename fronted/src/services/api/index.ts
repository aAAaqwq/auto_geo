/**
 * API 服务
 * 老王我用这个来封装所有 HTTP 请求！
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
