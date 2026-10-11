import torch
from transformers import AutoTokenizer, AutoModel
import sys

log_file = open("bge_embedding_pipeline.txt", "w", encoding="utf-8")
sys.stdout = log_file

MODEL_NAME = "BAAI/bge-base-en-v1.5"

# =========================================================
# PHASE 0 — Load model & tokenizer
# =========================================================
print("\n📦 PHASE 0 — LOAD MODEL")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()

# =========================================================
# INPUT
# =========================================================
text = "What are the lab_items used for people who has admissions 142345?"

print("\n" + "=" * 70)
print("📝 INPUT TEXT")
print(f"→ \"{text}\"")

# =========================================================
# PHASE 1 — Tokenization (text → tokens)
# =========================================================
print("\n" + "=" * 70)
print("🔹 PHASE 1 — TOKENIZATION")
print("Ý nghĩa: chia câu thành các đơn vị mà Transformer hiểu được")

encoded = tokenizer(
    text,
    return_tensors="pt",
    truncation=True
)

input_ids = encoded["input_ids"]
attention_mask = encoded["attention_mask"]
tokens = tokenizer.convert_ids_to_tokens(input_ids[0])
token_ids = input_ids[0].tolist()

print("\nTokens (token → token_id):")
for i, (tok, tid) in enumerate(zip(tokens, token_ids)):
    print(f"  {i:02d}: {tok:15s} → id={tid}")


print("\nAttention mask:")
print(" ", attention_mask.tolist())
print("  (1 = token thật, 0 = padding)")

# =========================================================
# PHASE 2 — Transformer Encoding (tokens → token embeddings)
# =========================================================
print("\n" + "=" * 70)
print("🧠 PHASE 2 — TRANSFORMER ENCODING")
print("Ý nghĩa: mỗi token học ngữ cảnh từ toàn câu")

with torch.no_grad():
    outputs = model(**encoded)

last_hidden_state = outputs.last_hidden_state
# shape: (1, seq_len, 768)

print("\nOutput shape:", tuple(last_hidden_state.shape))
print("→ Mỗi token → vector 768 chiều")

print("\nToken-level embeddings (5 chiều đầu):")
for i, tok in enumerate(tokens):
    vec = last_hidden_state[0, i]
    print(f"  {tok:10s} → {vec[:5].numpy()} ...")

# ======================= PHASE 2.5 ========================
# Xây pooling mask (theo đúng BGE)
# =========================================================
print("\n" + "=" * 70)
print("🧹 BUILD POOLING MASK (BGE style)")
print("Ý nghĩa: chỉ giữ token nội dung, bỏ CLS / SEP / PAD")

special_tokens = set(tokenizer.all_special_tokens)

pooling_mask = []
content_tokens = []

for tok in tokens:
    if tok in special_tokens:
        pooling_mask.append(0)
    else:
        pooling_mask.append(1)
        content_tokens.append(tok)

pooling_mask = torch.tensor(pooling_mask).unsqueeze(-1)

print("\nTokens dùng để pooling:")
print(" ", content_tokens)

print("Pooling mask:")
print(" ", pooling_mask.squeeze().tolist())
print("  (1 = dùng, 0 = bỏ)")

# =========================================================
# PHASE 3 — Mean Pooling (token embeddings → sentence embedding)
# =========================================================
print("\n" + "=" * 70)
print("📐 PHASE 3 — MEAN POOLING")
print("Ý nghĩa: gom toàn bộ token ngữ nghĩa thành 1 vector câu")

masked_embeddings = last_hidden_state[0] * pooling_mask
sum_embeddings = masked_embeddings.sum(dim=0)
num_tokens = pooling_mask.sum()

sentence_embedding_raw = sum_embeddings / num_tokens

print("\nSentence embedding (RAW)")
print("Shape:", tuple(sentence_embedding_raw.shape))
print("First 10 dims:", sentence_embedding_raw[:10].numpy())

# =========================================================
# PHASE 4 — L2 Normalization (geometry normalization)
# =========================================================
print("\n" + "=" * 70)
print("⚖️ PHASE 4 — L2 NORMALIZATION")
print("Ý nghĩa: ép vector lên hypersphere (norm = 1)")
print("→ cosine similarity = dot product")

sentence_embedding_final = torch.nn.functional.normalize(
    sentence_embedding_raw, p=2, dim=0
)

print("\nFinal embedding")
print("Norm:", torch.norm(sentence_embedding_final).item())
print("First 10 dims:", sentence_embedding_final[:10].numpy())

print("\n✅ DONE — BGE embedding pipeline hoàn chỉnh")
log_file.close()
sys.stdout = sys.__stdout__
print("✅ Log đã được lưu vào bge_embedding_pipeline.txt")
