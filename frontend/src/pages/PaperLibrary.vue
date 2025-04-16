<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { GetPapersList, DeletePaper } from '@/request/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserstore } from '@/store/user'

interface Paper {
  id: number
  title: string
  author: string
  abstract: string
  file_path: string
}

const papers = ref<Paper[]>([])
const loading = ref(true)
const fileInput = ref<HTMLInputElement | null>(null)
const uploadLoading = ref(false)
const userStore = useUserstore()

// 获取论文列表
async function fetchPapers() {
  loading.value = true
  try {
    papers.value = await GetPapersList({ skip: 0, limit: 100 })
  } catch (error) {
    console.error('获取论文列表失败', error)
    ElMessage.error('获取论文列表失败')
  } finally {
    loading.value = false
  }
}

// 触发文件选择对话框
function triggerFileUpload() {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

// 处理文件选择
async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    ElMessage.error('请上传PDF格式的论文')
    return
  }

  uploadLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)

    // 发送文件到后端
    const response = await fetch('/api/papers/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      },
      body: formData
    })

    if (!response.ok) {
      throw new Error(`上传失败: ${response.status}`)
    }

    const result = await response.json()
    ElMessage.success('论文上传成功')
    // 重新获取论文列表
    fetchPapers()
  } catch (error) {
    console.error('上传论文失败', error)
    ElMessage.error('上传论文失败')
  } finally {
    uploadLoading.value = false
    // 重置文件输入，允许重复上传同一文件
    if (fileInput.value) fileInput.value.value = ''
  }
}

// 删除论文
async function handleDelete(paperId: number) {
  try {
    await ElMessageBox.confirm('确定要删除这篇论文吗？此操作不可撤销哦！', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await DeletePaper(paperId)
    ElMessage.success('论文删除成功')
    // 重新获取列表
    fetchPapers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除论文失败', error)
      ElMessage.error('删除论文失败')
    }
  }
}

// 获取文件名（从路径中）
function getFileName(path: string): string {
  if (!path) return '未知文件'
  const parts = path.split('/')
  return parts[parts.length - 1]
}

// 页面加载时获取论文列表
onMounted(() => {
  fetchPapers()
})
</script>

<template>
  <div class="paper-library">
    <h1 class="page-title">论文库</h1>
    
    <div class="content-container">
      <!-- 上传区域 -->
      <el-card class="card-component">
        <template #header>
          <div class="card-header">
            <span>上传新论文</span>
          </div>
        </template>
        <div class="upload-area">
          <el-button type="primary" @click="triggerFileUpload" :loading="uploadLoading">
            <el-icon><Upload /></el-icon> 选择PDF文件
          </el-button>
          <input 
            type="file" 
            ref="fileInput" 
            @change="handleFileChange" 
            accept=".pdf" 
            style="display: none"
          />
          <span class="upload-hint">亲爱的fudan同学，你好！直接上传PDF文件，系统会自动提取论文信息～</span>
        </div>
      </el-card>
      
      <!-- 管理说明卡片 -->
      <el-card class="card-component">
        <template #header>
          <div class="card-header">
            <span>论文管理说明</span>
          </div>
        </template>
        <p class="card-content">目前功能已优化，可直接在前端上传论文！这里显示了您系统中所有论文。可查看详情，上传新论文，或删除不需要的论文。</p>
      </el-card>
      
      <!-- 论文列表卡片 -->
      <el-card class="card-component">
        <template #header>
          <div class="card-header">
            <span>论文列表</span>
          </div>
        </template>
        
        <el-table 
          :data="papers" 
          style="width: 100%" 
          v-loading="loading"
          class="data-table"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="title" label="标题" width="250" />
          <el-table-column prop="author" label="作者" width="150" />
          <el-table-column label="文件名" width="200">
            <template #default="{ row }">
              {{ getFileName(row.file_path) }}
            </template>
          </el-table-column>
          <el-table-column label="摘要" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.abstract.length > 100 ? row.abstract.substring(0, 100) + '...' : row.abstract }}
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-empty 
          v-if="papers.length === 0 && !loading" 
          description="暂无论文数据" 
          class="empty-state"
        />
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.paper-library {
  padding: 24px;
  height: 100%;
  background-color: #f5f7fa;
}

.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.content-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-component {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-content {
  color: #606266;
  line-height: 1.6;
}

.upload-area {
  display: flex;
  align-items: center;
  padding: 16px 0;
}

.upload-hint {
  margin-left: 16px;
  color: #909399;
  font-size: 14px;
}

.data-table {
  border-radius: 4px;
  overflow: hidden;
}

.empty-state {
  padding: 32px 0;
}

/* 覆盖element-plus样式 */
:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  background-color: #f8f9fb;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-table th.el-table__cell) {
  background-color: #f8f9fb;
}
</style>