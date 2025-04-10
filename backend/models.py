from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.sql import func
# 将相对导入改为绝对导入
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(256), unique=True, index=True)
    first_name = Column(String(128))
    last_name = Column(String(128))
    hashed_password = Column(String(256))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

# 新增论文模型
class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    author = Column(String(128))
    abstract = Column(Text)
    content = Column(Text)  # 解析后的全文
    file_path = Column(String(256))  # 原文档存储路径（可选）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    