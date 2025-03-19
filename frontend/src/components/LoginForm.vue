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

// 新增记住我复选框状态（1小时内免密登录）
const remember = ref(false)

// onMounted 钩子：检查 localStorage 是否有保存的登录信息，若在1小时内则自动填充
onMounted(() => {
  const stored = localStorage.getItem('loginInfo')
  if(stored) {
    const info = JSON.parse(stored)
    const now = new Date().getTime()
    if(now - info.timestamp < 3600000) { // 3600000毫秒 = 1小时
      ruleForm.userName = info.userName
      ruleForm.password = info.password
      remember.value = true
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
        ElMessage.success('登陆成功')
        userStore.token = res.access_token
        userStore.userName = ruleForm.userName

        // 如勾选“1小时免密登录”，保存登录信息到 localStorage（注意：生产环境请不要保存明文密码）
        if(remember.value) {
          const info = {
            userName: ruleForm.userName,
            password: ruleForm.password,
            timestamp: new Date().getTime()
          }
          localStorage.setItem('loginInfo', JSON.stringify(info))
        } else {
          localStorage.removeItem('loginInfo')
        }
        
        await router.push({ name: 'IndexMain', params: { userName: ruleForm.userName } })
      } catch (e) {
        console.log(e)
        ElMessage.error('登陆失败，请重新输入用户名和密码')
      }
    } else {
      ElMessage.error('登陆失败，未输入用户名和密码')
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
    <!-- 新增1小时免密登录复选框 -->
    <el-form-item>
      <el-checkbox v-model="remember">1小时免密登录</el-checkbox>
    </el-form-item>
    <!-- 按钮区域，采用 flex 居中对称排列 -->
    <el-form-item class="button-group">
      <el-button type="primary" @click="submitForm(ruleFormRef)">登录</el-button>
      <el-button type="success" @click="jumpToRegister()">注册</el-button>
    </el-form-item>
  </el-form>
</template>

<style scoped>
/* 新增按钮区域样式 */
.button-group {
  display: flex;
  width: 100%;
  justify-content: center;
  align-items: center;
}
/* 使用 ::v-deep 覆盖 .el-form-item__content 的 margin-left */
/* 根本原因：Element Plus 内部自动给按钮区域生成的容器
（.el-form-item__content）设置了 margin-left: auto，
从而将按钮推向右侧，要解决这个问题，需要覆盖这个自动样式 */
::v-deep(.button-group .el-form-item__content) {
  margin-left: 0 !important;
  display: flex;
  justify-content: center;
  gap: 20px;
}
</style>