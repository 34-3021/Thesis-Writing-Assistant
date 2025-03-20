import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import schemas
import requests

from backend_algo.schemas import GenerateChapterRequest, ChatResponse

app = FastAPI()

URL = 'http://10.176.64.152:11434/v1'
MODEL = 'qwen2.5:7b'

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