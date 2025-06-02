from backend_algo.retrieval import get_or_create_collection
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models

def get_mysql_paper_ids():
    db = SessionLocal()
    ids = [str(p.id) for p in db.query(models.Paper.id).all()]
    db.close()
    return set(ids)

def clean_orphan_vectors():
    collection = get_or_create_collection()
    all_docs = collection.get()
    chroma_ids = set(all_docs['ids'])
    mysql_ids = get_mysql_paper_ids()
    orphan_ids = chroma_ids - mysql_ids
    print(f"MySQL中存在的论文ID: {mysql_ids}")
    print(f"Chroma中所有论文ID: {chroma_ids}")
    print(f"需要删除的僵尸向量ID: {orphan_ids}")
    if orphan_ids:
        collection.delete(ids=list(orphan_ids))
        print(f"已删除{len(orphan_ids)}个僵尸向量。")
    else:
        print("没有需要删除的僵尸向量。")

if __name__ == "__main__":
    clean_orphan_vectors()