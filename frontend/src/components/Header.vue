<script setup lang="ts">
import {ElMessage, ElNotification as notify} from 'element-plus'
import {LogoutApi} from "@/request/api";
import {useRouter} from 'vue-router'
import {useUserstore} from "@/store/user";
const router = useRouter()
const userStore=useUserstore()

async function logout() {
  // 重置用户状态
  userStore.userName = 'userName'
  userStore.token = 'token'
  
  // 标记手动登出状态，但保留用户名
  const loginInfo = localStorage.getItem('loginInfo')
  if (loginInfo) {
    try {
      const info = JSON.parse(loginInfo)
      // 保留用户名，清除token，标记为手动登出
      localStorage.setItem('loginInfo', JSON.stringify({
        userName: info.userName,
        timestamp: info.timestamp,
        manualLogout: true
      }))
    } catch (e) {
      console.error('处理登出状态失败', e)
    }
  }
  
  ElMessage.success("登出成功")
  await router.push('/')
}
</script>

<template>
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" alt="Logo" style="height: 50px;">
    <div>
      <el-button type="info" @click="logout">登出</el-button>
    </div>
  </div>
</template>

<style scoped>
</style>