import os
import sys
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

import crud, models, schemas
from database import SessionLocal, engine
from security import verify_password

import requests
from backend_algo.schemas import GenerateChapterRequest, ChatResponse
# 导入向量检索函数
from backend_algo.retrieval import search_similar_papers
# 新增：导入向量化函数
from backend_algo.vectorizer import embed_text

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 自动创建数据库表
models.Base.metadata.create_all(bind=engine)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

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
    return paper

# 修改后的生成章节接口：在业务层中整合数据库中的论文，并附加向量化后的信息
@app.post("/generate-chapter", response_model=ChatResponse)
async def generate_chapter_endpoint(
    request: GenerateChapterRequest,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    # 构造检索用文本，组合用户输入信息
    query_text = f"{request.main_title} {request.chapter_title} {request.chapter_instruction}"
    retrieval_results = search_similar_papers(query_text, n_results=3)
    similar_ids = retrieval_results.get("ids", [[]])[0]
    
    # 遍历检索到的论文，获取向量化后的数据（示例：取前5个数）
    related_info = ""
    for pid in similar_ids:
        try:
            paper = db.query(models.Paper).filter(models.Paper.id == int(pid)).first()
        except Exception:
            paper = None
        if paper:
            vector = embed_text(paper.content)
            vector_list = vector.tolist()
            truncated_vector = vector_list[:5]
            related_info += f"论文标题：{paper.title}\n摘要：{paper.abstract}\n向量数据：{truncated_vector}\n\n"
    
    # 构造最终提示，包含用户输入和论文向量化数据
    final_prompt = (
        f"论文题目：{request.main_title}\n"
        f"章节标题：{request.chapter_title}\n"
        f"要求：{request.chapter_instruction}\n"
    )
    if related_info:
        final_prompt += "请参考以下相关论文（附向量数据）：\n" + related_info
    final_prompt += "请根据上述信息生成详细的章节内容。"
    
    payload = {
        "main_title": request.main_title,
        "chapter_title": request.chapter_title,
        "chapter_instruction": request.chapter_instruction,
        "prompt": final_prompt
    }
    resp = requests.post('http://localhost:8001/chat/generate-chapter', json=payload, timeout=60)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="算法层错误")
    return resp.json()