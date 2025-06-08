import json
import os

questions_path = "papers/questions.json"
workspace_dir = "workspace"
batch_files = [f for f in os.listdir(workspace_dir) if f.startswith("batch_results_") and f.endswith(".json")]
batch_files.sort()  # 最新的在最后

# 读取 questions.json
with open(questions_path, encoding="utf-8") as f:
    questions = json.load(f)

# 建立Q内容到索引的映射（用tuple序列化Q字段）
q_map = {json.dumps(q["Q"], ensure_ascii=False): idx for idx, q in enumerate(questions)}

# 遍历所有batch_results文件
for batch_file in batch_files:
    with open(os.path.join(workspace_dir, batch_file), encoding="utf-8") as f:
        batch_results = json.load(f)
    for batch in batch_results:
        q_key = json.dumps(batch["Q"], ensure_ascii=False)
        if q_key in q_map:
            idx = q_map[q_key]
            questions[idx]["A"] = batch["AI"]

# 保存
with open(questions_path, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print(f"已将 workspace 下所有 batch_results 的AI内容正确批量写入 {questions_path} 的A字段！")