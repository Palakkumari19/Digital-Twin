

# """
# API routes module for MULRAG - Hackathon MVP Version.

# Authentication removed.
# Single demo user mode enabled.
# """

# import time
# import os
# import asyncio
# from datetime import datetime
# from typing import Dict, Any

# from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException
# from fastapi.responses import JSONResponse

# from ..config import settings
# from ..models import (
#     CreateSession, QueryRequest,
#     SessionResponse, ChatHistoryResponse, UploadResponse
# )
# from ..database import (
#     session_repo, message_repo, log_repo,
#     convert_session_to_response, convert_message_to_response
# )
# from ..agents import MultiAgentRAGSystem


# # ==================== DEMO USER ====================

# DEMO_USER_ID = "hackathon_user"
# DEMO_USERNAME = "demo_user"


# # ==================== ROUTERS ====================

# session_router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
# upload_router = APIRouter(prefix="/api/v1", tags=["uploads"])
# chat_router = APIRouter(prefix="/api/v1", tags=["chat"])
# legacy_router = APIRouter(prefix="/api/v1", tags=["legacy"])


# # ==================== FLASHCARDS ROUTE ====================
# @session_router.get("/{session_id}/flashcards")
# async def get_flashcards(session_id: str):
#     """
#     Generate deterministic flashcards from stored document chunks.
#     Returns 5 random flashcards per request.
#     """

#     session = await session_repo.get_user_session(session_id, DEMO_USER_ID)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found")

#     if not session.get("document_id"):
#         raise HTTPException(status_code=400, detail="No document attached")

#     doc_source = os.path.join(settings.UPLOAD_DIR, session["document_id"])

#     from .. import document_processing
#     from ..flashcards import generate_flashcards

#     doc_processor = document_processing.document_processor

#     if doc_processor is None:
#         raise HTTPException(status_code=500, detail="Document processor not initialized")

#     chunks, _ = await doc_processor.get_or_process_document(
#         doc_source,
#         is_local_file=True
#     )

#     flashcards = generate_flashcards(chunks, limit=5)

#     return {
#         "success": True,
#         "total": len(flashcards),
#         "flashcards": flashcards
#     }
# # ==================== SESSION ROUTES ====================

# @session_router.post("/create", response_model=Dict[str, Any])
# async def create_session(session_data: CreateSession):
#     try:
#         from ..models import SessionDocument

#         session_doc = SessionDocument(
#             user_id=DEMO_USER_ID,
#             title=session_data.title,
#             document_id=session_data.document_id,
#             document_url=session_data.document_url,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow(),
#             message_count=0
#         )

#         session_id = await session_repo.create_session(session_doc)

#         session_response = convert_session_to_response({
#             "_id": session_id,
#             **session_doc.dict()
#         })

#         return {
#             "success": True,
#             "session_id": session_id,
#             "session": session_response.dict()
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @session_router.get("/list")
# async def list_sessions():
#     sessions = await session_repo.get_user_sessions(DEMO_USER_ID)

#     session_list = [
#         convert_session_to_response(s).dict()
#         for s in sessions
#     ]

#     return {
#         "success": True,
#         "sessions": session_list
#     }


# @session_router.get("/{session_id}/messages", response_model=ChatHistoryResponse)
# async def get_session_messages(session_id: str):
#     session = await session_repo.get_user_session(session_id, DEMO_USER_ID)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found")

#     messages = await message_repo.get_session_messages(session_id)

#     message_list = [
#         convert_message_to_response(m).dict()
#         for m in messages
#     ]

#     session_response = convert_session_to_response(session)

#     return ChatHistoryResponse(
#         session=session_response,
#         messages=message_list
#     )


# @session_router.delete("/{session_id}")
# async def delete_session(session_id: str):
#     deleted = await session_repo.delete_session(session_id, DEMO_USER_ID)
#     if not deleted:
#         raise HTTPException(status_code=404, detail="Session not found")

#     await message_repo.delete_session_messages(session_id)

#     return {"success": True}


# # ==================== UPLOAD ====================

