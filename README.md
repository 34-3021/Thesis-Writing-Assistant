# AI论文写作助手系统

由“34-3021寝室”集团有限公司中的郭诣丰开发
商标：
![商标](./frontend/src/assets/images/trademark.jpg)

![登录界面展示](./screenshots/login.png) 

## 一、项目简介

本项目为基于大语言模型的智能论文写作平台，采用前端（Vue）、后端业务（FastAPI）、后端算法（FastAPI+向量数据库）三层架构。系统支持论文智能生成、分章节管理、论文库上传与检索、写作记录自动保存、批量生成与评测、文档导出等功能。极大提升学术写作效率。

**本项目的算法与创新性工作详见随包提交的报告文档，README 仅介绍运行方法与基本操作。**

---

## 二、项目结构

```
mysql_fastapi_vue_sample_project/
├── frontend/           # 前端Vue项目
├── backend/            # 后端业务层
├── backend_algo/       # 后端算法层
├── data_vector_db/     # 向量数据库（Chroma相关文件）
├── eval_results/       # 评测结果导出目录（如BERTScore、ROUGE等自动评测结果）
├── papers/             # 数据集文件夹（含mapping.csv、questions.json、questions.txt等）
├── tools/              # 工具脚本文件夹（如download_model.py等辅助脚本）
├── workspace/          # AI生成内容与评测结果自动保存目录
├── 指令.txt            # 启动与常用操作指令说明
└── README.md           # 本说明文档
```

---

## 三、环境准备

Node.js 16+

Python 3.12

MySQL

Chroma 向量数据库

---

## 四、依赖安装

**前端：**
```bash
cd frontend
npm install
```

**后端业务层：**
```bash
cd backend
pip install -r requirements.txt
```
如 requirements.txt 不全，建议手动补充安装以下依赖：
```bash
pip install uvicorn
pip install pymysql
pip install bert-score
pip install rouge-chinese
pip install jieba
pip install tiktoken
pip install requests
pip install openpyxl
pip install docx
pip install python-docx
pip install pandas
pip install PyPDF2
pip install pdfminer.six
pip install jwt
pip install tqdm
pip install python-dotenv
```

**后端算法层：**
```bash
cd backend_algo
pip install -r requirements.txt
```
如 requirements.txt 不全，建议手动补充安装以下依赖：
```bash
pip install transformers
pip install torch
pip install sentence-transformers
pip install chromadb
pip install numpy
```

**其他说明**

若遇到依赖缺失或版本冲突，请根据报错信息补充安装相关包。
推荐使用 Python 3.12 及以上版本，Node.js 16 及以上版本。
若需 GPU 加速，请确保已正确安装 CUDA、torch 等相关依赖。

---

### 五、数据库配置

- 启动MySQL，创建名为`test`的数据库。
- 修改`backend/database.py`中的连接字符串以匹配本地数据库配置。**（重要！）**

---

### 六、启动方法

请严格按照如下顺序启动各部分：

1. **向量数据库（采用Chroma数据库）**
   ```bash
   chroma run --path ./data_vector_db --host localhost --port 8002
   ```
2. **后端算法层**
   ```bash
   uvicorn backend_algo.main:app --port 8001
   ```
3. **后端业务层**
   ```bash
   uvicorn backend.main:app --port 8000
   ```
4. **前端**
   ```bash
   cd frontend
   npm run dev
   ```

（下述内容可供选择）
**导入测试论文并向量化：**
```bash
python backend/insert_test_paper.py # 导入某篇特定论文
python backend_algo/vector_import.py # 向量化导入的论文
python backend/batch_import_papers.py # 批量导入papers文件夹中的所有论文（50篇）
```
注：上述函数仅供后端代码的测试与验证，用户实际使用项目时，直接在前端即可完成论文的导入与向量化。

---

## 七、论文操作与常用功能

1. 论文上传与删除
在前端 PaperLibrary 页面点击上传按钮，选择PDF文件即可自动导入论文并向量化。
删除论文可直接在前端页面点击删除按钮，系统会同步删除数据库和向量库中的记录。

2. 论文批量导入与清理（助教调试/测试用）
批量导入 papers 文件夹下所有论文并向量化： 
```bash
python batch_import_papers.py
```
向量化所有已存在论文（如有新论文手动导入后需补充向量化）： 
```bash
python vector_import.py
```
删除所有论文（数据库与向量库）： 
```bash
python clear_all_papers.py
```
删除向量库中“僵尸”论文（数据库已删但向量库未删的）： 
```bash
python -m backend_algo.clean_chroma_orphan_vectors
```
检查当前向量数据库中存在的所有论文：
```bash
python -m backend_algo.check_vector_db
```

3. 论文内容生成与批量问答
在 WritingAssistant 页面输入论文总标题、章节标题与内容要求，点击生成即可获得AI写作内容。
在 BatchQA 页面可批量编辑问题、参考编号，点击“一键批量回答”即可批量生成所有章节内容。
支持单题测试弹窗，便于助教现场输入自定义章节进行测试。

4. 评测与导出
批量生成后可点击“显示评测结果”自动评测AI内容与标准答案的BERTScore、ROUGE等指标。
支持一键导出评测结果为CSV，支持导出AI生成内容为Word/Markdown文档。

---

## 八、其他说明

1. 本项目的算法实现、创新点与详细功能介绍请参见随包提交的报告文档。
2. 各部分启动顺序不可颠倒，建议严格按“指令.txt”操作。
3. 论文库和写作内容均可自动保存，建议定期导出备份。
4. 若需清空所有论文或向量库内容，建议先备份数据。

---

## 九、开发者与致谢

本项目由“34-3021寝室”集团有限公司中的郭诣丰开发，作为数据库引论课程项目。
感谢老师、二位助教与开源社区（34-3021寝室）的支持。
欲商业化项目，请先给分满分，随后联系电话19945700324（郭诣丰）。

---

## 十、许可证

本项目采用 “34-3021寝室-MIT” 许可证开源。
