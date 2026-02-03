/**
 * 全局类型定义
 * 我用这个来统一管理所有类型！
 */

// ==================== 平台相关 ====================

export type PlatformId = 'zhihu' | 'baijiahao' | 'sohu' | 'toutiao'

export interface PlatformConfig {
  id: PlatformId
  name: string
  code: string
  color: string
}

// ==================== 账号相关 ====================

export interface Account {
  id: number
  platform: PlatformId
  account_name: string
  username?: string
  status: AccountStatus
  last_auth_time?: string
  remark?: string
  created_at: string
  updated_at: string
}

export enum AccountStatus {
  DISABLED = 0,
  ACTIVE = 1,
  EXPIRED = -1,
}

// ==================== 文章相关 ====================

export interface Article {
  id: number
  title: string
  content: string
  tags?: string
  category?: string
  cover_image?: string
  status: ArticleStatus
  view_count: number
  created_at: string
  updated_at: string
  published_at?: string
}

export enum ArticleStatus {
  DRAFT = 0,
  PUBLISHED = 1,
}

// ==================== 发布相关 ====================

export interface PublishTask {
  id: string
  articleId: number
  articleTitle: string
  accountId: number
  accountName: string
  platform: PlatformId
  platformName: string
  status: PublishStatus
  platformUrl?: string
  errorMsg?: string
}

export enum PublishStatus {
  PENDING = 0,
  PUBLISHING = 1,
  SUCCESS = 2,
  FAILED = 3,
}

export interface PublishRecord {
  id: number
  articleId: number
  articleTitle: string
  accountId: number
  accountName: string
  platform: PlatformId
  platformName: string
  status: PublishStatus
  platformUrl?: string
  errorMsg?: string
  retryCount: number
  createdAt: string
  publishedAt?: string
}

// ==================== API 响应相关 ====================

export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  timestamp?: string
}

export interface PaginatedResponse<T> {
  total: number
  items: T[]
  page?: number
  pageSize?: number
}

// ==================== 授权相关 ====================

export interface AuthResult {
  taskId: string
  status: 'pending' | 'success' | 'failed' | 'timeout'
  isLoggedIn?: boolean
  message?: string
}

// ==================== WebSocket 相关 ====================

export interface WSMessage {
  type: 'publish_progress' | 'publish_complete' | 'auth_complete'
  data: any
}

export interface PublishProgressMessage {
  taskId: string
  articleId: number
  articleTitle: string
  accountId: number
  accountName: string
  platform: PlatformId
  platformName: string
  status: PublishStatus
  errorMsg?: string
  platformUrl?: string
}

// ==================== 表单相关 ====================

export interface AccountFormData {
  platform: PlatformId
  account_name: string
  remark?: string
}

export interface ArticleFormData {
  title: string
  content: string
  tags?: string
  category?: string
  cover_image?: string
}

// ==================== 报表相关 ====================

export interface ComprehensiveOverview {
  total_articles: number
  total_geo_articles: number
  total_articles_generated: number
  geo_articles_passed: number
  geo_articles_failed: number
  total_publish_records: number
  publish_success: number
  publish_failed: number
  publish_pending: number
  publish_success_rate: number
  total_checks: number
  keyword_found: number
  company_found: number
  keyword_hit_rate: number
  company_hit_rate: number
  total_projects: number
  total_keywords: number
  active_keywords: number
}

export interface DailyTrendPoint {
  date: string
  articles_generated: number
  articles_published: number
  publish_success: number
  index_checks: number
  keyword_hits: number
}

export interface PlatformDailyData {
  date: string
  total_checks: number
  keyword_hits: number
  hit_rate: number
}

export interface PlatformComparison {
  platform: string
  platform_name: string
  daily_data: PlatformDailyData[]
}

export interface ProjectDailyData {
  date: string
  total_checks: number
  keyword_hits: number
  hit_rate: number
}

export interface ProjectComparison {
  project_id: number
  project_name: string
  company_name: string
  daily_data: ProjectDailyData[]
}

export interface TopProject {
  project_id: number
  project_name: string
  company_name: string
  total_keywords: number
  total_checks: number
  keyword_hit_rate: number
  company_hit_rate: number
  total_articles: number
  total_publish: number
}

export interface TopArticle {
  article_id: number
  title: string
  platform: string
  created_at: string
  keyword_hit_rate: number
  last_check_status: boolean
}

// ==================== 新增：数据报表相关类型 ====================

export interface FunnelDataItem {
  name: string
  value: number
}

export interface FunnelConversionRates {
  quality_rate: number
  publish_rate: number
  index_rate: number
  overall_rate: number
}

export interface FunnelSummary {
  generated: number
  published: number
  indexed: number
  period_days: number
}

export interface FunnelData {
  funnel_data: FunnelDataItem[]
  conversion_rates: FunnelConversionRates
  summary: FunnelSummary
}

export interface KPICardArticleGeneration {
  total: number
  today: number
  this_week: number
  unit: string
}

export interface KPICardPublishing {
  total_published: number
  publish_rate: number
  unit: string
}

export interface KPICardIndexing {
  total_indexed: number
  index_rate: number
  unit: string
}

export interface KPICardProjectsKeywords {
  total_projects: number
  total_keywords: number
  active_keywords: number
}

export interface KPIData {
  article_generation: KPICardArticleGeneration
  publishing: KPICardPublishing
  indexing: KPICardIndexing
  projects_keywords: KPICardProjectsKeywords
  platform_distribution: Record<string, number>
  update_time: string
}

export interface ArticleStats {
  total_articles: number
  published_count: number
  indexed_count: number
  index_rate: number
  platform_distribution: Record<string, number>
}

// ==================== 路由相关 ====================

export interface RouteMeta {
  title?: string
  icon?: string
  hidden?: boolean
}

// 导出报表相关类型
export * from './reports'
