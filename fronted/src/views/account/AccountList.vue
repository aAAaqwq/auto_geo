<template>
  <div class="account-list-page">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-select v-model="filterPlatform" placeholder="筛选平台" clearable style="width: 150px">
          <el-option
            v-for="platform in platforms"
            :key="platform.id"
            :label="platform.name"
            :value="platform.id"
          />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加账号
        </el-button>
      </div>
    </div>

    <!-- 账号卡片网格 -->
    <div class="accounts-grid">
      <div
        v-for="account in filteredAccounts"
        :key="account.id"
        class="account-card"
        :class="{ selected: selectedAccountIds.includes(account.id) }"
        @click="toggleSelection(account.id)"
      >
        <div class="account-header">
          <div class="platform-icon" :style="{ background: getPlatformColor(account.platform) }">
            {{ getPlatformCode(account.platform) }}
          </div>
          <div class="status-dot" :class="getStatusClass(account.status)"></div>
        </div>
        <h3 class="account-name">{{ account.account_name }}</h3>
        <p class="account-username">{{ account.username ? '@' + account.username : '已授权' }}</p>
        <p class="account-platform">{{ getPlatformName(account.platform) }}</p>

        <div class="account-actions" @click.stop>
          <el-button
            v-if="account.status !== 1"
            type="primary"
            size="small"
            @click="startAuth(account)"
          >
            去授权
          </el-button>
          <el-button size="small" @click="editAccount(account)">编辑</el-button>
          <el-button type="danger" size="small" @click="deleteAccount(account)">删除</el-button>
        </div>
      </div>

      <!-- 添加账号卡片 -->
      <div class="account-card add-card" @click="showAddDialog">
        <div class="add-icon">
          <el-icon><Plus /></el-icon>
        </div>
        <p>添加账号</p>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑账号' : '添加账号'"
      width="500px"
    >
      <el-form :model="formData" label-width="80px">
        <el-form-item label="平台">
          <el-select v-model="formData.platform" placeholder="选择平台" :disabled="isEdit">
            <el-option
              v-for="platform in platforms"
              :key="platform.id"
              :label="platform.name"
              :value="platform.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="账号名称">
          <el-input v-model="formData.account_name" placeholder="请输入备注名称（用于识别账号）" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.remark" type="textarea" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button v-if="isEdit" type="primary" @click="saveAccount">保存</el-button>
        <el-button v-else type="primary" @click="authNewAccount">去授权登录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAccountStore } from '@/stores/modules/account'
import { PLATFORMS } from '@/core/config/platform'

const accountStore = useAccountStore()

// 平台列表
const platforms = Object.values(PLATFORMS)

// 筛选
const filterPlatform = ref('')

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingAccountId = ref<number | null>(null)

// 表单数据
const formData = ref({
  platform: '',
  account_name: '',
  remark: '',
})

// 计算属性
const filteredAccounts = computed(() => {
  if (!filterPlatform.value) return accountStore.accounts
  return accountStore.accounts.filter(acc => acc.platform === filterPlatform.value)
})

const selectedAccountIds = computed(() => accountStore.selectedAccountIds)

// 加载数据
onMounted(() => {
  accountStore.loadAccounts()
})

// 方法
const showAddDialog = () => {
  isEdit.value = false
  editingAccountId.value = null
  formData.value = { platform: '', account_name: '', remark: '' }
  dialogVisible.value = true
}

const editAccount = (account: any) => {
  isEdit.value = true
  editingAccountId.value = account.id
  formData.value = {
    platform: account.platform,
    account_name: account.account_name,
    remark: account.remark || '',
  }
  dialogVisible.value = true
}

const saveAccount = async () => {
  if (!formData.value.platform || !formData.value.account_name) {
    ElMessage.warning('请填写必填项')
    return
  }

  const result = isEdit.value
    ? await accountStore.updateAccount(editingAccountId.value!, formData.value)
    : await accountStore.createAccount(formData.value)

  if (result.success) {
    ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
    dialogVisible.value = false
    accountStore.loadAccounts()
  } else {
    ElMessage.error(result.message || '操作失败')
  }
}

/**
 * 授权新账号
 * 老王我修改了：现在直接授权，不需要先创建账号！
 */
