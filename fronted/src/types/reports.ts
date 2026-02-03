/**
 * 数据报表相关类型定义
 */

// 漏斗图数据
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

// KPI卡片数据
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

// 文章统计数据
export interface ArticleStats {
  total_articles: number
  published_count: number
  indexed_count: number
  index_rate: number
  platform_distribution: Record<string, number>
}

// 综合概览数据
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

// 趋势数据点
export interface DailyTrendPoint {
  date: string
  articles_generated: number
  articles_published: number
  publish_success: number
  index_checks: number
  keyword_hits: number
}

// 平台对比数据
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

// 项目对比数据
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

// TOP项目
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

// TOP文章
export interface TopArticle {
  article_id: number
  title: string
  platform: string
  created_at: string
  keyword_hit_rate: number
  last_check_status: boolean
}