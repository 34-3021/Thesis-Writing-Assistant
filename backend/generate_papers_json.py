import csv
import json
import os

mapping_path = os.path.join(os.path.dirname(__file__), '../papers/mapping.csv')
papers_dir = os.path.join(os.path.dirname(__file__), '../papers')
output_json = os.path.join(papers_dir, 'papers.json')

papers = []
with open(mapping_path, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        file_name = row['编号文件']
        base = os.path.splitext(row['原始文件名'])[0]
        if '_' in base:
            title, author = base.rsplit('_', 1)
        else:
            title, author = base, "未知"
        papers.append({
            "path": f"papers/{file_name}",
            "title": title.strip(),
            "author": author.strip()
        })

with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(papers, f, ensure_ascii=False, indent=2)

print(f"已生成 {output_json}，共{len(papers)}条。")