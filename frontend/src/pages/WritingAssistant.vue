<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserstore } from '@/store/user'
import { GenerateChapterApi } from '@/request/api'
import { generateWordDocument, generateMarkdownDocument } from '@/utils/document-formatter'

interface Chapter {
  title: string
  instruction: string
  content: string
}

const userStore = useUserstore()
const userDisplayName = ref(userStore.userName)
const router = useRouter()

// 广告
const showAdDialog = ref(false)
const canExport = ref(false)
const adVideoList = [
  '/ads/Aerial-photography-of-Fudan-University.mp4',
  '/ads/Acceptance-letter-of-Fudan-University.mp4'
]
// Math.random() 生成一个0到1之间的随机小数，再 * adVideoList.length 将随机数乘以数组长度
// Math.floor(...) 向下取整，确保得到一个有效的数组索引(0到length-1)
const adVideoUrl = ref(adVideoList[Math.floor(Math.random() * adVideoList.length)])
// 用于获取video元素
const adVideoRef = ref<HTMLVideoElement | null>(null)

const mainTitle = ref('')
const chapters = ref<Chapter[]>([{ title: '', instruction: '', content: '' }])
const maxChapters = 5

async function generateChapterContent(chapterIndex: number) {
  const chapter = chapters.value[chapterIndex]
  if (!mainTitle.value) {
    alert('请填写论文总标题！')
    return
  }
  if (!chapter.title) {
    alert('请填写章节标题！')
    return
  }
  try {
    const res = await GenerateChapterApi({
      main_title: mainTitle.value,
      chapter_title: chapter.title,
      chapter_instruction: chapter.instruction || ''
    })
    chapters.value[chapterIndex].content = res.response
    alert(`章节${chapterIndex+1}内容生成成功！`)
  } catch (error) {
    console.error(error)
    alert('生成功能异常，请重试')
  }
}

async function regenerateChapterContent(chapterIndex: number) {
  chapters.value[chapterIndex].content = ''
  await generateChapterContent(chapterIndex)
}

function goBack() {
  router.push({ name: 'Index' })
}

function removeChapter(index: number) {
  chapters.value.splice(index, 1)
}

function addChapter() {
  if (chapters.value.length < maxChapters) {
    chapters.value.push({ title: '', instruction: '', content: '' })
  } else {
    alert('最多只能添加5个章节')
  }
}

function exportMarkdown() {
  generateMarkdownDocument(
    mainTitle.value, 
    chapters.value.map(chapter => ({ 
      title: chapter.title, 
      content: chapter.content 
    }))
  )
}

function exportWord() {
  adVideoUrl.value = adVideoList[Math.floor(Math.random() * adVideoList.length)]
  showAdDialog.value = true
  canExport.value = false
  // 每次打开弹窗时重置视频
  setTimeout(() => {
    if (adVideoRef.value) {
      adVideoRef.value.pause()
      adVideoRef.value.currentTime = 0
      adVideoRef.value.load()
    }
  }, 0)
}

function onAdEnded() {
  canExport.value = true
}

async function confirmExportWord() {
  showAdDialog.value = false
  await generateWordDocument(
    mainTitle.value, 
    chapters.value.map(chapter => ({ 
      title: chapter.title, 
      content: chapter.content 
    }))
  )
  alert('Word 文档导出成功！')
}

// 关闭广告弹窗时，强制暂停视频
function handleAdDialogClose() {
  showAdDialog.value = false
  if (adVideoRef.value) {
    adVideoRef.value.pause()
    adVideoRef.value.currentTime = 0
  }
}

function saveToLocalStorage() {
  const data = {
    mainTitle: mainTitle.value,
    chapters: chapters.value,
    lastUpdated: new Date().toISOString()
  }
  localStorage.setItem('writingAssistantData', JSON.stringify(data))
}

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

function clearAll() {
  if (confirm('确定要清空所有内容吗？此操作不可撤销哦！')) {
    localStorage.removeItem('writingAssistantData')
    mainTitle.value = ''
    chapters.value = [{ title: '', instruction: '', content: '' }]
  }
}

function goToBatchQA() {
  router.push({ name: 'BatchQA' })
}

onMounted(() => {
  loadFromLocalStorage()
})

watch(
  [mainTitle, chapters], 
  () => {
    saveToLocalStorage()
  },
  { deep: true }
)
</script>

