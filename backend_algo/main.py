import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"  # 确保 transformers 使用本地模型而不是在线下载
import sys
import uvicorn
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import backend_algo.schemas as schemas
import requests

from pydantic import BaseModel
from backend_algo.schemas import GenerateChapterRequest, ChatResponse

app = FastAPI()

URL = 'http://10.176.64.152:11434/v1'
MODEL = 'qwen2.5:7b'

# 全局加载模型（避免每次请求都加载）
reranker_tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-base")
reranker_model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base")

@app.post("/chat/stream/")
async def chat_stream(conversation: schemas.Conversation):

    def generator():
        with requests.post(f'{URL}/chat/completions', json={
            'model': MODEL,
            'stream': True,
            'messages': [m.model_dump() for m in conversation.messages],
        }, stream=True, timeout=60) as resp:
            for raw_line in resp.iter_lines():
                line = raw_line.decode('utf-8').strip()
                if line == '':
                    continue
                if line.startswith('data: '):
                    line = line[len('data: '):]
                    if line == '[DONE]':
                        yield raw_line + b'\n'
                        break
                else:
                    yield raw_line + b'\n'
                    break
                yield raw_line + b'\n'
    
    return StreamingResponse(generator())

@app.post("/chat/", response_model=schemas.ConversationResponse)
async def chat(conversation: schemas.Conversation):
    resp = requests.post(f'{URL}/chat/completions', json={
        'model': MODEL,
        'stream': False,
        'messages': [m.model_dump() for m in conversation.messages],
    }, stream=False, timeout=60)
    return resp.json()

# 新增接口：使用BGE-Reranker模型对文档进行重排序
def rerank_with_bge(query, documents, top_n=3):
    # 输入：query(str), documents(List[str])
    pairs = [[query, doc] for doc in documents]
    inputs = reranker_tokenizer(pairs, padding=True, truncation=True, return_tensors="pt", max_length=512)
    with torch.no_grad():
        scores = reranker_model(**inputs).logits.squeeze(-1).cpu().numpy()
    topk_idx = scores.argsort()[-top_n:][::-1]
    reranked_documents = [documents[i] for i in topk_idx]
    return reranked_documents

# 新增接口：使用BGE-Reranker模型对文档进行重排序
@app.post("/v1/rerank")
async def rerank(request: Request):
    data = await request.json()
    query = data["query"]
    documents = data["documents"]
    top_n = data.get("top_n", 3)
    # 用BGE-Reranker重排序
    reranked_documents = rerank_with_bge(query, documents, top_n=top_n)
    return {"reranked_documents": reranked_documents}

# 新增接口：生成章节内容，使用请求中提供的扩展提示
@app.post("/chat/generate-chapter", response_model=schemas.ChatResponse)
async def generate_chapter(request: GenerateChapterRequest):
    final_prompt = request.prompt if request.prompt is not None else (
        f"论文题目：{request.main_title}\n"
        f"章节标题：{request.chapter_title}\n"
        f"要求：{request.chapter_instruction}\n"
        "请根据上述信息生成详细的章节内容。"
    )
    resp = requests.post(f'{URL}/chat/completions', json={
        "model": MODEL,
        "stream": False,
        "messages": [{"role": "user", "content": final_prompt}],
    }, timeout=60)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="AI 模型接口错误")
    data = resp.json()
    return schemas.ChatResponse(response=data["choices"][0]["message"]["content"])

# 添加新的请求模型
class PaperVectorizeRequest(BaseModel):
    paper_id: int
    title: str
    author: str
    abstract: str
    content: str

@app.post("/vectorize-paper")
async def vectorize_paper(request: PaperVectorizeRequest):
    """接收论文信息并进行向量化处理"""
    try:
        # 导入向量数据库操作模块
        from vectorizer import embed_text
        from retrieval import get_or_create_collection
        
        # 获取向量数据库集合
        collection = get_or_create_collection()
        
        # 将论文内容向量化并存入向量数据库
        paper_text = f"标题: {request.title}\n摘要: {request.abstract}\n内容: {request.content}"
        
        # 检查ID是否已存在
        try:
            existing = collection.get(ids=[str(request.paper_id)])
            if existing['ids']:
                # 更新现有记录
                collection.delete(ids=[str(request.paper_id)])
        except Exception:
            pass  # ID不存在则继续添加
            
        # 添加到向量数据库
        collection.add(
            ids=[str(request.paper_id)],
            documents=[paper_text],
            metadatas=[{
                "title": request.title,
                "author": request.author,
                "paper_id": request.paper_id
            }]
        )
        
        return {"status": "success", "message": f"论文ID {request.paper_id} 向量化成功"}
    except Exception as e:
        return {"status": "error", "message": str(e)}