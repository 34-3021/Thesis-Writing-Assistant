import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from vectorizer import embed_text
from retrieval import get_or_create_collection

def import_papers_to_vector_db():
    """从关系数据库读取论文，向量化后存入向量数据库"""
    db: Session = SessionLocal()
    try:
        # 获取所有论文
        papers = db.query(models.Paper).all()
        if not papers:
            print("数据库中没有论文。")
            return
        
        # 获取向量数据库集合
        collection = get_or_create_collection()
        
        # 处理每篇论文
        for paper in papers:
            try:
                # 将论文内容向量化
                paper_text = f"标题: {paper.title}\n摘要: {paper.abstract}\n内容: {paper.content}"
                
                # 检查该ID是否已存在
                try:
                    existing = collection.get(ids=[str(paper.id)])
                    if existing['ids']:
                        print(f"论文ID {paper.id} 已存在于向量数据库，跳过")
                        continue
                except:
                    pass  # ID不存在，继续处理
                
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
                print(f"成功导入论文 ID: {paper.id}, 标题: {paper.title}")
            
            except Exception as e:
                print(f"导入论文ID {paper.id} 失败: {str(e)}")
                continue
                
        print("完成向量数据库导入")
        
    except Exception as e:
        print(f"导入过程出错: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import_papers_to_vector_db()