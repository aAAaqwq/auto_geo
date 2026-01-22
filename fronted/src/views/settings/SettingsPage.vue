<template>
  <div class="settings-page">
    <h2>设置</h2>
    <div class="settings-sections">
      <div class="setting-section">
        <h3>定时任务</h3>
        <div class="setting-item">
          <div class="setting-info">
            <span>定时任务服务状态</span>
            <span class="setting-desc">控制自动化任务的运行状态</span>
          </div>
          <div class="setting-value">
            <span class="status-badge" :class="{ active: schedulerRunning }">
              {{ schedulerRunning ? '运行中' : '已停止' }}
            </span>
          </div>
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span>快速配置</span>
            <span class="setting-desc">跳转到定时任务配置页面</span>
          </div>
          <el-button type="primary" link @click="goToScheduler">
            前往配置
            <svg viewBox="0 0 16 16" fill="currentColor" width="12">
              <path d="M4 8a.5.5 0 01.5-.5h5.793L4.146 3.354a.5.5 0 11.708-.708l7 7a.5.5 0 010 .708l-7 7a.5.5 0 01-.708-.708L10.293 8.5H4.5A.5.5 0 014 8z"/>
            </svg>
          </el-button>
        </div>
      </div>

      <div class="setting-section">
        <h3>知识库管理</h3>
        <div class="setting-item">
          <div class="setting-info">
            <span>企业知识库</span>
            <span class="setting-desc">管理不同企业的知识库内容</span>
          </div>
          <el-button type="primary" link @click="goToKnowledge">
            前往管理
            <svg viewBox="0 0 16 16" fill="currentColor" width="12">
              <path d="M4 8a.5.5 0 01.5-.5h5.793L4.146 3.354a.5.5 0 11.708-.708l7 7a.5.5 0 010 .708l-7 7a.5.5 0 01-.708-.708L10.293 8.5H4.5A.5.5 0 014 8z"/>
            </svg>
          </el-button>
        </div>
      </div>

      <div class="setting-section">
        <h3>应用设置</h3>
        <div class="setting-item">
          <div class="setting-info">
            <span>暗色主题</span>
            <span class="setting-desc">切换应用的外观主题</span>
          </div>
          <el-switch v-model="darkTheme" />
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span>启动时最小化到托盘</span>
            <span class="setting-desc">应用启动后最小化到系统托盘</span>
          </div>
          <el-switch v-model="minimizeToTray" />
        </div>
        <div class="setting-item">
          <div class="setting-info">
            <span>发布完成通知</span>
            <span class="setting-desc">文章发布完成后发送通知</span>
          </div>
          <el-switch v-model="publishNotification" />
        </div>
      </div>

      <div class="setting-section">
        <h3>关于</h3>
        <div class="about-info">
          <div class="about-header">
            <div class="about-logo">🚀</div>
            <div class="about-title">
              <strong>AutoGeo</strong>
              <span class="about-version">v2.0.0</span>
            </div>
          </div>
          <p>AI搜索引擎优化自动化平台</p>
          <p class="about-desc">用心打造的自动化工具，让GEO更简单</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const darkTheme = ref(true)
const minimizeToTray = ref(false)
const publishNotification = ref(true)
const schedulerRunning = ref(true)

const goToScheduler = () => {
  router.push({ name: 'Scheduler' })
}

const goToKnowledge = () => {
  router.push({ name: 'Knowledge' })
}
</script>

<style scoped lang="scss">
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 24px;

  h2 {
    margin: 0;
  }
}

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.setting-section {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 24px;

  h3 {
    margin: 0 0 20px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }

  .setting-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0;
    border-bottom: 1px solid var(--border);

    &:last-child {
      border-bottom: none;
      padding-top: 0;
    }

    .setting-info {
      display: flex;
      flex-direction: column;
      gap: 4px;

      > span:first-child {
        font-size: 14px;
        color: var(--text-primary);
        font-weight: 500;
      }

      .setting-desc {
        font-size: 12px;
        color: var(--text-secondary);
      }
    }

    .setting-value {
      .status-badge {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        background: var(--bg-tertiary);
        color: var(--text-secondary);

        &.active {
          background: rgba(34, 197, 94, 0.1);
          color: #22c55e;
        }
      }
    }
  }

  .about-info {
    text-align: center;
    padding: 20px 0;

    .about-header {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      margin-bottom: 16px;

      .about-logo {
        width: 64px;
        height: 64px;
        border-radius: 16px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
      }

      .about-title {
        text-align: left;

        strong {
          display: block;
          font-size: 20px;
          color: var(--text-primary);
        }

        .about-version {
          font-size: 13px;
          color: #6366f1;
          background: rgba(99, 102, 241, 0.1);
          padding: 4px 10px;
          border-radius: 12px;
        }
      }
    }

    p {
      margin: 6px 0;
      color: var(--text-secondary);
      font-size: 14px;

      &.about-desc {
        font-size: 13px;
        color: var(--text-secondary);
        opacity: 0.8;
      }
    }
  }
}

.el-button svg {
  margin-left: 4px;
  vertical-align: middle;
}
</style>
