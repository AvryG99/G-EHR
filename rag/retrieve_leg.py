import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.graph_builder import build_schema_graph
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
import networkx as nx
from itertools import combinations
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# ---------- NLTK setup ----------
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('omw-1.4', quiet=True)

# ---------- TEXT PREPROCESSING ----------
def preprocess_text(text):
    """Lemmatize + remove stopwords + lowercase"""
    lemmatizer = WordNetLemmatizer()
    words = nltk.word_tokenize(text.lower())
    words = [lemmatizer.lemmatize(w) for w in words if w.isalnum() and w not in stopwords.words('english')]
    return " ".join(words)

# ---------- LOAD GRAPH ----------
G = build_schema_graph()

# ---------- BUILD CORPORA ----------
table_texts, table_names = [], []
for node, data in G.nodes(data=True):
    desc = data['metadata'].get("description", "")
    text = f"Table: {node}. Primary Key: {data['metadata']['primary_key']}. Description: {desc}"
    table_texts.append(text)
    table_names.append(node)

column_texts, column_table_map = [], []
for node, data in G.nodes(data=True):
    attrs = data['attributes']
    attr_text = " ".join([f"{k} ({v['datatype']}): {v['description']}" for k, v in attrs.items()])
    column_texts.append(attr_text)
    column_table_map.append(node)

# ---------- CLEAN TEXT ----------
table_texts_clean = [preprocess_text(t) for t in table_texts]
column_texts_clean = [preprocess_text(t) for t in column_texts]

# ---------- EMBEDDINGS (SentenceTransformer + TF-IDF) ----------

# SentenceTransformer
model_table = SentenceTransformer('all-MiniLM-L6-v2')
sent_emb_table = model_table.encode(table_texts_clean, convert_to_numpy=True)

model_column = SentenceTransformer('all-MiniLM-L6-v2')
sent_emb_col = model_column.encode(column_texts_clean, convert_to_numpy=True)

# TF-IDF
tfidf_table = TfidfVectorizer(max_features=512)
tfidf_emb_table = tfidf_table.fit_transform(table_texts_clean).toarray()

tfidf_col = TfidfVectorizer(max_features=512)
tfidf_emb_col = tfidf_col.fit_transform(column_texts_clean).toarray()

# Normalize
sent_emb_table = normalize(sent_emb_table)
tfidf_emb_table = normalize(tfidf_emb_table)
sent_emb_col = normalize(sent_emb_col)
tfidf_emb_col = normalize(tfidf_emb_col)

# Weighted concat (70% semantic + 30% lexical)
alpha = 0.7
table_emb = np.concatenate([alpha * sent_emb_table, (1 - alpha) * tfidf_emb_table], axis=1)
column_emb = np.concatenate([alpha * sent_emb_col, (1 - alpha) * tfidf_emb_col], axis=1)

# ---------- FUNCTIONS ----------

def retrieve_main_tables(query, top_k=5, threshold=0.4):
    """Retrieve most relevant tables using hybrid embedding"""
    query_clean = preprocess_text(query)
    
    q_sent = model_table.encode([query_clean], convert_to_numpy=True)
    q_tfidf = tfidf_table.transform([query_clean]).toarray()
    
    q_emb = np.concatenate([alpha * normalize(q_sent), (1 - alpha) * normalize(q_tfidf)], axis=1)
    scores = cosine_similarity(q_emb, table_emb).flatten()
    
    sorted_idx = scores.argsort()[::-1][:top_k]
    selected = [table_names[i] for i in sorted_idx if scores[i] >= threshold]
    return selected

def add_intermediate_tables(main_tables):
    """Add intermediate tables by graph traversal"""
    all_tables = set(main_tables)
    for t1, t2 in combinations(main_tables, 2):
        try:
            path = nx.shortest_path(G.to_undirected(), source=t1, target=t2)
            all_tables.update(path)
        except nx.NetworkXNoPath:
            continue
    return list(all_tables)

def retrieve_columns(query, tables):
    """Retrieve relevant columns for given tables"""
    query_clean = preprocess_text(query)
    
    q_sent = model_column.encode([query_clean], convert_to_numpy=True)
    q_tfidf = tfidf_col.transform([query_clean]).toarray()
    
    q_emb = np.concatenate([alpha * normalize(q_sent), (1 - alpha) * normalize(q_tfidf)], axis=1)
    scores = cosine_similarity(q_emb, column_emb).flatten()
    
    relevant_columns = {}
    for idx, score in enumerate(scores):
        table = column_table_map[idx]
        if table in tables and score > 0.5:
            relevant_columns[table] = column_texts[idx]
    return relevant_columns

def rag_retrieve(query, top_k=5, table_threshold=0.35):
    """Full retrieval pipeline"""
    main_tables = retrieve_main_tables(query, top_k=top_k, threshold=table_threshold)
    full_tables = add_intermediate_tables(main_tables)
    columns = retrieve_columns(query, full_tables)
    return {
        "tables": full_tables,
        "columns": columns
    }

# ---------- TEST ----------
if __name__ == "__main__":
    query = "what are the lab items needed for patients 10006?"
    result = rag_retrieve(query, top_k=5)
    print("Tables needed for query (including intermediate):")
    print(result)