# @upload_router.post("/upload-pdf", response_model=UploadResponse)
# async def upload_pdf(file: UploadFile = File(...)):

#     if not file.filename.lower().endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF files allowed")

#     content = await file.read()

#     if len(content) > settings.MAX_FILE_SIZE:
#         raise HTTPException(
#             status_code=400,
#             detail=f"File must be < {settings.MAX_FILE_SIZE // (1024*1024)}MB"
#         )

#     file_id = f"upload_{int(time.time())}_{DEMO_USERNAME}_{file.filename}"

#     upload_path = os.path.join(settings.UPLOAD_DIR, file_id)
#     os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

#     with open(upload_path, "wb") as f:
#         f.write(content)

#     return UploadResponse(
#         success=True,
#         file_id=file_id,
#         filename=file.filename,
#         message="PDF uploaded successfully"
#     )


# # ==================== CHAT ====================

# @chat_router.post("/chat")
# async def chat_endpoint(
#     question: str = Form(...),
#     session_id: str = Form(...)
# ):

#     session = await session_repo.get_user_session(session_id, DEMO_USER_ID)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found")

#     from ..models import MessageDocument

#     user_message = MessageDocument(
#         session_id=session_id,
#         type="user",
#         content=question,
#         created_at=datetime.utcnow()
#     )
#     await message_repo.create_message(user_message)

#     if session.get("document_id"):
#         doc_source = os.path.join(settings.UPLOAD_DIR, session["document_id"])
#         is_local_file = True
#     elif session.get("document_url"):
#         doc_source = session["document_url"]
#         is_local_file = False
#     else:
#         raise HTTPException(status_code=400, detail="No document attached")

#     from openai import AsyncAzureOpenAI
#     from ..document_processing import DocumentProcessor

#     client = AsyncAzureOpenAI(
#         api_version=settings.OPENAI_API_VERSION,
#         azure_endpoint=settings.OPENAI_API_BASE,
#         api_key=settings.OPENAI_API_KEY
#     )

#     doc_processor = DocumentProcessor(client)
#     rag_system = MultiAgentRAGSystem(client, doc_processor)

#     result = await rag_system.process_question(
#         question,
#         session_id,
#         doc_source,
#         is_local_file
#     )

#     bot_message = MessageDocument(
#         session_id=session_id,
#         type="bot",
#         content=result["answer"],
#         processing_time=result["processing_time"],
#         created_at=datetime.utcnow(),
#         metadata=result["metadata"]
#     )

#     await message_repo.create_message(bot_message)

#     await session_repo.increment_message_count(session_id, 2)
#     await session_repo.update_session(session_id, updated_at=datetime.utcnow())

#     return JSONResponse(result)


# # ==================== LEGACY ====================

# @legacy_router.post("/hackrx/run")
# async def hackrx_run(request: QueryRequest, authorization: str = Header(None)):

#     log_entry = {
#         "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
#         "auth_header": authorization,
#         "request_data": request.dict()
#     }

#     await log_repo.create_log_from_request(**log_entry)

#     from .. import document_processing

#     chunks, faiss_index = await document_processing.document_processor.get_or_process_document(
#         request.documents,
#         is_local_file=False
#     )

#     return {"answers": []}


# # ==================== HEALTH ====================

# @chat_router.get("/health")
# async def health_check():
#     return {
#         "status": "healthy",
#         "mode": "hackathon_single_user",
#         "user": DEMO_USERNAME
#     }


# # ==================== INCLUDE ROUTERS ====================

# def include_routers(app):
#     app.include_router(session_router)
#     app.include_router(upload_router)
#     app.include_router(chat_router)
#     app.include_router(legacy_router)

#     print("[API] Hackathon routers loaded successfully")




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

from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

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


# ==================== DEMO USER ====================

DEMO_USER_ID = "hackathon_user"
DEMO_USERNAME = "demo_user"


# ==================== ROUTERS ====================

