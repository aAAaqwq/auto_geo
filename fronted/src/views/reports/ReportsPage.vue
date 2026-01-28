<template>
  <div class="reports-page">
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
        <el-button-group>
          <el-button
            :type="selectedPlatform === 'all' ? 'primary' : ''"
            @click="selectPlatform('all')"
          >
            全平台
          </el-button>
          <el-button
            v-for="platform in aiPlatforms"
            :key="platform.value"
            :type="selectedPlatform === platform.value ? 'primary' : ''"
            @click="selectPlatform(platform.value)"
          >
            {{ platform.label }}
          </el-button>
        </el-button-group>
        <el-button style="margin-left: 12px" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 数据总览卡片 -->
    <div class="overview-section">
      <div class="section-header">
        <h2 class="section-title">数据总览</h2>
        <el-icon class="info-icon"><InfoFilled /></el-icon>
      </div>
      <div class="overview-cards">
        <div class="overview-card card-primary">
          <div class="card-label">文章生成数</div>
          <div class="card-value">{{ overview.total_articles_generated || 0 }}</div>
          <div class="card-detail">
            <span>普通: {{ overview.total_articles || 0 }}</span>
            <span>GEO: {{ overview.total_geo_articles || 0 }}</span>
          </div>
        </div>
        <div class="overview-card card-success">
          <div class="card-label">发布成功率</div>
          <div class="card-value">{{ overview.publish_success_rate || 0 }}%</div>
          <div class="card-detail">
            <span>成功: {{ overview.publish_success || 0 }}</span>
            <span>总数: {{ overview.total_publish_records || 0 }}</span>
          </div>
        </div>
        <div class="overview-card card-warning">
          <div class="card-label">关键词命中率</div>
          <div class="card-value">{{ overview.keyword_hit_rate || 0 }}%</div>
          <div class="card-detail">
            <span>命中: {{ overview.keyword_found || 0 }}</span>
            <span>检测: {{ overview.total_checks || 0 }}</span>
          </div>
        </div>
        <div class="overview-card card-info">
          <div class="card-label">公司名命中率</div>
          <div class="card-value">{{ overview.company_hit_rate || 0 }}%</div>
          <div class="card-detail">
            <span>命中: {{ overview.company_found || 0 }}</span>
            <span>检测: {{ overview.total_checks || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 平台对比分析 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">AI平台对比分析</h3>
        </div>
        <div ref="platformChartRef" class="chart-container"></div>
      </div>

      <!-- 项目对比分析 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">项目对比分析</h3>
          <div class="chart-actions">
            <el-checkbox-group v-model="selectedProjects" @change="updateProjectChart">
              <el-checkbox
                v-for="project in projects"
                :key="project.id"
                :label="project.id"
                :disabled="selectedProjects.length >= 5 && !selectedProjects.includes(project.id)"
              >
                {{ project.name }}
              </el-checkbox>
            </el-checkbox-group>
            <span class="chart-note">限制每次勾选最多5个项目</span>
          </div>
        </div>
        <div ref="projectChartRef" class="chart-container"></div>
      </div>

      <!-- 综合趋势分析 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">综合趋势分析</h3>
          <el-radio-group v-model="trendType" size="small" @change="updateTrendChart">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="article">文章</el-radio-button>
            <el-radio-button label="publish">发布</el-radio-button>
            <el-radio-button label="index">收录</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="trendChartRef" class="chart-container"></div>
      </div>
    </div>

    <!-- 数据表格区域 -->
    <div class="tables-section">
      <!-- 项目TOP10排行榜 -->
      <div class="table-card">
        <div class="table-header">
          <h3 class="table-title">项目影响力排行榜</h3>
        </div>
        <el-table
          v-loading="loading"
          :data="topProjects"
          stripe
          style="width: 100%"
        >
          <el-table-column type="index" label="排名" width="60" />
          <el-table-column prop="project_name" label="品牌/项目" min-width="150" />
          <el-table-column prop="company_name" label="公司" min-width="150" />
          <el-table-column prop="total_articles" label="内容声量" width="100" />
          <el-table-column prop="keyword_hit_rate" label="AI提及率" width="120">
            <template #default="{ row }">
              <span :class="getHitRateClass(row.keyword_hit_rate)">
                {{ row.keyword_hit_rate }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="company_hit_rate" label="品牌关联度" width="120">
            <template #default="{ row }">
              <span :class="getHitRateClass(row.company_hit_rate)">
                {{ row.company_hit_rate }}%
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 高贡献文章榜 -->
      <div class="table-card" style="margin-top: 20px;">
        <div class="table-header">
          <h3 class="table-title">高贡献内容分析 (AI引用源)</h3>
        </div>
        <el-table
          v-loading="loadingArticles"
          :data="topArticles"
          stripe
          style="width: 100%"
        >
          <el-table-column type="index" label="排名" width="60" />
          <el-table-column prop="title" label="文章标题" min-width="250" show-overflow-tooltip />
          <el-table-column prop="platform" label="发布平台" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ row.platform }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="keyword_hit_rate" label="AI引用贡献率" width="150">
            <template #default="{ row }">
              <span :class="getHitRateClass(row.keyword_hit_rate)">
                {{ row.keyword_hit_rate }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="发布时间" width="180">
            <template #default="{ row }">
              {{ new Date(row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { Refresh, InfoFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { reportsApi } from '@/services/api'
import { geoKeywordApi } from '@/services/api'
import { ElMessage } from 'element-plus'
import type { 
  ComprehensiveOverview, 
  DailyTrendPoint, 
  PlatformComparison, 
  ProjectComparison, 
  TopProject, 
  TopArticle 
} from '@/types'

// 数据
const loading = ref(false)
const loadingArticles = ref(false)
const selectedProjectId = ref<number | null>(null)
const selectedDays = ref(7)
const selectedPlatform = ref('all')
const selectedProjects = ref<number[]>([])
const trendType = ref('all')

const projects = ref<any[]>([])
const overview = ref<Partial<ComprehensiveOverview>>({})
const dailyTrends = ref<DailyTrendPoint[]>([])
const platformComparison = ref<PlatformComparison[]>([])
const projectComparison = ref<ProjectComparison[]>([])
const topProjects = ref<TopProject[]>([])
const topArticles = ref<TopArticle[]>([])

// AI平台列表
const aiPlatforms = [
  { label: 'DeepSeek', value: 'deepseek' },
  { label: '豆包', value: 'doubao' },
  { label: '通义千问', value: 'qianwen' },
]

// 图表引用
const platformChartRef = ref<HTMLDivElement | null>(null)
const projectChartRef = ref<HTMLDivElement | null>(null)
const trendChartRef = ref<HTMLDivElement | null>(null)
let platformChart: echarts.ECharts | null = null
let projectChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

// 加载项目列表
const loadProjects = async () => {
  try {
    const result = await geoKeywordApi.getProjects()
    projects.value = result || []
    // 默认选择前5个项目
    if (projects.value.length > 0 && selectedProjects.value.length === 0) {
      selectedProjects.value = projects.value.slice(0, 5).map((p: any) => p.id)
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

// 加载全面数据概览
const loadOverview = async () => {
  try {
    const params: any = {}
    if (selectedProjectId.value) {
      params.project_id = selectedProjectId.value
    }
    const result = await reportsApi.getComprehensiveOverview(params)
    overview.value = result || {}
  } catch (error) {
    console.error('加载数据概览失败:', error)
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

// 加载项目对比数据
const loadProjectComparison = async () => {
  try {
    const params: any = { days: selectedDays.value }
    if (selectedProjects.value.length > 0) {
      params.project_ids = selectedProjects.value.join(',')
    }
    const result = await reportsApi.getProjectComparison(params)
    projectComparison.value = result || []
    updateProjectChart()
  } catch (error) {
    console.error('加载项目对比数据失败:', error)
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

// 加载TOP文章
const loadTopArticles = async () => {
  loadingArticles.value = true
  try {
    const params: any = { limit: 10 }
    if (selectedProjectId.value) {
      params.project_id = selectedProjectId.value
    }
    const result = await reportsApi.getTopArticles(params)
    topArticles.value = result || []
  } catch (error) {
    console.error('加载TOP文章失败:', error)
  } finally {
    loadingArticles.value = false
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

// 统一数据加载入口
const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadOverview(),
      loadPlatformComparison(),
      loadProjectComparison(),
      loadTopProjects(),
      loadTopArticles(),
      loadDailyTrends()
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
  // 只加载与时间相关的数据
  Promise.all([
    loadPlatformComparison(),
    loadProjectComparison(),
    loadDailyTrends()
  ])
}

// 选择平台
const selectPlatform = (platform: string) => {
  selectedPlatform.value = platform
  // 可以根据平台筛选数据
  loadPlatformComparison()
}

// 初始化图表
const initCharts = () => {
  if (platformChartRef.value) {
    platformChart = echarts.init(platformChartRef.value)
  }
  if (projectChartRef.value) {
    projectChart = echarts.init(projectChartRef.value)
  }
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    platformChart?.resize()
    projectChart?.resize()
    trendChart?.resize()
  })
  
  updatePlatformChart()
  updateProjectChart()
  updateTrendChart()
}

// 更新平台对比图表
const updatePlatformChart = () => {
  if (!platformChart || !platformComparison.value.length) return
  
  const dates = platformComparison.value[0]?.daily_data?.map((item: any) => {
    const date = new Date(item.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }) || []
  
  const series = platformComparison.value.map((platform: PlatformComparison) => ({
    name: platform.platform_name,
    type: 'line',
    smooth: true,
    data: platform.daily_data.map(item => item.hit_rate),
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
      data: platformComparison.value.map(p => p.platform_name),
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
      name: '命中率(%)',
      min: 0,
      max: 100
    },
    series
  }
  
  platformChart.setOption(option)
}

// 更新项目对比图表
const updateProjectChart = () => {
  if (!projectChart || !projectComparison.value.length) {
    loadProjectComparison()
    return
  }
  
  const dates = projectComparison.value[0]?.daily_data?.map((item: any) => {
    const date = new Date(item.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }) || []
  
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
  
  const series = projectComparison.value.map((project: ProjectComparison, index: number) => ({
    name: project.project_name,
    type: 'line',
    smooth: true,
    data: project.daily_data.map(item => item.hit_rate),
    itemStyle: {
      color: colors[index % colors.length]
    }
  }))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: projectComparison.value.map(p => p.project_name),
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
      name: '命中率(%)',
      min: 0,
      max: 100
    },
    series
  }
  
  projectChart.setOption(option)
}

// 更新趋势图表
const updateTrendChart = () => {
  if (!trendChart || !dailyTrends.value.length) return
  
  const dates = dailyTrends.value.map(item => {
    const date = new Date(item.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  })
  
  const option: any = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: [],
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
    yAxis: [
      {
        type: 'value',
        name: '数量',
        position: 'left'
      },
      {
        type: 'value',
        name: '命中数',
        position: 'right'
      }
    ],
    series: []
  }
  
  if (trendType.value === 'all' || trendType.value === 'article') {
    option.legend.data.push('生成文章数', '发布文章数', '发布成功数')
    option.series.push(
      {
        name: '生成文章数',
        type: 'line',
        data: dailyTrends.value.map(item => item.articles_generated),
        smooth: true,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '发布文章数',
        type: 'line',
        data: dailyTrends.value.map(item => item.articles_published),
        smooth: true,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '发布成功数',
        type: 'line',
        data: dailyTrends.value.map(item => item.publish_success),
        smooth: true,
        itemStyle: { color: '#E6A23C' }
      }
    )
  }
  
  if (trendType.value === 'all' || trendType.value === 'index') {
    option.legend.data.push('检测次数', '关键词命中')
    option.series.push(
      {
        name: '检测次数',
        type: 'bar',
        yAxisIndex: 1,
        data: dailyTrends.value.map(item => item.index_checks),
        itemStyle: { color: '#909399' }
      },
      {
        name: '关键词命中',
        type: 'line',
        yAxisIndex: 1,
        data: dailyTrends.value.map(item => item.keyword_hits),
        smooth: true,
        itemStyle: { color: '#F56C6C' }
      }
    )
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

// 获取命中率样式类
const getHitRateClass = (rate: number) => {
  if (rate >= 60) return 'rate-high'
  if (rate >= 30) return 'rate-medium'
  return 'rate-low'
}

// 监听项目选择变化
watch(selectedProjects, () => {
  if (selectedProjects.value.length > 5) {
    ElMessage.warning('最多只能选择5个项目')
    selectedProjects.value = selectedProjects.value.slice(0, 5)
  } else {
    loadProjectComparison()
  }
})

// 初始化
onMounted(async () => {
  await loadProjects()
  await loadData()
  await nextTick()
  initCharts()
})
</script>

<style scoped lang="scss">
.reports-page {
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

// 数据总览
.overview-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  .section-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    
    .section-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
    
    .info-icon {
      margin-left: 8px;
      color: #909399;
      cursor: pointer;
    }
  }
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.overview-card {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  
  .card-label {
    font-size: 14px;
    color: #606266;
    margin-bottom: 12px;
  }
  
  .card-value {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
  }
  
  .card-detail {
    font-size: 12px;
    color: #909399;
    display: flex;
    justify-content: space-around;
  }
  
  &.card-primary {
    background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
    color: white;
    
    .card-label,
    .card-detail {
      color: rgba(255, 255, 255, 0.9);
    }
  }
  
  &.card-success {
    background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
    color: white;
    
    .card-label,
    .card-detail {
      color: rgba(255, 255, 255, 0.9);
    }
  }
  
  &.card-warning {
    background: linear-gradient(135deg, #E6A23C 0%, #ebb563 100%);
    color: white;
    
    .card-label,
    .card-detail {
      color: rgba(255, 255, 255, 0.9);
    }
  }
  
  &.card-info {
    background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
    color: white;
    
    .card-label,
    .card-detail {
      color: rgba(255, 255, 255, 0.9);
    }
  }
}

// 图表区域
.charts-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
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
    }
    
    .chart-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .chart-note {
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .chart-container {
    width: 100%;
    height: 400px;
  }
}

// 表格区域
.tables-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.table-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  .table-header {
    margin-bottom: 16px;
    
    .table-title {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
}

// 命中率样式
.rate-high {
  color: #67C23A;
  font-weight: 600;
}

.rate-medium {
  color: #E6A23C;
  font-weight: 600;
}

.rate-low {
  color: #F56C6C;
  font-weight: 600;
}

// 响应式设计
@media (max-width: 1400px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .filter-bar {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>