import os
import json
import sys
import tiktoken

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
import backend.crud as crud
import backend.models as models

def truncate_to_token_limit(text, max_tokens=8192, model_name="text-embedding-ada-002"):
    enc = tiktoken.encoding_for_model(model_name)
    tokens = enc.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return enc.decode(tokens)

def extract_pdf_text(pdf_path):
    # 你已有的PDF文本提取函数
    from backend.pdf_parser import extract_pdf_text
    return extract_pdf_text(pdf_path)

def main():
    # 读取papers.json
    with open('papers/papers.json', 'r', encoding='utf-8') as f:
        papers = json.load(f)

    db = SessionLocal()
    for paper in papers:
        pdf_path = paper['path']
        abs_path = os.path.join(os.path.dirname(__file__), '..', pdf_path)
        if not os.path.exists(abs_path):
            print(f"文件不存在: {abs_path}")
            continue

        # 检查数据库是否已存在
        db_paper = db.query(models.Paper).filter(models.Paper.file_path == pdf_path).first()
        if db_paper:
            print(f"已存在: {pdf_path}")
            continue

        # 提取文本
        content = extract_pdf_text(abs_path)
        title = os.path.splitext(os.path.basename(pdf_path))[0]
        author = "未知"
        abstract = content[:500] if content else ""

        # 插入数据库
        db_paper = crud.create_paper(
            db,
            title=title,
            author=author,
            abstract=abstract,
            content=content,
            file_path=pdf_path
        )
        print(f"已导入: {pdf_path}")

        # 向量化
        try:
            from backend_algo.retrieval import get_or_create_collection
            collection = get_or_create_collection()
            # 限制最大长度，防止超出embedding模型限制
            max_tokens = 8192  # 或模型实际限制？
            truncated_content = truncate_to_token_limit(content, max_tokens=max_tokens)
            paper_text = f"标题: {title}\n摘要: {abstract}\n内容: {truncated_content}"
            collection.add(
                ids=[str(db_paper.id)],
                documents=[paper_text],
                metadatas=[{
                    "title": title,
                    "author": author,
                    "paper_id": db_paper.id
                }]
            )
            print(f"已向量化: {pdf_path}")
        except Exception as e:
            import traceback
            print(f"向量化失败: {pdf_path}")
            print(traceback.format_exc())

    db.close()

if __name__ == "__main__":
    main()