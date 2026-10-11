"""FastAPI interface for the MIMIC-IV medical assistant."""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_classic.memory import ConversationBufferMemory
from pydantic import BaseModel

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


app = FastAPI(title="MIMIC-IV Medical Database Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

assistant = create_assistant()
sessions: dict[str, ConversationBufferMemory] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    message: str
    timestamp: str


def get_or_create_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in sessions:
        sessions[session_id] = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history",
            output_key="answer",
        )
    return sessions[session_id]


@app.get("/")
async def root():
    return {"message": "MIMIC-IV Medical Database Assistant API"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        memory = get_or_create_memory(request.session_id)
        answer, _, _ = assistant.answer(
            request.message, memory.chat_memory.messages
        )

        memory.chat_memory.add_user_message(request.message)
        memory.chat_memory.add_ai_message(answer)

        return ChatResponse(
            message=answer,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/clear/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        sessions[session_id].clear()
        return {"message": f"Session {session_id} cleared"}
    return {"message": f"Session {session_id} not found"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
