# 添加必要的导入
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1" # 重要：让transformers库在离线模式下运行，只用本地缓存
import json
import shutil
from fastapi import File, UploadFile, Request, Body # Body用于处理请求体
from bert_score import score as bert_score # 需要安装 bert-score 库（外网）
from rouge_chinese import Rouge
import threading
from datetime import datetime  # 确保已导入
from backend_algo.vectorizer import embed_text
import tiktoken
import sys
import re # 用于清理引用格式
import csv # 加载 mapping.csv，用于建立逻辑编号到 file_path 的映射
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta, timezone
from typing import Annotated
from typing import List, Annotated  # 确保List被导入

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from sqlalchemy.orm import Session

import backend.crud as crud
import backend.models as models
import backend.schemas as schemas
from backend.database import SessionLocal, engine
from backend.security import verify_password

import requests
from backend_algo.schemas import GenerateChapterRequest, ChatResponse
# 导入向量检索函数
from backend_algo.retrieval import search_similar_papers
# 新增：导入向量化函数
from backend_algo.vectorizer import embed_text

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

rouge = Rouge()

# 自动创建数据库表
models.Base.metadata.create_all(bind=engine)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

number_to_file = {}
with open('papers/mapping.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # 跳过表头
    for row in reader:
        # 假设第一列是编号文件名，如 paper_005.pdf
        num = int(row[0].replace('paper_', '').replace('.pdf', ''))
        number_to_file[num] = row[0]

def truncate_to_token_limit(text, max_tokens=8192, model_name="text-embedding-ada-002"):
    enc = tiktoken.encoding_for_model(model_name)
    tokens = enc.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return enc.decode(tokens)

def get_session():
    with SessionLocal() as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 构建参考文献列表的函数
def build_reference_list(ref_ids, db):
    refs = []
    for logic_id in ref_ids:
        file_name = number_to_file.get(logic_id)
        if not file_name:
            continue
        paper = db.query(models.Paper).filter(models.Paper.file_path.like(f"%{file_name}%")).first()
        if paper:
            ref = f"[{logic_id}]{paper.author if paper.author else '未知'}，{paper.title if paper.title else file_name}"
            # 如有url字段可加上
            refs.append(ref)
    if refs:
        return "参考文献：\n" + "\n".join(refs)
    else:
        return ""

def strip_reference(text):
    # 去除“参考文献”及其后内容
    idx = text.find("参考文献")
    if idx != -1:
        return text[:idx].strip()
    return text.strip()

import jieba
def clean_for_rouge(text):
    # 不去除“参考文献”及其后内容
    # jieba分词
    text = ' '.join(jieba.cut(text))
    return text.strip()

# 清理引用格式的函数
def clean_references(text, allowed_ids):
    # 0. 先把所有多余右中括号（如[5]]、[8]]）变成[5]、[8]
    text = re.sub(r'\[(\d+)\]+', r'[\1]', text)

    # 1. 去除所有markdown标题、编号、列表等结构
    text = re.sub(r'^#{1,6}\s*.*$', '', text, flags=re.MULTILINE)  # 去除所有#标题行
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)      # 去除编号列表
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)       # 去除无序列表
    text = re.sub(r'^\s*$', '', text, flags=re.MULTILINE)          # 去除空行

    # 2. 强力去除正文中所有“参考文献”及其下方编号行（包括“参考文献：”等变体）
    text = re.sub(r'参考文献[:：]?\s*(\n\s*\[\d+\].*)*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'#+\s*\d*\s*参考文献.*(\n(\[.*\].*)?)*', '', text, flags=re.IGNORECASE)
    # 把有“参考”或“引用文献”字样的行也全部去除（包括“参考：”“引用文献：[2]”等）
    text = re.sub(r'^\s*(参考|引用文献|引用|文献)[^，。；:：\d\[]*[:：]?\s*(\[\d+\])?.*\n?', '', text, flags=re.MULTILINE)
    # 去除正文中单独成行的“作者. 题目. ...”等伪文献条目
    text = re.sub(r'^[\u4e00-\u9fa5A-Za-z·、，,.\s]{2,20}[.．]\s*.+[.。]\s*\n?', '', text, flags=re.MULTILINE)

    # 3. 处理所有括号包裹的引用（如（[5,14]）、([5][14])、（[5][14]）等，支持中英文括号、逗号、空格）
    def multi_ref_repl(m):
        nums = re.findall(r'\[(\d+)\]', m.group(0))
        seen = set()
        nums = [int(x) for x in nums if int(x) in allowed_ids and not (x in seen or seen.add(x))]
        return ''.join(f'[{n}]' for n in nums)
    text = re.sub(r'[（(][^）)]*[）)]', multi_ref_repl, text)

    # 4. 替换所有（[x]）、([x])、［x］、【x】、｛x｝等为[x]
    text = re.sub(r'[（(【［\[]\s*(\d+)\s*[）)】］\]]', r'[\1]', text)

    # 5. 去除“见论文[14]”“（见论文[14]）”等花样引用
    text = re.sub(r'（?见论文\[(\d+)\]）?', lambda m: f"[{m.group(1)}]" if int(m.group(1)) in allowed_ids else '', text)
    text = re.sub(r'如论文\[(\d+)\]所述', lambda m: f"[{m.group(1)}]" if int(m.group(1)) in allowed_ids else '', text)

    # 6. 只保留 [数字] 格式且数字在 allowed_ids（去除如[e1]等非数字引用）
    def repl(m):
        nums = [int(x) for x in re.findall(r'\d+', m.group(0))]
        seen = set()
        nums = [x for x in nums if x in allowed_ids and not (x in seen or seen.add(x))]
        if nums:
            return ''.join(f'[{n}]' for n in nums)
        else:
            return ''
    text = re.sub(r'[\[\［][^\]\］]+[\]\］]', repl, text)

    # 7. 去除 paper_050 等
    text = re.sub(r'paper_\d{3}', '', text)

    # 8. 去除正文中单独成行的引用编号（如"[16] [17]"、"[19][20]"等）
    text = re.sub(r'^\s*(?:\[\d+\]\s*){1,}\s*$', '', text, flags=re.MULTILINE)

    # 9. 参考文献部分只保留 [x]作者，论文标题（可选加网址）
    lines = text.splitlines()
    in_ref = False
    new_lines = []
    for line in lines:
        if '参考文献' in line:
            in_ref = True
            new_lines.append(line)
            continue
        if in_ref:
            m = re.match(r'\[(\d+)\](.*?)[，,](.*?)(https?://\S+)?', line)
            if m and int(m.group(1)) in allowed_ids:
                ref_line = f"[{m.group(1)}]{m.group(2).strip()}，{m.group(3).strip()}" 
                if m.group(4):
                    ref_line += f" {m.group(4)}"
                new_lines.append(ref_line)
            # 跳过其它参考文献行
        else:
            new_lines.append(line)
    text = '\n'.join(new_lines)

    # 10. 去除所有行内markdown加粗/斜体/删除线等
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    # # 11. 去除每段开头的 [数字][数字]... 或 纯数字编号（如 43. 45. 43、45) 及其变体
    # text = re.sub(r'^(?:\[\d+\]){1,}\s*', '', text, flags=re.MULTILINE)  # 行首连续引用
    # text = re.sub(r'^\s*\d+[\.\、\)]\s*', '', text, flags=re.MULTILINE)   # 行首数字+点/顿号/括号
    # text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)           # 行首纯数字单独成行

    return text

# 调用reranker服务对候选论文进行重排序，返回排序后的论文列表
def rerank_papers(query, candidate_papers, top_n=3):
    rerank_url = "http://localhost:8001/v1/rerank"  # 替换为你的实际reranker服务地址
    payload = {
        "model": "bge-reranker-v2-m3",
        "query": query,
        "documents": [f"标题: {p['title']}\n内容: {p['content']}" for p in candidate_papers],
        "top_n": top_n
    }
    try:
        resp = requests.post(rerank_url, json=payload, timeout=30)
        resp.raise_for_status()
        rerank_result = resp.json()
        reranked_docs = rerank_result['reranked_documents']
        # 按顺序返回排序后的论文对象
        reranked_papers = []
        for doc in reranked_docs:
            for p in candidate_papers:
                if doc.startswith(f"标题: {p['title']}"):
                    reranked_papers.append(p)
                    break
        return reranked_papers
    except Exception as e:
        print(f"Reranker调用失败，降级为embedding排序: {e}")
        # 只返回前top_n个候选论文
        return candidate_papers[:top_n]

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: Annotated[schemas.User, Depends(get_current_active_user)]):
    return current_user