<template>
  <div class="writing-assistant-wrapper">
    <div class="header-actions">
      <el-button type="primary" @click="goToBatchQA" size="large" style="margin-bottom: 16px;">
        <el-icon><Document /></el-icon> &nbsp;批量回答问题
      </el-button>
      <el-button type="primary" @click="goBack" size="large">
        <el-icon><Back /></el-icon> &nbsp;返回
      </el-button>
      <el-button type="danger" @click="clearAll" size="large">
        <el-icon><Delete /></el-icon> &nbsp;一键清空
      </el-button>
    </div>
    
    <el-card class="welcome-card">
      <template #header>
        <div class="welcome-header">
          <span>欢迎，{{ userDisplayName }}！开始您的论文写作助手之旅吧！</span>
        </div>
      </template>
      <p>当前写作助手支持<strong class="highlight-text">写作记录自动保存</strong>，如要删除已有内容，可点击右上角的一键清空～</p>
    </el-card>
    
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>论文内容编辑</span>
        </div>
      </template>
      
      <el-form label-position="top" class="writing-assistant-form">
        <el-form-item label="论文总标题">
          <el-input v-model="mainTitle" placeholder="请输入论文总标题" size="large"></el-input>
        </el-form-item>
        
        <div v-for="(chapter, index) in chapters" :key="index" class="chapter-box">
          <div class="chapter-header">
            <span class="chapter-number">章节 {{ index + 1 }}</span>
          </div>
          
          <el-form-item label="章节标题">
            <el-input v-model="chapter.title" placeholder="请输入章节标题"></el-input>
          </el-form-item>
          
          <el-form-item label="章节内容说明（可选）">
            <el-input v-model="chapter.instruction" placeholder="请输入生成该章节内容的具体要求或说明" type="textarea" :rows="3"></el-input>
          </el-form-item>
          
          <div class="chapter-actions">
            <el-button type="success" @click="generateChapterContent(index)" size="default">
              <el-icon><MessageBox /></el-icon> &nbsp;生成该章节内容
            </el-button>
            <el-button type="danger" @click="removeChapter(index)" size="default">
              <el-icon><Close /></el-icon> &nbsp;删除章节
            </el-button>
          </div>
        </div>
        
        <el-button 
          type="primary" 
          @click="addChapter" 
          v-if="chapters.length < maxChapters"
          class="add-chapter-btn"
          size="large"
        >
          <el-icon><Plus /></el-icon> &nbsp;添加章节
        </el-button>
      </el-form>
    </el-card>
    
    <el-card v-if="chapters.some(chapter => chapter.content)" class="content-card preview-card">
      <template #header>
        <div class="card-header">
          <span>生成内容预览</span>
        </div>
      </template>
      
      <div v-for="(chapter, index) in chapters" :key="'content-' + index" class="preview-chapter">
        <template v-if="chapter.content">
          <div class="preview-chapter-header">
            <span class="chapter-number">章节 {{ index + 1 }}</span>
            <span class="chapter-title">{{ chapter.title }}</span>
          </div>
          
          <el-input 
            type="textarea" 
            v-model="chapter.content" 
            :rows="8"
            class="content-textarea"
          ></el-input>
          
          <div class="regenerate-actions">
            <el-button type="info" @click="regenerateChapterContent(index)">
              <el-icon><Refresh /></el-icon> &nbsp;不满意？重新生成
            </el-button>
          </div>
        </template>
      </div>
      
      <div class="export-actions">
        <el-button type="warning" @click="exportMarkdown" size="large">
          <el-icon><Document /></el-icon> &nbsp;导出 Markdown 文件
        </el-button>
        <el-button type="primary" @click="exportWord" size="large">
          <el-icon><Download /></el-icon> &nbsp;导出 Word 文档
        </el-button>
      </div>
    </el-card>
    
    <div class="trademark-container">
      <img src="@/assets/images/trademark.jpg" alt="trademark" class="floating-trademark" />
    </div>
  </div>
  <el-dialog 
    v-model="showAdDialog" 
    title="Word文档导出难度较高，观看广告后才可导出哦～" 
    width="600px" 
    :close-on-click-modal="true" 
    :show-close="true"
    @close="handleAdDialogClose"
  >
    <video
      width="100%"
      controls
      ref="adVideoRef"
      @ended="onAdEnded"
      :src="adVideoUrl"
      style="border-radius: 8px;"
    ></video>
    <div style="margin-top: 8px; text-align: left; font-size: 12px; color: #909399;">
      提示：可使用快进
    </div>
    <div style="margin-top: 16px; text-align: right;">
      <el-button type="primary" :disabled="!canExport" @click="confirmExportWord">导出Word文档</el-button>
    </div>
  </el-dialog>
</template>

<style scoped>
.writing-assistant-wrapper {
  position: relative;
  padding: 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  min-height: 100vh;
}

/* 卡片统一样式 */
.content-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.welcome-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.welcome-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
}

/* 标签高亮 */
.highlight-text {
  color: #fa8c16;
}

/* 章节样式 */
.chapter-box {
  margin-bottom: 24px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  background-color: #fafafa;
  transition: all 0.3s;
}

.chapter-box:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.chapter-header {
  margin-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
}

.chapter-number {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin-right: 8px;
}

.chapter-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

/* 预览区域样式 */
.preview-card {
  background-color: #ffffff;
}

.preview-chapter {
  margin-bottom: 32px;
}

.preview-chapter:last-child {
  margin-bottom: 16px;
}

.preview-chapter-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.chapter-title {
  font-size: 16px;
  font-weight: 500;
  color: #434343;
}

.content-textarea {
  border-radius: 4px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.regenerate-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

/* 导出按钮区域 */
.export-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px dashed #f0f0f0;
}

/* 添加章节按钮 */
.add-chapter-btn {
  width: 100%;
  margin-top: 8px;
}

/* 商标 */
.trademark-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.floating-trademark {
  height: 60px;
  opacity: 0.85;
  border-radius: 4px;
}

/* 覆盖element-plus组件库样式 */
:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>