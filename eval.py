import json

# Load model outputs và ground truth
with open("generated_code.json", "r") as f:
    model_outputs = json.load(f)

with open("valid_preprocessed.json", "r") as f:
    ground_truth = json.load(f)

# Tạo dict lookup từ ground truth theo question
gt_dict = {item["question"]: item for item in ground_truth}

total = len(model_outputs)
complete_count = 0
success_count = 0

for out in model_outputs:
    query = out.get("query", "").strip()
    question = out.get("question")  # dùng question để match GT
    if query:  # Complete nếu có query
        complete_count += 1
    
    gt = gt_dict.get(question)
    if gt and query == gt["query"].strip():  # Success nếu query giống hẳn GT
        success_count += 1

CR = complete_count / total * 100
SR = success_count / total * 100

print(f"Complete Rate (CR): {CR:.2f}%")
print(f"Success Rate (SR): {SR:.2f}%")
