# 模块：用来将文本转换为向量的（调用API）
import requests
import numpy as np

# 注意将URL和MODEL修改成实际的值
EMBEDDING_API_URL = "http://10.176.64.152:11435/v1/embeddings"
MODEL = "bge-m3"

def embed_text(text: str) -> np.array:
    """
    将输入文本转换为向量，返回一个numpy数组
    """
    # 为避免请求过大，可以考虑分段处理或取摘要，这里示例直接处理全文
    response = requests.post(EMBEDDING_API_URL, json={
        "model": MODEL,
        "input": [text],
    }).json()
    # 从response中取出第一条（唯一）的embedding
    if "data" not in response:
        print("Embedding API error:", response)
        raise RuntimeError(f"Embedding API error: {response}")
    embedding = response["data"][0]["embedding"]
    return np.array(embedding)