# 获取问题列表
@app.get("/questions")
async def get_questions():
    import json
    with open("papers/questions.json", "r", encoding="utf-8") as f:
        return json.load(f)
    
# 批量生成答案
@app.post("/batch-generate")
async def batch_generate(request: Request, current_user: Annotated[schemas.User, Depends(get_current_active_user)], db: SessionDep):
    data = await request.json()
    questions = data.get("questions", [])
    results = []
    save_records = []  # 新增，用于保存生成的章节记录
    for q in questions:
        chapter_results = []
        for idx, chapter in enumerate(q["Q"]):
            all_ref_ids = q["R"][idx] if isinstance(q["R"][idx], list) else [q["R"][idx]]
            # 1. 先获取这10篇论文的内容
            papers = []
            for logic_id in all_ref_ids:
                file_name = number_to_file.get(logic_id)
                if not file_name:
                    continue
                paper = db.query(models.Paper).filter(models.Paper.file_path.like(f"%{file_name}%")).first()
                if paper:
                    papers.append({
                        "id": logic_id,
                        "title": paper.title,
                        "content": paper.content[:8000]
                    })
            # 2. 用向量检索工具筛选最相关的3篇
            # 用章节标题+指引作为检索query
            query_text = chapter[0] + " " + chapter[1]
            # 只在这10篇中检索，需传入限定的id和内容
            import numpy as np
            from backend_algo.vectorizer import embed_text
            query_vec = embed_text(query_text)
            paper_vecs = [embed_text(p["content"]) for p in papers]
            sims = [float(np.dot(query_vec, v) / (np.linalg.norm(query_vec) * np.linalg.norm(v) + 1e-8)) for v in paper_vecs]
            topk_idx = np.argsort(sims)[-10:][::-1]  # 先召回top10
            candidate_papers = [papers[i] for i in topk_idx]

            # 用reranker重排序，选top3
            selected_papers = rerank_papers(query_text, candidate_papers, top_n=3)
            selected_ids = [p["id"] for p in selected_papers]
            # 3. 拼接内容，只给AI最相关的3篇
            ref_texts = [
                f"[{p['id']}] {p['title']}\n内容片段：{p['content']}\n"
                for p in selected_papers
            ]
            ref_content = "\n".join(ref_texts)
            # 4. 后续prompt拼接与AI调用时，R字段只允许selected_ids
            prompt = (
                f"请严格只参考下列论文（编号见[]）进行写作，不允许引用其它论文：\n{ref_content}\n"
                f"【写作要求】\n章节标题：{chapter[0]}\n章节内容要求：{chapter[1]}\n"
                f"正文引用格式必须统一为：[编号]，如[14]，紧跟在引用句子后面，不允许出现“见论文[14]”“（见论文[14]）”等其它写法。\n"
                f"只允许在正文中引用以下编号：{','.join(str(x) for x in selected_ids)}，严禁出现其它编号或引用。\n"
                "如无内容可引用，不要强行加编号。如果给到的论文与内容完全无关，也无需引用，\n"
                "**引用编号只能紧跟在引用内容句子末尾，不允许出现在段落开头或单独成行，不允许每段开头加编号。**\n"
                "**正文请用自然段落，不要markdown格式，不要分级标题、编号、列表。也不要在文末输出‘参考文献’的小节！**\n"
                "**再次重申：直接回答章节的写作内容。不要任何引入，请勿在文末输出参考文献。请勿在文末输出‘参考文献’的小节。**\n"
                "请生成符合要求的章节内容。"
            )
            # 后续AI调用、clean_references、build_reference_list等逻辑不变，只需把selected_ids传下去
            max_retry = 3
            for retry in range(max_retry):
                req = GenerateChapterRequest(
                    main_title="论文写作助手批量生成",
                    chapter_title=chapter[0],
                    chapter_instruction=chapter[1],
                    prompt=prompt
                )
                resp = await generate_chapter_endpoint(req, current_user, db)
                raw_answer = resp["response"] if isinstance(resp, dict) else resp.response
                cleaned_answer = clean_references(raw_answer, set(selected_ids))
                used_ids = set(int(x) for x in re.findall(r'\[(\d+)\]', cleaned_answer) if int(x) in selected_ids)
                reference_list = build_reference_list(used_ids, db)
                if reference_list.strip():
                    break
            chapter_results.append(cleaned_answer + ("\n\n" + reference_list if reference_list else ""))
        results.append(chapter_results)
        # 保存每个问题的Q/A/R/AI
        save_records.append({
            "Q": q["Q"],
            "A": q.get("A", []),
            "R": q.get("R", []),
            "AI": chapter_results
        })
    # 自动保存到workspace
    save_dir = os.path.join(os.path.dirname(__file__), "../workspace")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(save_records, f, ensure_ascii=False, indent=2)
    return {"data": results}

