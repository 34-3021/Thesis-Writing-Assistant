<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { BatchGenerateApi } from '@/request/api'
import { useRouter } from 'vue-router'

const router = useRouter()
const questions = ref<any[]>([])
const chapterRows = ref<any[]>([])
const loading = ref(false)
const progress = ref(0)
const stopFlag = ref(false) // 新增，用于控制批量生成的停止
const evalDialogVisible = ref(false)
const evalResults = ref<any[]>([])

// 单题测试弹窗相关
const showTestDialog = ref(false)
const testChapters = ref([
  { title: '', instruction: '', r: '' }
])
const testAnswers = ref<string[]>([])

function addTestChapter() {
  testChapters.value.push({ title: '', instruction: '', r: '' })
}
function removeTestChapter(idx: number) {
  if (testChapters.value.length > 1) testChapters.value.splice(idx, 1)
}
async function generateTestAnswers() {
  // 构造与后端一致的请求结构
  const q = {
    Q: testChapters.value.map(ch => [ch.title, ch.instruction]),
    R: testChapters.value.map(ch => ch.r.split(',').map(v => Number(v.trim())))
  }
  try {
    const res = await BatchGenerateApi([q])
    testAnswers.value = res.data.data[0]
  } catch (e) {
    testAnswers.value = ['生成失败']
  }
}

// 评测结果展示
async function evaluateResults() {
  if (!answers.value.length) {
    ElMessage.warning('请先批量生成AI答案')
    return
  }
  try {
    const res = await fetch('/api/evaluate-batch-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(answers.value)
    })
    const data = await res.json()
    evalResults.value = data.results
    evalDialogVisible.value = true
  } catch (e) {
    ElMessage.error('评测失败，请检查后端接口')
  }
}

// 页面加载时获取问题
async function fetchQuestions() {
  try {
    const res = await fetch('/api/questions')
    if (!res.ok) throw new Error('接口请求失败')
    const data = await res.json()
    questions.value = data
    chapterRows.value = []
    questions.value.forEach((q, qIdx) => {
      q.Q.forEach((chapter: any, cIdx: number) => {
        chapterRows.value.push({
          qIdx,
          cIdx,
          title: chapter[0],
          instruction: chapter[1],
          r: q.R[cIdx] ? q.R[cIdx].join(',') : ''
        })
      })
    })
  } catch (e) {
    ElMessage.error('加载问题库失败，请检查后端接口和questions.json文件')
  }
}
fetchQuestions()

