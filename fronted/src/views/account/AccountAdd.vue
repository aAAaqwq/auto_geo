<template>
  <div class="account-add-page">
    <h2>添加账号</h2>
    <p>请从账号列表页面添加账号</p>
    <el-button @click="$router.push('/accounts')">返回账号列表</el-button>
  </div>
</template>

<style scoped>
.account-add-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}
</style>