# 批量评测生成内容
@app.post("/evaluate-batch-generate")
async def evaluate_batch_generate(
    ai_results: list = Body(...),
):
    with open("papers/questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    std_answers = [q["A"] for q in questions]

    results = []
    for i, (ai_ans_list, std_ans_list) in enumerate(zip(ai_results, std_answers)):
        q_result = []
        for j, (ai_text, std_text) in enumerate(zip(ai_ans_list, std_ans_list)):
            # 不去除“参考文献”及其后内容
            ai_main = ai_text.strip()
            std_main = std_text.strip()
            # 仅ROUGE需要分词
            ai_cut = clean_for_rouge(ai_main)
            std_cut = clean_for_rouge(std_main)
            scores = rouge.get_scores(ai_cut, std_cut)[0]
            # BERTScore直接用原文
            try:
                P, R, F1 = bert_score(
                    [ai_main], [std_main],
                    model_type="bert-base-chinese",  # 只写模型名
                    lang="zh",
                    rescale_with_baseline=True
                )
                bert_f1 = float(F1[0])
            except Exception as e:
                print(f"BERTScore计算失败: {e}")
                bert_f1 = -1
            print(f"==== 问题{i+1} 章节{j+1} ====")
            print("AI生成内容（分词后）:", ai_cut)
            print("标准答案（分词后）:", std_cut)
            print(f"RougeL: {scores['rouge-l']['f']:.4f}, Rouge1: {scores['rouge-1']['f']:.4f}, Rouge2: {scores['rouge-2']['f']:.4f}, BERTScore: {bert_f1:.4f}")
            q_result.append({
                "rougeL": float(scores['rouge-l']['f']),
                "rouge1": float(scores['rouge-1']['f']),
                "rouge2": float(scores['rouge-2']['f']),
                "bert_score": bert_f1,
                "ai_text": ai_text,
                "std_text": std_text
            })
        results.append(q_result)
    return {"results": results}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: SessionDep):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/", response_model=schemas.UserList)
