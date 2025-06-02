<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { BatchGenerateApi } from '@/request/api'

const questions = ref<any[]>([])
const chapterRows = ref<any[]>([])
const loading = ref(false)
const progress = ref(0)

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
  answers.value = []
  for (let i = 0; i < questions.value.length; i++) {
    try {
      const res = await BatchGenerateApi([questions.value[i]])
      answers.value[i] = res.data.data[0] // 注意：res.data.data 是后端返回的data字段
      progress.value = Math.round(((i + 1) / questions.value.length) * 100)
    } catch (e) {
      answers.value[i] = ['生成失败']
    }
  }
  loading.value = false
  ElMessage.success('批量生成完成')
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
      <span v-if="loading" style="margin-left: 16px;">进度：{{ progress }}%</span>
    </div>

    <!-- 生成结果展示区域 -->
    <div v-if="answers.length > 0" style="margin-top: 32px;">
      <h3>AI批量生成结果</h3>
      <div v-for="(answerArr, qIdx) in answers" :key="qIdx" class="answer-block">
        <h4>问题 {{ qIdx + 1 }}</h4>
          <div v-for="(chapterAnswer, cIdx) in answerArr" :key="cIdx" class="chapter-answer">
            <b>章节 {{ cIdx + 1 }}：</b>
          <div style="white-space: pre-wrap; background: #f8f8f8; border-radius: 4px; padding: 8px; margin-bottom: 8px;">
            {{ chapterAnswer }}
          </div>
        </div>
      </div>
    </div>
  </div>
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
</style>