const authNewAccount = async () => {
  if (!formData.value.platform) {
    ElMessage.warning('请选择平台')
    return
  }

  const accountName = formData.value.account_name || `${PLATFORMS[formData.value.platform]?.name}账号`

  const result = await accountStore.startAuth(formData.value.platform, undefined, accountName)
  if (result.success) {
    dialogVisible.value = false
    ElMessage.success('授权窗口已打开，请在窗口中完成登录后点击"授权完成"按钮')

    // 轮询检查授权状态
    const checkInterval = setInterval(async () => {
      const status = await accountStore.checkAuthStatus(result.taskId)
      if (status.status === 'success') {
        clearInterval(checkInterval)
        ElMessage.success('授权成功！账号已自动保存')
        // 账号列表已在 checkAuthStatus 中自动刷新
      } else if (status.status === 'failed' || status.status === 'timeout') {
        clearInterval(checkInterval)
        ElMessage.error(status.message || '授权失败，请重试')
      }
    }, 2000)
  } else {
    ElMessage.error(result.message || '授权启动失败')
  }
}

const deleteAccount = async (account: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除账号"${account.account_name}"吗？`, '确认删除', {
      type: 'warning',
    })

    const result = await accountStore.deleteAccount(account.id)
    if (result.success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message || '删除失败')
    }
  } catch {
    // 用户取消
  }
}

const startAuth = async (account: any) => {
  const result = await accountStore.startAuth(account.platform, account.id)
  if (result.success) {
    dialogVisible.value = false
    ElMessage.success('授权窗口已打开，请在窗口中完成登录后点击"授权完成"按钮')

    // 轮询检查授权状态
    const checkInterval = setInterval(async () => {
      const status = await accountStore.checkAuthStatus(result.taskId)
      if (status.status === 'success') {
        clearInterval(checkInterval)
        ElMessage.success('授权成功！账号已自动更新')
        // 账号列表已在 checkAuthStatus 中自动刷新
      } else if (status.status === 'failed' || status.status === 'timeout') {
        clearInterval(checkInterval)
        ElMessage.error(status.message || '授权失败，请重试')
      }
    }, 2000)
  } else {
    ElMessage.error(result.message || '授权启动失败')
  }
}

const toggleSelection = (id: number) => {
  accountStore.toggleAccountSelection(id)
}

// 工具方法
const getPlatformColor = (platform: string) => {
  return PLATFORMS[platform]?.color || '#666'
}

const getPlatformCode = (platform: string) => {
  return PLATFORMS[platform]?.code || '?'
}

const getPlatformName = (platform: string) => {
  return PLATFORMS[platform]?.name || platform
}

const getStatusClass = (status: number) => {
  return {
    'status-active': status === 1,
    'status-inactive': status === 0,
    'status-expired': status === -1,
  }
}
</script>

<style scoped lang="scss">
.account-list-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .toolbar-left {
    display: flex;
    gap: 12px;
  }
}

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.account-card {
  background: var(--bg-secondary);
  border: 2px solid transparent;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  &.selected {
    border-color: var(--primary);
  }

  &.add-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 2px dashed var(--border);
    min-height: 200px;

    &:hover {
      border-color: var(--primary);
    }

    .add-icon {
      font-size: 48px;
      color: var(--text-secondary);
      margin-bottom: 12px;
    }

    p {
      margin: 0;
      color: var(--text-secondary);
    }
  }

  .account-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .platform-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 600;
      color: white;
    }

    .status-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;

      &.status-active {
        background: #4caf50;
        box-shadow: 0 0 8px #4caf50;
      }

      &.status-inactive {
        background: #9e9e9e;
      }

      &.status-expired {
        background: #f44336;
      }
    }
  }

  .account-name {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .account-username {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: var(--text-secondary);
  }

  .account-platform {
    margin: 0 0 16px 0;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .account-actions {
    display: flex;
    gap: 8px;
  }
}

// 选择器样式覆盖
:deep(.el-select) {
  .el-input__wrapper {
    background: var(--bg-tertiary);
    border-color: var(--border);
    box-shadow: none;

    &:hover,
    &.is-focus {
      border-color: var(--primary);
    }
  }
}

:deep(.el-dialog) {
  background: var(--bg-secondary);
  border: 1px solid var(--border);

  .el-dialog__header {
    border-bottom: 1px solid var(--border);
  }

  .el-dialog__title {
    color: var(--text-primary);
  }
}
</style>
