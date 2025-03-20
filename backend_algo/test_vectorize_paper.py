# 脚本，测试用
import os
import sys

# 将backend目录添加到sys.path中
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, '../backend')
sys.path.insert(0, os.path.abspath(backend_path))

from sqlalchemy.orm import Session
from database import SessionLocal  # 现在可以正确引用 backend/database.py
import models
from vectorizer import embed_text

def test_vectorize_first_paper():
    db: Session = SessionLocal()
    try:
        paper = db.query(models.Paper).first()
        if not paper:
            print("No paper found in database.")
            return
        print("Paper title:", paper.title)
        # 调用向量化函数
        vector = embed_text(paper.content)
        print("Generated vector shape:", vector.shape)
    finally:
        db.close()

if __name__ == "__main__":
    test_vectorize_first_paper()