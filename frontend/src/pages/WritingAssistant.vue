<script setup lang="ts">
/*
  该页面实现论文写作助手前端界面：
  1. 顶部输入论文总标题
  2. 动态添加最多5个章节，每个章节有标题和内容说明输入框
  3. “一键生成内容”按钮，调用模拟接口生成各章节内容（暂时返回模拟文本，后续可替换为真正的后台 API 调用）
  4. 显示生成后的内容，供用户修改
  5. “一键导出 Markdown 文件”按钮，将内容生成 Markdown 文件并下载
*/

// 使用 Vue 组合式 API
import { ref } from 'vue'

// 定义章节结构
interface Chapter {
  title: string        // 章节标题
  instruction: string  // 章节内容说明
  content: string      // 后续生成的章节内容（AI生成的）
}

// 论文总标题
const mainTitle = ref('')

// 动态章节列表，初始包含一个章节输入框
const chapters = ref<Chapter[]>([
  { title: '', instruction: '', content: '' }
])

// 限制最多添加的章节数
const maxChapters = 5

// 模拟调用后台生成内容的接口
function generateContent() {
  // TODO: 替换为实际后端 API 调用，本处只是模拟返回内容
  chapters.value.forEach((chapter, index) => {
    chapter.content = `生成的内容 for Chapter ${index + 1} with title "${chapter.title}" and instructions "${chapter.instruction}".`
  })
  alert('内容生成完成！（模拟结果）')
}

// 添加章节输入区域
function addChapter() {
  if (chapters.value.length < maxChapters) {
    chapters.value.push({ title: '', instruction: '', content: '' })
  } else {
    alert('最多只能添加5个章节')
  }
}

// 导出 Markdown 文件
function exportMarkdown() {
  // 生成 Markdown 格式内容
  let markdownText = `# ${mainTitle.value}\n\n`
  chapters.value.forEach((chapter, index) => {
    markdownText += `## ${chapter.title}\n\n`
    markdownText += `${chapter.content}\n\n`
  })
  // 生成 Blob 对象，并创建下载链接
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
  <div style="padding: 20px;">
    <!-- 整体使用 Element Plus 的 Form 组件布局 -->
    <el-form label-position="top">
      <el-form-item label="论文总标题">
        <el-input v-model="mainTitle" placeholder="请输入论文总标题"></el-input>
      </el-form-item>
      
      <!-- 循环生成章节输入框 -->
      <div v-for="(chapter, index) in chapters" :key="index" style="margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;">
        <el-form-item :label="`章节 ${index + 1} 标题`">
          <el-input v-model="chapter.title" placeholder="请输入章节标题"></el-input>
        </el-form-item>
        <el-form-item :label="`章节 ${index + 1} 内容说明`">
          <el-input v-model="chapter.instruction" placeholder="请输入生成该章节内容的说明" type="textarea"></el-input>
        </el-form-item>
      </div>
      
      <!-- 当章节数未超过限制时，显示添加章节按钮 -->
      <el-button type="primary" @click="addChapter" v-if="chapters.length < maxChapters">添加章节</el-button>
      
      <!-- 生成内容按钮 -->
      <el-form-item style="margin-top: 20px;">
        <el-button type="success" @click="generateContent">一键生成内容</el-button>
      </el-form-item>
    </el-form>
    
    <!-- 如果生成了内容，则显示内容预览区 -->
    <div v-if="chapters.some(chapter => chapter.content)" style="margin-top: 40px;">
      <h2>生成内容预览</h2>
      <div v-for="(chapter, index) in chapters" :key="'content-' + index" style="margin-bottom: 20px;">
        <h3>章节 {{ index + 1 }}: {{ chapter.title }}</h3>
        <el-input type="textarea" v-model="chapter.content" rows="6"></el-input>
      </div>
      <!-- 导出 Markdown 文件按钮 -->
      <el-button type="warning" @click="exportMarkdown">一键导出 Markdown 文件</el-button>
    </div>
  </div>
</template>

<style scoped>
/* 可以根据需要添加样式 */
</style>