<template>
  <div class="enhanced-reports-page">
    <!-- 顶部筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select
          v-model="selectedProjectId"
          placeholder="选择项目"
          clearable
          filterable
          style="width: 200px"
          @change="handleProjectChange"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
        <el-select
          v-model="selectedDays"
          style="width: 120px; margin-left: 12px"
          @change="handleDaysChange"
        >
          <el-option label="近7天" :value="7" />
          <el-option label="近30天" :value="30" />
          <el-option label="近90天" :value="90" />
        </el-select>
      </div>
      <div class="filter-right">
        <el-button type="primary" @click="exportData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
        <el-button style="margin-left: 12px" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- KPI 卡片区域 -->
    <div class="kpi-section">
      <div class="section-header">
        <h2 class="section-title">核心指标</h2>
        <span class="update-time">更新时间: {{ formatTime(kpiData.update_time) }}</span>
      </div>
      <div class="kpi-grid">
        <!-- 文章生成卡片 -->
        <div class="kpi-card card-blue">
          <div class="kpi-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="kpi-content">
            <div class="kpi-label">文章生成总数</div>
            <div class="kpi-value">{{ kpiData.article_generation?.total || 0 }}</div>
            <div class="kpi-sub">
              <span class="highlight">今日 +{{ kpiData.article_generation?.today || 0 }}</span>
              <span>本周 {{ kpiData.article_generation?.this_week || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- 发布成功卡片 -->
        <div class="kpi-card card-green">
          <div class="kpi-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="kpi-content">
            <div class="kpi-label">发布成功率</div>
            <div class="kpi-value">{{ kpiData.publishing?.publish_rate || 0 }}%</div>
            <div class="kpi-sub">
              <span>已发布 {{ kpiData.publishing?.total_published || 0 }} 篇</span>
            </div>
          </div>
        </div>

        <!-- 收录命中卡片 -->
        <div class="kpi-card card-orange">
          <div class="kpi-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="kpi-content">
            <div class="kpi-label">收录命中率</div>
            <div class="kpi-value">{{ kpiData.indexing?.index_rate || 0 }}%</div>
            <div class="kpi-sub">
              <span>已收录 {{ kpiData.indexing?.total_indexed || 0 }} 篇</span>
            </div>
          </div>
        </div>

        <!-- 项目关键词卡片 -->
        <div class="kpi-card card-purple">
          <div class="kpi-icon">
            <el-icon><Collection /></el-icon>
          </div>
          <div class="kpi-content">
            <div class="kpi-label">项目/关键词</div>
            <div class="kpi-value">{{ kpiData.projects_keywords?.total_projects || 0 }}/{{ kpiData.projects_keywords?.total_keywords || 0 }}</div>
            <div class="kpi-sub">
              <span>活跃关键词 {{ kpiData.projects_keywords?.active_keywords || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 转化漏斗图 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><Filter /></el-icon>
            转化漏斗分析
          </h3>
          <div class="chart-actions">
            <el-tag type="info" size="small">近{{ selectedDays }}天</el-tag>
          </div>
        </div>
        <div ref="funnelChartRef" class="chart-container"></div>
        <div class="funnel-stats" v-if="funnelData.conversion_rates">
          <div class="stat-item">
            <span class="stat-label">质检通过率</span>
            <span class="stat-value">{{ funnelData.conversion_rates.quality_rate }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">发布转化率</span>
            <span class="stat-value">{{ funnelData.conversion_rates.publish_rate }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">收录转化率</span>
            <span class="stat-value">{{ funnelData.conversion_rates.index_rate }}%</span>
          </div>
          <div class="stat-item highlight">
            <span class="stat-label">总转化率</span>
            <span class="stat-value">{{ funnelData.conversion_rates.overall_rate }}%</span>
          </div>
        </div>
      </div>

      <!-- 平台对比分析 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><Platform /></el-icon>
            AI平台收录对比
          </h3>
          <div class="chart-actions">
            <el-radio-group v-model="platformMetric" size="small">
              <el-radio-button label="hit_rate">命中率</el-radio-button>
              <el-radio-button label="count">检测数</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div ref="platformChartRef" class="chart-container"></div>
      </div>

      <!-- 综合趋势分析 -->
      <div class="chart-card full-width">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><TrendCharts /></el-icon>
            综合趋势分析
          </h3>
          <div class="chart-actions">
            <el-check-tag 
              v-for="metric in trendMetrics" 
              :key="metric.key"
              :checked="selectedTrendMetrics.includes(metric.key)"
              @change="toggleTrendMetric(metric.key)"
              class="metric-tag"
            >
              {{ metric.label }}
            </el-check-tag>
          </div>
        </div>
        <div ref="trendChartRef" class="chart-container large"></div>
      </div>
    </div>

    <!-- 数据表格区域 -->
    <div class="tables-section">
      <!-- 项目排行榜 -->
      <div class="table-card">
        <div class="table-header">
          <h3 class="table-title">
            <el-icon><Trophy /></el-icon>
            项目影响力排行榜
          </h3>
          <el-link type="primary" @click="viewAllProjects">查看全部</el-link>
        </div>
        <el-table
          v-loading="loading"
          :data="topProjects"
          stripe
          style="width: 100%"
        >
          <el-table-column type="index" label="排名" width="60">
            <template #default="{ $index }">
              <div class="rank-cell" :class="getRankClass($index)">
                {{ $index + 1 }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="project_name" label="品牌/项目" min-width="150">
            <template #default="{ row }">
              <div class="project-cell">
                <span class="project-name">{{ row.project_name }}</span>
                <span class="company-name">{{ row.company_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="total_articles" label="内容声量" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.total_articles }} 篇</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="keyword_hit_rate" label="AI提及率" width="120">
            <template #default="{ row }">
              <div class="rate-cell" :class="getRateClass(row.keyword_hit_rate)">
                <el-progress 
                  :percentage="row.keyword_hit_rate" 
                  :color="getRateColor(row.keyword_hit_rate)"
                  :show-text="false"
                  :stroke-width="8"
                />
                <span class="rate-value">{{ row.keyword_hit_rate }}%</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="company_hit_rate" label="品牌关联度" width="120">
            <template #default="{ row }">
              <div class="rate-cell" :class="getRateClass(row.company_hit_rate)">
                <el-progress 
                  :percentage="row.company_hit_rate" 
                  :color="getRateColor(row.company_hit_rate)"
                  :show-text="false"
                  :stroke-width="8"
                />
                <span class="rate-value">{{ row.company_hit_rate }}%</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { 
  Refresh, Download, Document, CircleCheck, TrendCharts, 
  Collection, Filter, Platform, Trophy, InfoFilled 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { reportsApi, geoKeywordApi } from '@/services/api'
import { ElMessage } from 'element-plus'
import type { 
  FunnelData, KPIData, TopProject, PlatformComparison, 
  ProjectComparison, DailyTrendPoint 
} from '@/types'

// 数据
const loading = ref(false)
const selectedProjectId = ref<number | null>(null)
const selectedDays = ref(30)
const platformMetric = ref('hit_rate')
const selectedTrendMetrics = ref(['articles_generated', 'keyword_hits'])

const projects = ref<any[]>([])
const kpiData = ref<Partial<KPIData>>({})
const funnelData = ref<Partial<FunnelData>>({})
const platformComparison = ref<PlatformComparison[]>([])
const projectComparison = ref<ProjectComparison[]>([])
const dailyTrends = ref<DailyTrendPoint[]>([])
const topProjects = ref<TopProject[]>([])

// 趋势指标选项
const trendMetrics = [
  { key: 'articles_generated', label: '文章生成' },
  { key: 'articles_published', label: '发布数量' },
  { key: 'publish_success', label: '发布成功' },
  { key: 'index_checks', label: '检测次数' },
  { key: 'keyword_hits', label: '关键词命中' },
]

// 图表引用
const funnelChartRef = ref<HTMLDivElement | null>(null)
const platformChartRef = ref<HTMLDivElement | null>(null)
const trendChartRef = ref<HTMLDivElement | null>(null)
let funnelChart: echarts.ECharts | null = null
let platformChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

// 加载项目列表
const loadProjects = async () => {
  try {
    const result = await geoKeywordApi.getProjects()
    projects.value = result || []
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

// 加载KPI数据
const loadKpiData = async () => {
  try {
    const params: any = {}
    if (selectedProjectId.value) {
      params.project_id = selectedProjectId.value
    }
    const result = await reportsApi.getKpiCards(params)
    kpiData.value = result || {}
  } catch (error) {
    console.error('加载KPI数据失败:', error)
  }
}

// 加载漏斗数据
const loadFunnelData = async () => {
  try {
    const params: any = { days: selectedDays.value }
    if (selectedProjectId.value) {
      params.project_id = selectedProjectId.value
    }
    const result = await reportsApi.getFunnelData(params)
    funnelData.value = result || {}
    updateFunnelChart()
  } catch (error) {
    console.error('加载漏斗数据失败:', error)
  }
}

// 加载平台对比数据
const loadPlatformComparison = async () => {
  try {
    const params: any = { days: selectedDays.value }
    if (selectedProjectId.value) {
      params.project_id = selectedProjectId.value
    }
    const result = await reportsApi.getPlatformComparison(params)
    platformComparison.value = result || []
    updatePlatformChart()
  } catch (error) {
    console.error('加载平台对比数据失败:', error)
  }
}

// 加载每日趋势数据
const loadDailyTrends = async () => {
  try {
    const params: any = { days: selectedDays.value }
    if (selectedProjectId.value) {
      params.project_id = selectedProjectId.value
    }
    const result = await reportsApi.getDailyTrends(params)
    dailyTrends.value = result || []
    updateTrendChart()
  } catch (error) {
    console.error('加载趋势数据失败:', error)
  }
}

// 加载TOP项目
const loadTopProjects = async () => {
  try {
    const params: any = { limit: 10 }
    if (selectedProjectId.value) {
      params.project_id = selectedProjectId.value
    }
    const result = await reportsApi.getTopProjects(params)
    topProjects.value = result || []
  } catch (error) {
    console.error('加载TOP项目失败:', error)
  }
}

// 统一数据加载
const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadKpiData(),
      loadFunnelData(),
      loadPlatformComparison(),
      loadDailyTrends(),
      loadTopProjects()
    ])
  } finally {
    loading.value = false
  }
}

// 筛选变化处理
const handleProjectChange = () => {
  loadData()
}

const handleDaysChange = () => {
  Promise.all([
    loadFunnelData(),
    loadPlatformComparison(),
    loadDailyTrends()
  ])
}

// 切换趋势指标
const toggleTrendMetric = (key: string) => {
  const index = selectedTrendMetrics.value.indexOf(key)
  if (index > -1) {
    if (selectedTrendMetrics.value.length > 1) {
      selectedTrendMetrics.value.splice(index, 1)
    }
  } else {
    selectedTrendMetrics.value.push(key)
  }
  updateTrendChart()
}

// 初始化图表
const initCharts = () => {
  if (funnelChartRef.value) {
    funnelChart = echarts.init(funnelChartRef.value)
  }
  if (platformChartRef.value) {
    platformChart = echarts.init(platformChartRef.value)
  }
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }

  window.addEventListener('resize', () => {
    funnelChart?.resize()
    platformChart?.resize()
    trendChart?.resize()
  })
}

// 更新漏斗图
const updateFunnelChart = () => {
  if (!funnelChart || !funnelData.value.funnel_data) return

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        name: '转化漏斗',
        type: 'funnel',
        left: '10%',
        top: 20,
        bottom: 20,
        width: '80%',
        min: 0,
        max: Math.max(...funnelData.value.funnel_data.map((d: any) => d.value)),
        minSize: '0%',
        maxSize: '100%',
        sort: 'descending',
        gap: 2,
        label: {
          show: true,
          position: 'inside',
          formatter: '{b}\n{c}',
          fontSize: 12
        },
        labelLine: {
          length: 10,
          lineStyle: {
            width: 1,
            type: 'solid'
          }
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1
        },
        emphasis: {
          label: {
            fontSize: 14
          }
        },
        data: funnelData.value.funnel_data
      }
    ],
    color: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C']
  }

  funnelChart.setOption(option)
}

// 更新平台对比图
const updatePlatformChart = () => {
  if (!platformChart || !platformComparison.value.length) return

  const dates = platformComparison.value[0]?.daily_data?.map((item: any) => {
    const date = new Date(item.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }) || []

  const series = platformComparison.value.map((platform: any) => ({
    name: platform.platform_name,
    type: 'line',
    smooth: true,
    data: platform.daily_data.map((item: any) => 
      platformMetric.value === 'hit_rate' ? item.hit_rate : item.total_checks
    ),
    itemStyle: {
      color: getPlatformColor(platform.platform)
    }
  }))

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: platformComparison.value.map((p: any) => p.platform_name),
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value',
      name: platformMetric.value === 'hit_rate' ? '命中率(%)' : '检测数',
      min: 0,
      max: platformMetric.value === 'hit_rate' ? 100 : undefined
    },
    series
  }

  platformChart.setOption(option)
}

// 更新趋势图
const updateTrendChart = () => {
  if (!trendChart || !dailyTrends.value.length) return

  const dates = dailyTrends.value.map((item: any) => {
    const date = new Date(item.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  })

  const metricConfig: any = {
    articles_generated: { label: '生成文章数', color: '#409EFF', type: 'line' },
    articles_published: { label: '发布文章数', color: '#67C23A', type: 'line' },
    publish_success: { label: '发布成功数', color: '#E6A23C', type: 'line' },
    index_checks: { label: '检测次数', color: '#909399', type: 'bar' },
    keyword_hits: { label: '关键词命中', color: '#F56C6C', type: 'line' },
  }

  const series = selectedTrendMetrics.value.map((key: string) => {
    const config = metricConfig[key]
    return {
      name: config.label,
      type: config.type,
      data: dailyTrends.value.map((item: any) => item[key]),
      smooth: true,
      itemStyle: { color: config.color }
    }
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: series.map((s: any) => s.name),
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value',
      name: '数量'
    },
    series
  }

  trendChart.setOption(option)
}

// 获取平台颜色
const getPlatformColor = (platform: string) => {
  const colors: Record<string, string> = {
    doubao: '#FF6B00',
    qianwen: '#409EFF',
    deepseek: '#67C23A'
  }
  return colors[platform] || '#909399'
}

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

// 获取排名样式类
const getRankClass = (index: number) => {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

// 获取命中率样式类
const getRateClass = (rate: number) => {
  if (rate >= 60) return 'rate-high'
  if (rate >= 30) return 'rate-medium'
  return 'rate-low'
}

// 获取命中率颜色
const getRateColor = (rate: number) => {
  if (rate >= 60) return '#67C23A'
  if (rate >= 30) return '#E6A23C'
  return '#F56C6C'
}

// 导出数据
const exportData = () => {
  ElMessage.success('数据导出功能开发中...')
}

// 查看全部项目
const viewAllProjects = () => {
  ElMessage.info('跳转到项目详情页...')
}

// 监听平台指标变化
watch(platformMetric, () => {
  updatePlatformChart()
})

// 初始化
onMounted(async () => {
  await loadProjects()
  await loadData()
  await nextTick()
  initCharts()
})

// 清理
onUnmounted(() => {
  funnelChart?.dispose()
  platformChart?.dispose()
  trendChart?.dispose()
})
</script>

<style scoped lang="scss">
.enhanced-reports-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

// 筛选栏
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  .filter-left {
    display: flex;
    align-items: center;
  }
  
  .filter-right {
    display: flex;
    align-items: center;
  }
}

// KPI 区域
.kpi-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .section-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
    
    .update-time {
      font-size: 12px;
      color: #909399;
    }
  }
}

