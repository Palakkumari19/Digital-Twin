


"""
API routes module for MULRAG - Hackathon MVP Version.

Authentication removed.
Single demo user mode enabled.
"""

import time
import os
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ..config import settings
from ..models import (
    CreateSession, QueryRequest,
    SessionResponse, ChatHistoryResponse, UploadResponse
)
from ..database import (
    session_repo, message_repo, log_repo,
    convert_session_to_response, convert_message_to_response
)
from ..agents import MultiAgentRAGSystem
#from ..document_processing import document_processor


# ==================== DEMO USER ====================

DEMO_USER_ID = "hackathon_user"
DEMO_USERNAME = "demo_user"


# ==================== ROUTERS ====================

session_router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
upload_router = APIRouter(prefix="/api/v1", tags=["uploads"])
chat_router = APIRouter(prefix="/api/v1", tags=["chat"])
legacy_router = APIRouter(prefix="/api/v1", tags=["legacy"])


# ==================== SESSION ROUTES ====================

@session_router.post("/create", response_model=Dict[str, Any])
async def create_session(session_data: CreateSession):
    try:
        from ..models import SessionDocument

        session_doc = SessionDocument(
            user_id=DEMO_USER_ID,
            title=session_data.title,
            document_id=session_data.document_id,
            document_url=session_data.document_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            message_count=0
        )

        session_id = await session_repo.create_session(session_doc)

        session_response = convert_session_to_response({
            "_id": session_id,
            **session_doc.dict()
        })

        return {
            "success": True,
            "session_id": session_id,
            "session": session_response.dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.get("/list")
async def list_sessions():
    sessions = await session_repo.get_user_sessions(DEMO_USER_ID)

    session_list = [
        convert_session_to_response(s).dict()
        for s in sessions
    ]

    return {
        "success": True,
        "sessions": session_list
    }


@session_router.get("/{session_id}/messages", response_model=ChatHistoryResponse)
async def get_session_messages(session_id: str):
    session = await session_repo.get_user_session(session_id, DEMO_USER_ID)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await message_repo.get_session_messages(session_id)

    message_list = [
        convert_message_to_response(m).dict()
        for m in messages
    ]

    session_response = convert_session_to_response(session)

    return ChatHistoryResponse(
        session=session_response,
        messages=message_list
    )


@session_router.delete("/{session_id}")
async def delete_session(session_id: str):
    deleted = await session_repo.delete_session(session_id, DEMO_USER_ID)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    await message_repo.delete_session_messages(session_id)

    return {"success": True}


# ==================== UPLOAD ====================

@upload_router.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    content = await file.read()

    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File must be < {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )

    file_id = f"upload_{int(time.time())}_{DEMO_USERNAME}_{file.filename}"

    upload_path = os.path.join(settings.UPLOAD_DIR, file_id)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    with open(upload_path, "wb") as f:
        f.write(content)

    return UploadResponse(
        success=True,
        file_id=file_id,
        filename=file.filename,
        message="PDF uploaded successfully"
    )


# ==================== CHAT ====================

@chat_router.post("/chat")
async def chat_endpoint(
    question: str = Form(...),
    session_id: str = Form(...)
):

    session = await session_repo.get_user_session(session_id, DEMO_USER_ID)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from ..models import MessageDocument

    # Save user message
    user_message = MessageDocument(
        session_id=session_id,
        type="user",
        content=question,
        created_at=datetime.utcnow()
    )
    await message_repo.create_message(user_message)

    # Determine document source
    if session.get("document_id"):
        doc_source = os.path.join(settings.UPLOAD_DIR, session["document_id"])
        is_local_file = True
    elif session.get("document_url"):
        doc_source = session["document_url"]
        is_local_file = False
    else:
        raise HTTPException(status_code=400, detail="No document attached")

    from openai import AsyncAzureOpenAI

    client = AsyncAzureOpenAI(
        api_version=settings.OPENAI_API_VERSION,
        azure_endpoint=settings.OPENAI_API_BASE,
        api_key=settings.OPENAI_API_KEY
    )

    #rag_system = MultiAgentRAGSystem(client, document_processor)
    from ..document_processing import DocumentProcessor

    doc_processor = DocumentProcessor(client)

    rag_system = MultiAgentRAGSystem(client, doc_processor)

    result = await rag_system.process_question(
        question,
        session_id,
        doc_source,
        is_local_file
    )

    # Save bot message
    bot_message = MessageDocument(
        session_id=session_id,
        type="bot",
        content=result["answer"],
        processing_time=result["processing_time"],
        created_at=datetime.utcnow(),
        metadata=result["metadata"]
    )

    await message_repo.create_message(bot_message)

    await session_repo.increment_message_count(session_id, 2)
    await session_repo.update_session(session_id, updated_at=datetime.utcnow())

    return JSONResponse(result)


# ==================== LEGACY ====================

@legacy_router.post("/hackrx/run")
async def hackrx_run(request: QueryRequest, authorization: str = Header(None)):

    log_entry = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "auth_header": authorization,
        "request_data": request.dict()
    }

    await log_repo.create_log_from_request(**log_entry)

    doc_url = request.documents

    chunks, faiss_index = await document_processor.get_or_process_document(
        doc_url,
        is_local_file=False
    )

    tasks = [answer_question_simple(q, chunks, faiss_index)
             for q in request.questions]

    answers = await asyncio.gather(*tasks)

    return {"answers": answers}


async def answer_question_simple(question: str, chunks: list, faiss_index):

    from ..document_processing import (
        get_embeddings, search_faiss, rerank_chunks_by_keyword_overlap
    )

    from openai import AsyncAzureOpenAI
    import numpy as np

    client = AsyncAzureOpenAI(
        api_version=settings.OPENAI_API_VERSION,
        azure_endpoint=settings.OPENAI_API_BASE,
        api_key=settings.OPENAI_API_KEY
    )

    question_embeddings = await get_embeddings([question], client)
    avg_embedding = np.mean(question_embeddings, axis=0, keepdims=True)

    retrieved_chunks = search_faiss(avg_embedding, faiss_index, chunks, k=None)
    top_chunks = rerank_chunks_by_keyword_overlap(question, retrieved_chunks, top_k=None)

    context = "\n---\n".join(top_chunks)

    prompt = f"""
Answer this question based on the document context.

Context:
{context}

Question: {question}
Answer:
"""

    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=300,
        model=settings.OPENAI_DEPLOYMENT
    )

    return response.choices[0].message.content.strip()


# ==================== HEALTH ====================

@chat_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "hackathon_single_user",
        "user": DEMO_USERNAME
    }


# ==================== INCLUDE ROUTERS ====================

def include_routers(app):
    app.include_router(session_router)
    app.include_router(upload_router)
    app.include_router(chat_router)
    app.include_router(legacy_router)

    print("[API] Hackathon routers loaded successfully")