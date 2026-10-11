# Research & Technical Specification: MIMIC-IV Text-to-SQL Agent with Dual-Runtime Sandbox and Knowledge Graph

## 1. Overview & System Objectives
This research blueprint outlines the architecture for an advanced **Text-to-SQL Agent** specialized for the **MIMIC-IV** (Medical Information Mart for Intensive Care IV) database. 
The system bridges natural language (NL) queries with complex clinical databases by addressing three major challenges:
1. **Schema & Join Complexity:** Overcoming multi-table relational navigation via a **Clinical Knowledge Graph**.
2. **Medical Terminology Discrepancies:** Mapping colloquial terms (e.g., "heart attack") to precise database values via a **Lookup Tool & Embedding Retrieval**.
3. **Cross-Dialect Execution & Cost Safety:** Ensuring error-free, zero-cost development via a **Dual-Runtime Sandbox (DuckDB + SQLGlot Transpilation)** prior to production execution on **Google BigQuery**.

---

## 2. Core Architectural Components

```
[ User Natural Language Query ]
             │
             ▼
┌──────────────────────────┐
│ Clinical Entity Normalizer│ ──(Resolves synonyms: "heart attack" -> "myocardial infarction")
└──────────────────────────┘
             │
             ▼
┌──────────────────────────┐
│ Knowledge Graph Retriever│ ──(Provides exact join paths: patients -> admissions -> icustays)
└──────────────────────────┘
             │
             ▼
┌──────────────────────────┐
│ Lookup Tool (Vector Search)│ ──(Retrieves feasible high-cardinality values/codes)
└──────────────────────────┘
             │
             ▼
┌──────────────────────────┐
│ LLM Core + Soft-Prompt   │ ──(Generates GoogleSQL Query)
└──────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────┐
│ DUAL-RUNTIME SANDBOX                                   │
│ 1. SQLGlot Transpiler: BigQuery SQL ──> DuckDB Dialect │
│ 2. Local Execution: Run against local mock DB          │
│ 3. Self-Healing Loop: Catch errors & re-prompt LLM     │
└────────────────────────────────────────────────────────┘
             │ (If tests pass)
             ▼
[ Production Execution on Google BigQuery (Zero-Cost Safe) ]
```

---

## 3. Module Specifications

### Module A: Clinical Semantic Alignment & Lookup Tool
* **Purpose:** Handle high-cardinality columns (e.g., `d_icd_diagnoses.long_title`, `d_labitems.label`) and bridge colloquial phrasing with clinical entries.
* **Mechanism:**
  * Uses a Sentence-Transformer embedding model (e.g., `bge-large-en-v1.5` or `Bio_ClinicalBERT`) stored in a local vector database (FAISS).
  * Executes a `get_feasible_column_values` tool returning frequency-sorted matches.

### Module B: Clinical Schema Knowledge Graph (KG)
* **Purpose:** Prevent incorrect table joins (`subject_id` vs `hadm_id` vs `stay_id`).
* **Mechanism:** 
  * Directed graph where nodes are tables/columns and edges represent valid Foreign Keys and clinical join patterns (e.g., enforcing passage through `icustays` when dealing with chart events).

### Module C: Dual-Runtime Sandbox & Transpilation Layer
* **Purpose:** Test queries locally using DuckDB without incurring BigQuery costs, while maintaining GoogleSQL as the primary dialect.
* **Mechanism:**
  * **Transpilation:** Utilizes Python's `sqlglot` library to seamlessly convert BigQuery dialect into DuckDB-compatible syntax for local debugging.
  * **Self-Correction Loop:** If local execution fails, the error stack trace is fed back into the LLM prompt to fix the query autonomously.

### Module D: Soft-Prompt Integration
* **Purpose:** Imprint deep MIMIC-IV relational instincts and syntax behavior directly onto open-source LLM weights (e.g., Llama/DeepSeek) as continuous trainable prefix vectors, reducing context length overhead.

---

## 4. Implementation Guidelines for Coding Agents

When implementing code based on this blueprint, adhere strictly to the following instructions:

1. **Strict Dialect Separation:** Always instruct the LLM to output queries in **Google BigQuery Standard SQL** format. Never write raw DuckDB queries as primary targets; let `sqlglot` handle the translation layer.
2. **Mandatory Table Filtering:** For high-volume tables (`chartevents`, `labevents`), the agent must *always* verify or constrain queries using appropriate IDs and lookup values to prevent full table scans.
3. **Error Feedback Loop:** Implement a maximum retry limit of $N=3$ for the self-healing sandbox loop to prevent infinite token consumption.
4. **Environment Toggle:** Provide a configuration switch (`MIMIC_ENV=local` vs `MIMIC_ENV=cloud`) to switch between the DuckDB local sandbox and the Google BigQuery client seamlessly.