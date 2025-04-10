from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal

def delete_papers(ids_to_delete):
    db: Session = SessionLocal()
    try:
        for paper_id in ids_to_delete:
            # 使用 text() 函数明确声明 SQL 语句
            db.execute(text(f"DELETE FROM papers WHERE id = {paper_id}"))
        db.commit()
        print(f"成功删除论文 ID: {ids_to_delete}")
    except Exception as e:
        print(f"删除失败: {e}")
        db.rollback()
    finally:
        db.close()

delete_papers([100])