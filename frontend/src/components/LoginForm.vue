<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useRouter } from 'vue-router'
import { useUserstore } from '@/store/user'
import { LoginApi } from "@/request/api"
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserstore()

const ruleFormRef = ref<FormInstance>()

// 定义登录表单数据
const ruleForm = reactive({
  userName: '',
  password: ''
})

// 免密登录复选框状态
const remember = ref(false)

// onMounted 钩子：检查 localStorage 是否有保存的登录信息
onMounted(() => {
  const stored = localStorage.getItem('loginInfo')
  if(stored) {
    const info = JSON.parse(stored)
    const now = new Date().getTime()
    
    // 填充用户名 - 无论是否过期都会填充，提升用户体验
    ruleForm.userName = info.userName
    
    // 验证是否在有效期内（1小时）以及是否手动登出
    if(now - info.timestamp < 3600000 && !info.manualLogout) {
      remember.value = true
      
      // 如果有token且未过期且未手动登出，可以直接使用token自动登录
      if (info.token) {
        userStore.token = info.token
        userStore.userName = info.userName
        // 自动跳转到主页
        router.push({ name: 'IndexMain' })
      }
    }
  }
})

// 验证函数
const checkUserName = (rule: any, value: any, callback: any) => {
  if (value === '') {
    return callback(new Error('请输入用户名'))
  } else {
    callback()
  }
}
const checkPassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else {
    callback()
  }
}

const rules = reactive<FormRules<typeof ruleForm>>({
  userName: [{ validator: checkUserName, trigger: 'blur' }],
  password: [{ validator: checkPassword, trigger: 'blur' }],
})

const submitForm = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate(async (valid) => {
    if (valid) {
      try {
        let res = await LoginApi({
          username: ruleForm.userName,
          password: ruleForm.password
        })
        ElMessage.success('登录成功')
        userStore.token = res.access_token
        userStore.userName = ruleForm.userName

        // 如勾选"1小时免密登录"，保存信息到localStorage
        if(remember.value) {
          const info = {
            userName: ruleForm.userName,
            token: res.access_token,
            timestamp: new Date().getTime(),
            manualLogout: false  // 初始未手动登出
          }
          localStorage.setItem('loginInfo', JSON.stringify(info))
        } else {
          localStorage.removeItem('loginInfo')
        }
        
        await router.push({ name: 'IndexMain', params: { userName: ruleForm.userName } })
      } catch (e) {
        console.log(e)
        ElMessage.error('登录失败，请重新输入用户名和密码')
      }
    } else {
      ElMessage.error('登录失败，未输入用户名和密码')
      return false
    }
  })
}

function jumpToRegister() {
  router.push('/register')
}
</script>

<template>
  <el-form
      ref="ruleFormRef"
      :model="ruleForm"
      :rules="rules"
      style="max-width: 600px"
      label-width="auto"
      class="demo-ruleForm"
  >
    <el-form-item label="用户名" prop="userName">
      <el-input v-model="ruleForm.userName" type="text" autocomplete="off"/>
    </el-form-item>
    <el-form-item label="密码" prop="password">
      <el-input v-model="ruleForm.password" type="password" autocomplete="off"/>
    </el-form-item>
    <el-form-item>
      <el-checkbox v-model="remember">1小时免密登录</el-checkbox>
    </el-form-item>
    <el-form-item class="button-group">
      <el-button type="primary" @click="submitForm(ruleFormRef)">登录</el-button>
      <el-button type="success" @click="jumpToRegister()">注册</el-button>
    </el-form-item>
  </el-form>
</template>

<style scoped>
.button-group {
  display: flex;
  width: 100%;
  justify-content: center;
  align-items: center;
}
::v-deep(.button-group .el-form-item__content) {
  margin-left: 0 !important;
  display: flex;
  justify-content: center;
  gap: 20px;
}
</style>