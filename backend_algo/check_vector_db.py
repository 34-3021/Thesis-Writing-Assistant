from backend_algo.retrieval import get_or_create_collection

def check_vector_db():
    collection = get_or_create_collection()
    all_docs = collection.get()
    print("向量数据库中所有论文ID：", all_docs['ids'])
    print("向量数据库中所有论文标题：", [m['title'] for m in all_docs['metadatas']])

if __name__ == "__main__":
    check_vector_db()