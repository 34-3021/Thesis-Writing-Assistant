import os
import csv

PAPERS_DIR = os.path.join(os.path.dirname(__file__), '..', 'papers')
OUTPUT_CSV = os.path.join(PAPERS_DIR, 'mapping.csv')

def main():
    pdf_files = sorted([
        f for f in os.listdir(PAPERS_DIR)
        if f.lower().endswith('.pdf') and f.startswith('paper_')
    ])
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # 写表头
        writer.writerow(['编号文件', '主题', '子主题', '原始文件名'])
        for pdf in pdf_files:
            # 这里只能自动填编号和文件名，主题和子主题需后续人工补充
            writer.writerow([pdf, '', '', ''])
    print(f"已生成 {OUTPUT_CSV}，共{len(pdf_files)}条。")

if __name__ == '__main__':
    main()