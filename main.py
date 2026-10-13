"""Command-line interface for the MIMIC-III medical assistant."""

from utils.config import load_project_env

load_project_env()

import json
import os
import argparse

from medical_assistant import json_safe
from langchain_classic.memory import ConversationBufferMemory

from llm.llm_client import LLMClient
from medical_assistant import MedicalDatabaseAssistant
from rag.clinical_semantics import FeasibleValueLookup
from rag.fewshot_retriever import FewshotRetriever
from rag.retrieve import MIMICColumnRetriever


OPENAI_MODEL = "gpt-4o-mini"
FEWSHOT_PATH = "./memory/memory.json"
MAX_FEWSHOT = 3
MAX_RETRY = 3


def create_assistant() -> MedicalDatabaseAssistant:
    retriever = MIMICColumnRetriever(
        faiss_index_path="graph/faiss_index.bin",
        meta_path="graph/faiss_meta.json",
    )
    return MedicalDatabaseAssistant(
        llm=LLMClient(model=OPENAI_MODEL, temperature=0),
        retriever=retriever,
        fewshot_retriever=FewshotRetriever(FEWSHOT_PATH),
        value_lookup=FeasibleValueLookup(retriever.model),
        max_fewshot=MAX_FEWSHOT,
        max_retry=MAX_RETRY,
        max_semantic_retry=int(os.getenv('MIMIC_SEMANTIC_RETRIES', '2')),
    )


def create_ehrsql_assistant():
    from ehrsql.assistant import EHRSQLAssistant
    return EHRSQLAssistant(
        llm=LLMClient(model=OPENAI_MODEL, temperature=0),
        max_retry=MAX_RETRY,
        max_fewshot=4,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-ehrsql", "--ehrsql", action="store_true",
                        help="use the local cleaned EHRSQL MIMIC-III database")
    parser.add_argument("--evaluate", action="store_true",
                        help="evaluate the selected EHRSQL mode on valid.json")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--output-prefix", default="evaluation/ehrsql_valid")
    args = parser.parse_args()
    if args.evaluate and not args.ehrsql:
        parser.error("--evaluate currently requires -ehrsql")
    if args.ehrsql and args.evaluate:
        from evaluation.run_ehrsql_batch import run_batch
        run_batch(args.output_prefix, args.workers)
        return

    assistant = create_ehrsql_assistant() if args.ehrsql else create_assistant()
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history",
        output_key="answer",
    )

    print("🩺 EHRSQL cleaned MIMIC-III Assistant" if args.ehrsql
          else "🩺 MIMIC-III Medical Assistant")
    print("Type 'exit' to quit\n")

    while True:
        question = input("User > ").strip()
        if question.lower() in {"exit", "quit"}:
            break

        if args.ehrsql:
            sql, result = assistant.query(question)
            answer = ("Unanswerable from the EHRSQL schema." if result.get("abstained")
                      else json.dumps(json_safe(result.get("rows", [])), ensure_ascii=False, default=str)
                      if result.get("success") else f"Query failed: {result.get('error')}")
        else:
            answer, sql, result = assistant.answer(
                question, memory.chat_memory.messages
            )
        if os.getenv("MIMIC_DEBUG", "0").lower() in {"1", "true"}:
            print("SQL:", sql)
            print("Query result:", json.dumps(json_safe(result), ensure_ascii=False, default=str))

        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message(answer)

        print("\nAssistant >", answer)
        print("-" * 60)


if __name__ == "__main__":
    main()
