<template>
  <div class="settings-page">
    <h2>设置</h2>
    <div class="settings-sections">
      <div class="setting-section">
        <h3>平台设置</h3>
        <div class="platform-toggles">
          <div
            v-for="platform in platforms"
            :key="platform.id"
            class="platform-toggle"
          >
            <div class="platform-info">
              <div
                class="platform-badge"
                :style="{ background: platform.color }"
              >
                {{ platform.code }}
              </div>
              <span>{{ platform.name }}</span>
            </div>
            <el-switch v-model="platform.enabled" @change="togglePlatform(platform.id)" />
          </div>
        </div>
      </div>

      <div class="setting-section">
        <h3>应用设置</h3>
        <div class="setting-item">
          <span>暗色主题</span>
          <el-switch v-model="darkTheme" />
        </div>
        <div class="setting-item">
          <span>启动时最小化到托盘</span>
          <el-switch v-model="minimizeToTray" />
        </div>
        <div class="setting-item">
          <span>发布完成通知</span>
          <el-switch v-model="publishNotification" />
        </div>
      </div>

      <div class="setting-section">
        <h3>关于</h3>
        <div class="about-info">
          <p><strong>AutoGeo</strong> 智能多平台文章发布助手</p>
          <p>版本: 1.0.0</p>
          <p>老王我用心打造的自动化工具！</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { PLATFORMS } from '@/core/config/platform'

const darkTheme = ref(true)
const minimizeToTray = ref(false)
const publishNotification = ref(true)

const platforms = Object.values(PLATFORMS).map(p => ({
  ...p,
  enabled: true,
}))

const togglePlatform = (id: string) => {
  console.log('Toggle platform:', id)
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
    margin: 0 0 16px 0;
    font-size: 16px;
    color: var(--text-primary);
  }

  .platform-toggles {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .platform-toggle {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: var(--bg-tertiary);
      border-radius: 8px;

      .platform-info {
        display: flex;
        align-items: center;
        gap: 12px;

        .platform-badge {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 600;
          color: white;
        }
      }
    }
  }

  .setting-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);

    &:last-child {
      border-bottom: none;
    }
  }

  .about-info {
    p {
      margin: 8px 0;
      color: var(--text-secondary);
    }
  }
}
</style>