async def read_users(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: SessionDep,
        skip: int = 0,
        limit: int = 100,
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return schemas.UserList(total=crud.count_users(db), users=users)

@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)], user_id: int, db: SessionDep):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/users/name/{username}", response_model=schemas.User)
async def read_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)], username: str, db: SessionDep):
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(current_user: Annotated[schemas.User, Depends(get_current_active_user)], chat_request: schemas.ChatRequest):
    resp = requests.post('http://localhost:8001/chat', json={
        'messages': [{'role': 'user', 'content': chat_request.prompt}]
    })
    return schemas.ChatResponse(response=resp.json()['choices'][0]['message']['content'])

@app.get("/papers/", response_model=List[schemas.Paper])
async def get_papers(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """获取论文列表"""
    papers = db.query(models.Paper).offset(skip).limit(limit).all()
    return papers

@app.delete("/papers/{paper_id}", response_model=schemas.Paper)
async def delete_paper(
    paper_id: int,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    """删除指定ID的论文"""
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="论文未找到")
    
    db.delete(paper)
    db.commit()

    # 同步删除Chroma向量
    try:
        from backend_algo.retrieval import get_or_create_collection
        collection = get_or_create_collection()
        collection.delete(ids=[str(paper_id)])
        print(f"已同步删除Chroma中论文ID: {paper_id}")
    except Exception as e:
        print(f"删除Chroma向量失败: {e}")
    return paper

# 修改后的生成章节接口：在业务层中整合数据库中的论文，并附加向量化后的信息
@app.post("/generate-chapter", response_model=ChatResponse)
async def generate_chapter_endpoint(
    request: GenerateChapterRequest,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    payload = {
        "main_title": request.main_title,
        "chapter_title": request.chapter_title,
        "chapter_instruction": request.chapter_instruction,
        "prompt": request.prompt
    }
    resp = requests.post('http://localhost:8001/chat/generate-chapter', json=payload, timeout=60)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="算法层错误")
    return resp.json()

# 确保上传目录存在
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "test_papers")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/papers/upload", response_model=schemas.Paper)
async def upload_paper(
    file: UploadFile,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    """上传论文文件并导入到数据库"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持上传PDF文件")
    
    # 生成唯一文件名避免冲突
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # 保存上传的文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 提取PDF文本内容
        from backend.pdf_parser import extract_pdf_text
        content = extract_pdf_text(file_path)
        
        # 从文件名中提取标题(去掉扩展名)
        title = os.path.splitext(file.filename)[0]
        
        # 简单推断作者(使用上传用户的姓名)
        author = f"{current_user.first_name} {current_user.last_name}"
        
        # 提取摘要
        abstract = content[:800] if content else ""
        
        # 创建论文记录
        paper = crud.create_paper(
            db, 
            title=title,
            author=author, 
            abstract=abstract,
            content=content, 
            file_path=file_path
        )
        
        # 启动向量化处理（异步），避免阻塞响应
        def vectorize_paper():
            try:
                # 导入向量数据库操作模块
                from backend_algo.vectorizer import embed_text
                from backend_algo.retrieval import get_or_create_collection
                
                # 获取向量数据库集合
                collection = get_or_create_collection()
                
                # 将论文内容向量化并存入向量数据库
                paper_text = f"标题: {paper.title}\n内容: {paper.content}"
                
                # 添加到向量数据库
                collection.add(
                    ids=[str(paper.id)],
                    documents=[paper_text],
                    metadatas=[{
                        "title": paper.title,
                        "author": paper.author,
                        "paper_id": paper.id
                    }]
                )
                print(f"成功向量化论文 ID: {paper.id}, 标题: {paper.title}")
            except Exception as e:
                print(f"向量化论文失败: {str(e)}")
        
        # 使用线程异步处理向量化
        thread = threading.Thread(target=vectorize_paper)
        thread.daemon = True
        thread.start()
        
        return paper
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # ← 这里输出详细错误
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"处理论文失败: {str(e)}")