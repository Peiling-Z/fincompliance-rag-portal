from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from app.rag.ingest import ingest_pdf_to_store
from app.rag.retriever import ask_question

load_dotenv()

app = FastAPI(title="FinCompliance RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

class AskRequest(BaseModel):
    question: str

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    saved = ingest_pdf_to_store(file.filename, content)
    return {"status": "ok", "saved": saved}

@app.post("/ask")
async def ask(req: AskRequest):
    answer = ask_question(req.question)
    return answer
