<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { GetPapersList, DeletePaper } from '@/request/api'
import { ElMessage, ElMessageBox } from 'element-plus'

interface Paper {
  id: number
  title: string
  author: string
  abstract: string
  file_path: string
}

const papers = ref<Paper[]>([])
const loading = ref(true)

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

// 删除论文
async function handleDelete(paperId: number) {
  try {
    await ElMessageBox.confirm('确定要删除这篇论文吗？此操作不可逆', '提示', {
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
    <h1>论文库</h1>
    
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span>论文管理说明</span>
        </div>
      </template>
      <p>这里显示了您系统中所有的论文。您可以查看论文详情或删除不需要的论文。</p>
      <p>要添加新论文，请通过后端命令行运行 <code>python backend/insert_test_paper.py</code>。</p>
    </el-card>
    
    <el-table :data="papers" style="width: 100%; margin-top: 20px" v-loading="loading">
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
    
    <el-empty v-if="papers.length === 0 && !loading" description="暂无论文数据" />
  </div>
</template>

<style scoped>
.paper-library {
  padding: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h1 {
  margin-bottom: 20px;
  color: #409EFF;
}

code {
  background-color: #f0f0f0;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
}
</style>