// KPI 卡片网格
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.kpi-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  &.card-blue {
    border-left: 4px solid #409EFF;
    .kpi-icon { color: #409EFF; background: rgba(64, 158, 255, 0.1); }
  }
  
  &.card-green {
    border-left: 4px solid #67C23A;
    .kpi-icon { color: #67C23A; background: rgba(103, 194, 58, 0.1); }
  }
  
  &.card-orange {
    border-left: 4px solid #E6A23C;
    .kpi-icon { color: #E6A23C; background: rgba(230, 162, 60, 0.1); }
  }
  
  &.card-purple {
    border-left: 4px solid #9c27b0;
    .kpi-icon { color: #9c27b0; background: rgba(156, 39, 176, 0.1); }
  }
}

.kpi-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  margin-right: 16px;
  font-size: 24px;
}

.kpi-content {
  flex: 1;
}

.kpi-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.kpi-sub {
  font-size: 12px;
  color: #909399;
  
  .highlight {
    color: #67C23A;
    margin-right: 8px;
  }
}

// 图表区域
.charts-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  &.full-width {
    grid-column: 1 / -1;
  }
  
  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .chart-title {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .chart-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .chart-container {
    width: 100%;
    height: 350px;
    
    &.large {
      height: 400px;
    }
  }
}

// 漏斗图统计
.funnel-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  
  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    
    &.highlight {
      .stat-value {
        color: #409EFF;
        font-size: 24px;
      }
    }
  }
  
  .stat-label {
    font-size: 12px;
    color: #606266;
    margin-bottom: 4px;
  }
  
  .stat-value {
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }
}

// 指标标签
.metric-tag {
  margin-right: 8px;
  margin-bottom: 4px;
}

// 表格区域
.tables-section {
  margin-bottom: 20px;
}

.table-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .table-title {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}

// 排名单元格
.rank-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
  
  &.rank-1 {
    background: #FFD700;
    color: #fff;
  }
  
  &.rank-2 {
    background: #C0C0C0;
    color: #fff;
  }
  
  &.rank-3 {
    background: #CD7F32;
    color: #fff;
  }
}

// 项目单元格
.project-cell {
  display: flex;
  flex-direction: column;
  
  .project-name {
    font-weight: 500;
    color: #303133;
  }
  
  .company-name {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }
}

// 命中率单元格
.rate-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .rate-value {
    font-weight: 500;
    font-size: 13px;
  }
  
  &.rate-high .rate-value {
    color: #67C23A;
  }
  
  &.rate-medium .rate-value {
    color: #E6A23C;
  }
  
  &.rate-low .rate-value {
    color: #F56C6C;
  }
}

// 响应式设计
@media (max-width: 1400px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .funnel-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
  
  .funnel-stats {
    grid-template-columns: 1fr;
  }
  
  .filter-bar {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>
