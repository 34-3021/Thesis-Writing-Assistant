<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'  // 添加watch和onMounted
// watch用于监听数据变化，onMounted用于组件挂载后执行代码（钩子中加载数据）
import { useRouter } from 'vue-router'
import { useUserstore } from '@/store/user'
import { GenerateChapterApi } from '@/request/api'
// 导入工具函数
import { generateWordDocument, generateMarkdownDocument } from '@/utils/document-formatter'

// 定义章节结构
interface Chapter {
  title: string
  instruction: string
  content: string
}

// 从用户store中获取用户名
const userStore = useUserstore()
const userDisplayName = ref(userStore.userName)
const router = useRouter()

// 论文总标题
const mainTitle = ref('')

// 动态章节列表，初始包含一个章节输入框
const chapters = ref<Chapter[]>([{ title: '', instruction: '', content: '' }])

const maxChapters = 5

// 调用AI后端生成章节内容的函数（针对单个章节）
async function generateChapterContent(chapterIndex: number) {
  const chapter = chapters.value[chapterIndex]
  if (!mainTitle.value || !chapter.title || !chapter.instruction) {
    alert('请填写论文总标题、章节标题与内容说明')
    return
  }
  try {
    const res = await GenerateChapterApi({
      main_title: mainTitle.value,
      chapter_title: chapter.title,
      chapter_instruction: chapter.instruction
    })
    // 将生成的内容更新到该章节的 content 字段
    chapters.value[chapterIndex].content = res.response
    alert(`章节${chapterIndex+1}内容生成成功！`)
  } catch (error) {
    console.error(error)
    alert('生成功能异常，请重试')
  }
}

function goBack() {
  router.push({ name: 'Index' })
}

function removeChapter(index: number) {
  // 删除对应章节
  chapters.value.splice(index, 1)
}

function addChapter() {
  if (chapters.value.length < maxChapters) {
    chapters.value.push({ title: '', instruction: '', content: '' })
  } else {
    alert('最多只能添加5个章节')
  }
}

// 导出Markdown文件
function exportMarkdown() {
  generateMarkdownDocument(
    mainTitle.value, 
    chapters.value.map(chapter => ({ 
      title: chapter.title, 
      content: chapter.content 
    }))
  )
}

// 导出Word文档
async function exportWord() {
  try {
    await generateWordDocument(
      mainTitle.value, 
      chapters.value.map(chapter => ({ 
        title: chapter.title, 
        content: chapter.content 
      }))
    )
    alert('Word 文档导出成功！')
  } catch (error) {
    console.error('导出Word文档失败', error)
    alert('导出Word文档失败')
  }
}

// 新增: 保存当前内容到 localStorage
function saveToLocalStorage() {
  const data = {
    mainTitle: mainTitle.value,
    chapters: chapters.value,
    lastUpdated: new Date().toISOString()
  }
  localStorage.setItem('writingAssistantData', JSON.stringify(data))
}

// 新增: 从 localStorage 加载内容
function loadFromLocalStorage() {
  const savedData = localStorage.getItem('writingAssistantData')
  if (savedData) {
    try {
      const data = JSON.parse(savedData)
      mainTitle.value = data.mainTitle || ''
      chapters.value = data.chapters || [{ title: '', instruction: '', content: '' }]
    } catch (e) {
      console.error('Failed to load saved data', e)
    }
  }
}

// 新增: 清空保存的内容
function clearAll() {
  // 显示确认对话框
  if (confirm('确定要清空所有内容吗？此操作不可撤销哦！')) {
    localStorage.removeItem('writingAssistantData')
    mainTitle.value = ''
    chapters.value = [{ title: '', instruction: '', content: '' }]
  }
}

// 组件挂载时加载保存的内容
onMounted(() => {
  loadFromLocalStorage()
})

// 监听数据变化，自动保存
watch(
  [mainTitle, chapters], 
  () => {
    saveToLocalStorage()
  },
  { deep: true } // 深度监听对象内部变化
)
// script表示Vue组件的逻辑部分，可以在其中写入JavaScript代码，如变量、函数等
</script>

<template>
  <div class="writing-assistant-wrapper">
    <div class="header-actions">
      <el-button type="primary" @click="goBack">返回</el-button>
      <!-- 清空按钮 -->
      <el-button type="danger" @click="clearAll">一键清空</el-button>
    </div>
    <div class="welcome-bar">
      <strong>欢迎，{{ userDisplayName }}！</strong> 开始您的论文写作助手之旅吧！<br/>
      <p>当前写作助手支持<strong style="color: #DAA520;">写作记录保存</strong>，如要删除，可点击右上角的一键清空～</p>
    </div>
    
    <el-form label-position="top" class="writing-assistant-form">
      <el-form-item label="论文总标题">
        <el-input v-model="mainTitle" placeholder="请输入论文总标题"></el-input>
      </el-form-item>
      
      <div v-for="(chapter, index) in chapters" :key="index" class="chapter-box">
        <el-form-item :label="`章节 ${index + 1} 标题`">
          <el-input v-model="chapter.title" placeholder="请输入章节标题"></el-input>
        </el-form-item>
        <el-form-item :label="`章节 ${index + 1} 内容说明`">
          <el-input v-model="chapter.instruction" placeholder="请输入生成该章节内容的说明" type="textarea"></el-input>
        </el-form-item>
        <!-- 生成按钮 -->
        <el-button type="success" @click="generateChapterContent(index)">
          生成该章节内容
        </el-button>
        <!-- 新增删除按钮 -->
        <el-button type="danger" @click="removeChapter(index)" style="margin-left:10px;">
          删除章节
        </el-button>
      </div>
      
      <el-button type="primary" @click="addChapter" v-if="chapters.length < maxChapters">
        添加章节
      </el-button>
      
      <el-form-item class="btn-group">
        <!-- 如需批量生成可调用此函数（目前仅供模拟），或逐个点击生成 -->
        <!-- <el-button type="success" @click="generateContentSimulate">一键生成内容（模拟）</el-button> -->
      </el-form-item>
    </el-form>
    
    <div v-if="chapters.some(chapter => chapter.content)" class="preview-area">
      <h2>生成内容预览</h2>
      <div v-for="(chapter, index) in chapters" :key="'content-' + index" class="preview-chapter">
        <h3>章节 {{ index + 1 }}: {{ chapter.title }}</h3>
        <el-input type="textarea" v-model="chapter.content" :rows="6"></el-input>
      </div>
      
      <!-- 添加导出按钮组 -->
      <div class="export-buttons">
        <el-button type="warning" @click="exportMarkdown" class="export-btn">
          导出 Markdown 文件
        </el-button>
        <el-button type="primary" @click="exportWord" class="export-btn">
          导出 Word 文档
        </el-button>
      </div>
    </div>
    <div class="trademark-container">
      <img src="@/assets/images/trademark.jpg" alt="trademark" class="floating-trademark" />
    </div>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
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
/* 添加导出按钮组样式 */
.export-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin: 20px auto;
}
.export-btn {
  font-weight: 500;
}
/* 修改后 */
.trademark-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
}

.floating-trademark {
  height: 80px;
  opacity: 0.9;
}
</style>