// 导出评测结果为CSV
function exportEvalResults() {
  if (!evalResults.value.length) {
    ElMessage.warning('暂无评测结果')
    return
  }
  let csv = '问题编号,章节编号,BERTScore,ROUGE-L,ROUGE-1,ROUGE-2\n'
  evalResults.value.forEach((qResult, qIdx) => {
    (qResult as any[]).forEach((chapter, cIdx) => {
      const bert = chapter.bert_score !== undefined && chapter.bert_score !== -1 ? chapter.bert_score.toFixed(4) : 'N/A'
      csv += `${qIdx + 1},${cIdx + 1},${bert},${chapter.rougeL.toFixed(4)},${chapter.rouge1.toFixed(4)},${chapter.rouge2.toFixed(4)}\n`
    })
  })
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `评测结果_${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function updateChapterField(row: any, key: 'title'|'instruction'|'r', value: string) {
  if (key === 'r') {
    questions.value[row.qIdx].R[row.cIdx] = value.split(',').map(v => Number(v.trim()))
    row.r = value
  } else if (key === 'title') {
    questions.value[row.qIdx].Q[row.cIdx][0] = value
    row.title = value
  } else if (key === 'instruction') {
    questions.value[row.qIdx].Q[row.cIdx][1] = value
    row.instruction = value
  }
}

const answers = ref<string[][]>([])
async function batchGenerate() {
  loading.value = true
  stopFlag.value = false
  answers.value = []
  for (let i = 0; i < questions.value.length; i++) {
    if (stopFlag.value) {
      ElMessage.warning('已终止批量生成')
      break
    }
    try {
      const res = await BatchGenerateApi([questions.value[i]])
      answers.value[i] = res.data.data[0]
      progress.value = Math.round(((i + 1) / questions.value.length) * 100)
    } catch (e) {
      answers.value[i] = ['生成失败']
    }
  }
  loading.value = false
  ElMessage.success('批量生成完成')
}

function stopBatchGenerate() {
  stopFlag.value = true
}

function goBack() {
  router.push({ name: 'WritingAssistant' })
}
</script>

<template>
  <div style="padding: 24px;">
    <h2>批量问题编辑与AI批量回答</h2>
    <table class="custom-table">
      <thead>
        <tr>
          <th style="width:60px;">问题序号</th>
          <th style="width:120px;">章节编号</th>
          <th style="width:180px;">章节标题</th>
          <th style="width:320px;">章节内容要求</th>
          <th style="width:140px;">参考论文编号</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(q, qIdx) in questions">
          <tr>
            <td :rowspan="q.Q.length" style="vertical-align: top; font-weight: bold;">{{ qIdx + 1 }}</td>
            <td>1</td>
            <td>
              <el-input v-model="q.Q[0][0]" @change="updateChapterField({ qIdx: qIdx, cIdx: 0 }, 'title', q.Q[0][0])" size="small" />
            </td>
            <td>
              <el-input v-model="q.Q[0][1]" @change="updateChapterField({ qIdx: qIdx, cIdx: 0 }, 'instruction', q.Q[0][1])" size="small" />
            </td>
            <td>
              <el-input v-model="q.R[0]" @change="updateChapterField({ qIdx: qIdx, cIdx: 0 }, 'r', q.R[0].join(','))" size="small" />
            </td>
          </tr>
          <tr v-for="(chapter, cIdx) in q.Q.slice(1)" :key="cIdx">
            <td>{{ cIdx + 2 }}</td>
            <td>
              <el-input v-model="q.Q[cIdx+1][0]" @change="updateChapterField({ qIdx: qIdx, cIdx: cIdx+1 }, 'title', q.Q[cIdx+1][0])" size="small" />
            </td>
            <td>
              <el-input v-model="q.Q[cIdx+1][1]" @change="updateChapterField({ qIdx: qIdx, cIdx: cIdx+1 }, 'instruction', q.Q[cIdx+1][1])" size="small" />
            </td>
            <td>
              <el-input v-model="q.R[cIdx+1]" @change="updateChapterField({ qIdx: qIdx, cIdx: cIdx+1 }, 'r', q.R[cIdx+1].join(','))" size="small" />
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <div style="margin: 24px 0;">
      <el-button type="primary" @click="batchGenerate" :loading="loading">一键批量回答</el-button>
      <el-button type="danger" @click="stopBatchGenerate" :disabled="!loading" style="margin-left: 8px;">终止批量回答</el-button>
      <el-button type="default" @click="goBack" style="margin-left: 8px;">返回写作助手</el-button>
      <el-button type="success" @click="evaluateResults" :disabled="answers.length === 0" style="margin-left: 8px;">显示评测结果</el-button>
      <el-button type="primary" @click="showTestDialog = true" style="margin-left: 8px;">助教专用：单题测试</el-button>
      <span v-if="loading" style="margin-left: 16px;">进度：{{ progress }}%</span>
    </div>

    <!-- 生成结果展示区域 -->
    <div v-if="answers.length > 0" style="margin-top: 32px;">
      <h3>AI批量生成结果</h3>
      <div v-for="(answerArr, qIdx) in answers" :key="qIdx" class="answer-block">
        <h4>问题 {{ qIdx + 1 }}</h4>
          <div v-for="(chapterAnswer, cIdx) in answerArr" :key="cIdx" class="chapter-answer">
            <b>章节 {{ cIdx + 1 }}：</b>
            <!-- 新增补充信息 -->
            <div class="chapter-meta">
              <div>章节标题：{{ questions[qIdx].Q[cIdx][0] }}</div>
              <div>用户提示词：{{ questions[qIdx].Q[cIdx][1] }}</div>
              <div>AI可见的参考论文：{{ questions[qIdx].R[cIdx].join(', ') }}</div>
            </div>
            <div style="white-space: pre-wrap; background: #f8f8f8; border-radius: 4px; padding: 8px; margin-bottom: 8px;">
              {{ chapterAnswer }}
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 评测结果对话框 -->
    <el-dialog v-model="evalDialogVisible" title="AI生成内容评测结果" width="60%">
      <div v-if="evalResults.length > 0">
        <table class="custom-table">
          <thead>
            <tr>
              <th>问题编号</th>
              <th>章节编号</th>
              <th>BERTScore</th>
              <th>ROUGE-L</th>
              <th>ROUGE-1</th>
              <th>ROUGE-2</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(qResult, qIdx) in evalResults" :key="qIdx">
              <tr v-for="(chapter, cIdx) in qResult" :key="`${qIdx}-${cIdx}`">
                <td>{{ qIdx + 1 }}</td>
                <td>{{ cIdx + 1 }}</td>
                <td>{{ chapter.bert_score !== undefined && chapter.bert_score !== -1 ? chapter.bert_score.toFixed(4) : 'N/A' }}</td>
                <td>{{ chapter.rougeL.toFixed(4) }}</td>
                <td>{{ chapter.rouge1.toFixed(4) }}</td>
                <td>{{ chapter.rouge2.toFixed(4) }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="exportEvalResults">导出评测结果</el-button>
        <el-button @click="evalDialogVisible = false">关闭</el-button>
      </span>
    </el-dialog>
    <el-dialog v-model="showTestDialog" title="单题测试" width="700px">
      <div v-for="(ch, idx) in testChapters" :key="idx" style="margin-bottom: 16px; border-bottom: 1px dashed #eee;">
        <el-form label-position="top">
          <el-form-item label="章节标题">
            <el-input v-model="ch.title" placeholder="请输入章节标题"></el-input>
          </el-form-item>
          <el-form-item label="章节内容要求">
            <el-input v-model="ch.instruction" placeholder="请输入章节内容要求"></el-input>
          </el-form-item>
          <el-form-item label="参考论文编号">
            <el-input v-model="ch.r" placeholder="如：5,8,9（用英文逗号分隔）"></el-input>
          </el-form-item>
          <div style="text-align:right;">
            <el-button type="danger" @click="removeTestChapter(idx)" :disabled="testChapters.length===1">删除章节</el-button>
          </div>
        </el-form>
      </div>
      <div style="text-align:right;">
        <el-button type="primary" @click="addTestChapter">添加章节</el-button>
        <el-button type="success" @click="generateTestAnswers">生成各章节内容</el-button>
      </div>
      <div v-if="testAnswers.length" style="margin-top:24px;">
        <h4>生成结果：</h4>
        <div v-for="(ans, idx) in testAnswers" :key="idx" style="background:#f8f8f8; margin-bottom:8px; border-radius:4px; padding:8px;">
          <b>章节{{idx+1}}：</b>
          <div style="white-space:pre-wrap;">{{ ans }}</div>
        </div>
      </div>
    </el-dialog>
</template>

<style scoped>
.custom-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 24px;
}
.custom-table th, .custom-table td {
  border: 1px solid #ebeef5;
  padding: 8px;
}
.answer-block {
  margin-bottom: 32px;
  border-bottom: 1px solid #eee;
  padding-bottom: 16px;
}
.chapter-answer {
  margin-bottom: 8px;
}
.chapter-meta {
  font-size: 13px;
  color: #888;
  margin-bottom: 4px;
  line-height: 1.6;
}
</style>