<script setup lang="ts">
/*
  该页面实现论文写作助手前端界面：  
  … （原注释保持不变）
*/
import { ref } from 'vue'
import { useUserstore } from '@/store/user'

// 定义章节结构
interface Chapter {
  title: string
  instruction: string
  content: string
}

// 从用户store中获取用户名
const userStore = useUserstore()
const userDisplayName = ref(userStore.userName)

// 论文总标题
const mainTitle = ref('')

// 动态章节列表，初始包含一个章节输入框
const chapters = ref<Chapter[]>([{ title: '', instruction: '', content: '' }])

// 限制章节数
const maxChapters = 5

function generateContent() {
  chapters.value.forEach((chapter, index) => {
    chapter.content = `生成的内容 for Chapter ${index + 1} with title "${chapter.title}" and instructions "${chapter.instruction}".`
  })
  alert('内容生成完成！（模拟结果）')
}

function addChapter() {
  if (chapters.value.length < maxChapters) {
    chapters.value.push({ title: '', instruction: '', content: '' })
  } else {
    alert('最多只能添加5个章节')
  }
}

function exportMarkdown() {
  let markdownText = `# ${mainTitle.value}\n\n`
  chapters.value.forEach((chapter, index) => {
    markdownText += `## ${chapter.title}\n\n`
    markdownText += `${chapter.content}\n\n`
  })
  const blob = new Blob([markdownText], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '论文写作助手生成内容.md'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="writing-assistant-wrapper">
    <!-- 欢迎提示条 -->
    <div class="welcome-bar">
      <strong>欢迎，{{ userDisplayName }}！</strong> 开始您的论文写作助手之旅吧！
    </div>
    
    <el-form label-position="top" class="writing-assistant-form">
      <el-form-item label="论文总标题">
        <el-input v-model="mainTitle" placeholder="请输入论文总标题"></el-input>
      </el-form-item>
      
      <!-- 循环生成章节输入框 -->
      <div v-for="(chapter, index) in chapters" :key="index" class="chapter-box">
        <el-form-item :label="`章节 ${index + 1} 标题`">
          <el-input v-model="chapter.title" placeholder="请输入章节标题"></el-input>
        </el-form-item>
        <el-form-item :label="`章节 ${index + 1} 内容说明`">
          <el-input v-model="chapter.instruction" placeholder="请输入生成该章节内容的说明" type="textarea"></el-input>
        </el-form-item>
      </div>
      
      <!-- 添加章节按钮 -->
      <el-button type="primary" @click="addChapter" v-if="chapters.length < maxChapters">
        添加章节
      </el-button>
      
      <!-- 生成内容按钮 -->
      <el-form-item class="btn-group">
        <el-button type="success" @click="generateContent">
          一键生成内容
        </el-button>
      </el-form-item>
    </el-form>
    
    <!-- 生成内容预览区 -->
    <div v-if="chapters.some(chapter => chapter.content)" class="preview-area">
      <h2>生成内容预览</h2>
      <div v-for="(chapter, index) in chapters" :key="'content-' + index" class="preview-chapter">
        <h3>章节 {{ index + 1 }}: {{ chapter.title }}</h3>
        <el-input type="textarea" v-model="chapter.content" :rows="6"></el-input>
      </div>
      <el-button type="warning" @click="exportMarkdown" class="export-btn">
        一键导出 Markdown 文件
      </el-button>
    </div>
    <!-- 新增右下角放大的固定商标 -->
    <img src="@/assets/images/trademark.jpg" alt="trademark" class="floating-trademark" />
  </div>
</template>

<style scoped>
.writing-assistant-wrapper {
  position: relative;
  padding: 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #cbebff 100%);
  border: 2px solid #91d5ff;
  border-radius: 10px;
  margin: 20px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
}
.welcome-bar {
  background-color: #e6f7ff;
  color: #1890ff;
  padding: 10px 15px;
  border: 1px solid #91d5ff;
  border-radius: 5px;
  margin-bottom: 20px;
  text-align: center;
  font-size: 16px;
}
.writing-assistant-form {
  background-color: #ffffff;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #d9d9d9;
}
.chapter-box {
  margin-bottom: 20px;
  border: 1px dashed #91d5ff;
  padding: 15px;
  border-radius: 5px;
}
.preview-area {
  margin-top: 40px;
  background-color: #fafafa;
  padding: 20px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
}
.preview-chapter {
  margin-bottom: 20px;
}
.btn-group {
  margin-top: 20px;
}
.export-btn {
  display: block;
  margin: 20px auto;
}
/* 新增右下角浮动商标样式 */
.floating-trademark {
  position: absolute;
  bottom: 20px;
  right: 20px;
  height: 80px;  /* 稍大于其他页面 */
  opacity: 0.9;
}
</style>