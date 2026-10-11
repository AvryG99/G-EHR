"""Command-line interface for the MIMIC-IV medical assistant."""

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
    )


def main():
    assistant = create_assistant()
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history",
        output_key="answer",
    )

    print("🩺 MIMIC-IV Medical Assistant")
    print("Type 'exit' to quit\n")

    while True:
        question = input("User > ").strip()
        if question.lower() in {"exit", "quit"}:
            break

        answer, _, _ = assistant.answer(
            question, memory.chat_memory.messages
        )
        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message(answer)

        print("\nAssistant >", answer)
        print("-" * 60)


if __name__ == "__main__":
    main()