session_router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
upload_router = APIRouter(prefix="/api/v1", tags=["uploads"])
chat_router = APIRouter(prefix="/api/v1", tags=["chat"])
legacy_router = APIRouter(prefix="/api/v1", tags=["legacy"])


# ==================== FLASHCARDS ROUTE ====================
@session_router.get("/{session_id}/flashcards")
async def get_flashcards(session_id: str):
    """
    Generate deterministic flashcards from stored document chunks.
    Returns 5 random flashcards per request.
    """

    session = await session_repo.get_user_session(session_id, DEMO_USER_ID)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.get("document_id"):
        raise HTTPException(status_code=400, detail="No document attached")

    doc_source = os.path.join(settings.UPLOAD_DIR, session["document_id"])

    from .. import document_processing
    from ..flashcards import generate_flashcards

    doc_processor = document_processing.document_processor

    if doc_processor is None:
        raise HTTPException(status_code=500, detail="Document processor not initialized")

    chunks, _ = await doc_processor.get_or_process_document(
        doc_source,
        is_local_file=True
    )

    flashcards = generate_flashcards(chunks, limit=5)

    return {
        "success": True,
        "total": len(flashcards),
        "flashcards": flashcards
    }

#=================quiz====================
# ================= QUIZ (NO LLM CALL) =================
# ================= QUIZ (RANDOM, NO LLM) =================
@session_router.post("/{session_id}/generate-quiz")
async def generate_quiz(session_id: str):

    import random

    session = await session_repo.get_user_session(session_id, DEMO_USER_ID)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.get("document_id"):
        raise HTTPException(status_code=400, detail="No document attached")

    doc_source = os.path.join(settings.UPLOAD_DIR, session["document_id"])

    from .. import document_processing
    doc_processor = document_processing.document_processor

    if doc_processor is None:
        raise HTTPException(status_code=500, detail="Document processor not initialized")

    # Get document chunks
    chunks, _ = await doc_processor.get_or_process_document(
        doc_source,
        is_local_file=True
    )

    if not chunks:
        return {
            "success": True,
            "quiz": []
        }

    # Shuffle chunks for randomness
    random.shuffle(chunks)

    # Select up to 5 chunks
    selected_chunks = chunks[:5]

    question_templates = [
        "What is the main idea of this section?",
        "Which concept is explained here?",
        "What responsibility is described?",
        "What skill or ability is highlighted?",
        "Summarize this concept briefly.",
        "What role or function is being discussed?",
        "What key point is mentioned here?"
    ]

    random.shuffle(question_templates)

    quiz = []

    for i, chunk in enumerate(selected_chunks):

        sentence = chunk.split(".")[0].strip()

        if not sentence:
            continue

        quiz.append({
            "question": f"Q{i+1}: {question_templates[i % len(question_templates)]}",
            "answer": f"A{i+1}: {sentence}"
        })

    return {
        "success": True,
        "quiz": quiz
    }

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

    user_message = MessageDocument(
        session_id=session_id,
        type="user",
        content=question,
        created_at=datetime.utcnow()
    )
    await message_repo.create_message(user_message)

    if session.get("document_id"):
        doc_source = os.path.join(settings.UPLOAD_DIR, session["document_id"])
        is_local_file = True
    elif session.get("document_url"):
        doc_source = session["document_url"]
        is_local_file = False
    else:
        raise HTTPException(status_code=400, detail="No document attached")

    from openai import AsyncAzureOpenAI
    from ..document_processing import DocumentProcessor

    client = AsyncAzureOpenAI(
        api_version=settings.OPENAI_API_VERSION,
        azure_endpoint=settings.OPENAI_API_BASE,
        api_key=settings.OPENAI_API_KEY
    )

    doc_processor = DocumentProcessor(client)
    rag_system = MultiAgentRAGSystem(client, doc_processor)

    result = await rag_system.process_question(
        question,
        session_id,
        doc_source,
        is_local_file
    )

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

    from .. import document_processing

    chunks, faiss_index = await document_processing.document_processor.get_or_process_document(
        request.documents,
        is_local_file=False
    )

    return {"answers": []}


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