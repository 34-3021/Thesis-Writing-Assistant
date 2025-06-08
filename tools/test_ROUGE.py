import jieba
from rouge_score import rouge_scorer
from rouge_chinese import Rouge

def clean_text(text):
    # 不去掉[x]，只分词
    # text = re.sub(r'\[\d+\]', '', text)
    text = ' '.join(jieba.cut(text))
    return text.strip()

scorer = rouge_scorer.RougeScorer(['rougeL', 'rouge1', 'rouge2'], use_stemmer=False)

# 测试1：完全相同
a = "环境监测在生态环境保护中发挥着重要作用。"
b = "环境监测在生态环境保护中发挥着重要作用。"
print(scorer.score(clean_text(a), clean_text(b)))

# 测试2：有部分重合
a = "环境监测在生态环境保护中发挥着重要作用。"
b = "环境监测对于生态环境保护非常重要。"
print(scorer.score(clean_text(a), clean_text(b)))

# 测试3：完全不同
a = "环境监测在生态环境保护中发挥着重要作用。"
b = "今天是星期五。"
print(scorer.score(clean_text(a), clean_text(b)))

# 测试4：英文完全相同
a = "I am a young boy named Gyf."
b = "I am a young boy named Gyf."
print(scorer.score(clean_text(a), clean_text(b)))

# 测试5：英文有部分重合
a = "I am an unhappy young boy named Gyf."
b = "I am a young boy named Gyf."
print(scorer.score(clean_text(a), clean_text(b)))

# 测试6：英文完全不同
a = "He is an interesting teacher who is very tall."
b = "I am a young boy named Gyf."
print(scorer.score(clean_text(a), clean_text(b)))

print("接下来使用Rouge库进行中文测试：")
# 测试7：中文使用Rouge库，分词，结果为合理值，0到1之间
rouge = Rouge()
a = "环境监测 在 生态环境保护 中发挥着 重要作用。"
b = "环境监测 对于 生态环境保护 非常重要。"
print(rouge.get_scores(a, b))

# 测试8：中文使用Rouge库，不分词，结果为0
rouge = Rouge()
a = "环境监测在生态环境保护中发挥着重要作用。"
b = "环境监测对于生态环境保护非常重要。"
print(rouge.get_scores(a, b))

# 测试9：中文使用Rouge库，完全相同
rouge = Rouge()
a = "环境监测在生态环境保护中发挥着重要作用。"
b = "环境监测在生态环境保护中发挥着重要作用。"
print(rouge.get_scores(a, b))