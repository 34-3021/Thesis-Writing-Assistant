import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models

def clear_sql_and_chroma():
    db: Session = SessionLocal()
    try:
        # 获取所有论文ID
        papers = db.query(models.Paper).all()
        paper_ids = [str(paper.id) for paper in papers]
        print(f"准备删除SQL库中的{len(paper_ids)}篇论文...")

        # 删除SQL中的所有论文
        db.query(models.Paper).delete()
        db.commit()
        print("已清空SQL论文表。")

        # 删除Chroma向量库中的所有对应向量
        if paper_ids:
            try:
                from backend_algo.retrieval import get_or_create_collection
                collection = get_or_create_collection()
                collection.delete(ids=paper_ids)
                print(f"已同步删除Chroma中{len(paper_ids)}条向量。")
            except Exception as e:
                print(f"删除Chroma向量失败: {e}")
        else:
            print("SQL库中无论文，无需同步删除Chroma。")
    except Exception as e:
        print(f"清空失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_sql_and_chroma()