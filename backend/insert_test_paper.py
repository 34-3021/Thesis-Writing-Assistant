# 脚本，测试用
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import pdf_parser
import models

def insert_test_paper():
    # 设置测试论文文件的路径
    file_path = "backend/test_papers/test1.pdf"
    # 使用 pdf_parser 提取论文文本
    content = pdf_parser.extract_pdf_text(file_path)
    
    # 此处可手动设置标题、作者、摘要（也可通过解析获取）
    title = "测试论文标题"
    author = "测试作者"
    abstract = content[:500]  # 示例：取前500个字符作为摘要

    # 使用数据库会话写入数据
    db: Session = SessionLocal()
    try:
        paper = crud.create_paper(db, title=title, author=author, abstract=abstract,
                                  content=content, file_path=file_path)
        print("成功插入论文，ID：", paper.id)
    except Exception as e:
        print("插入失败：", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    insert_test_paper()