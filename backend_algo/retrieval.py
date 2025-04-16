# 负责：检索功能的实现
import requests
import numpy as np
import chromadb
import chromadb.utils.embedding_functions as embedding_functions

# 向量化函数，复用你在 vectorizer.py 中的实现
from backend_algo.vectorizer import embed_text

# 调用向量数据库API（依据 PPT 示例进行配置）
# 注意修改 API base 和相关参数为实际值
API_BASE = "http://10.176.64.152:11435/v1"
MODEL_FOR_EMBED = "bge-m3"  # 向量化模型，与前面的保持一致

# 使用 chromadb 的 embedding function 示例（如果需要）
embedding_function = embedding_functions.OpenAIEmbeddingFunction(
    api_key="API_KEY_IS_NOT_NEEDED",
    api_base=API_BASE,
    model_name=MODEL_FOR_EMBED
)

# 连接本地向量数据库（确保先启动向量数据库，例如 chromadb 启动在8002端口）
client = chromadb.HttpClient(host='localhost', port=8002)

# 如果不存在，则新建 collection，否则获取集合
def get_or_create_collection():
    try:
        collection = client.get_collection(name="paper_collection", embedding_function=embedding_function)
    except Exception:
        collection = client.create_collection(name="paper_collection", embedding_function=embedding_function)
    return collection

# 向量检索函数，根据 query_text 返回最相近的论文ID和相似度
def search_similar_papers(query_text: str, n_results: int = 3):
    # 计算 query_text 的向量
    query_vector = embed_text(query_text)
    # 获取向量数据库 collection
    collection = get_or_create_collection()
    # 执行查询
    result = collection.query(query_texts=[query_text], n_results=n_results)
    return result

if __name__ == "__main__":
    # 测试检索功能
    query = "人工智能在论文写作中的应用"
    res = search_similar_papers(query, n_results=2)
    print("检索结果：", res)