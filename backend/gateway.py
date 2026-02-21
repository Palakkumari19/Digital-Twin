# import os
# import sys
# from dotenv import load_dotenv
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# # ==============================
# # Environment Setup
# # ==============================

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# load_dotenv(os.path.join(BASE_DIR, ".env"))

# # If you want RAG later, keep this:
# sys.path.insert(0, os.path.join(BASE_DIR, "rag_engine"))

# # ==============================
# # Import Engines
# # ==============================

# from simple_engine.main import app as simple_app
# # from rag_engine.main import app as rag_app   # KEEP COMMENTED FOR NOW

# # ==============================
# # Create Unified App
# # ==============================

# app = FastAPI(title="Digital Memory Twin - Unified Backend")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.mount("/simple", simple_app)
# # app.mount("/rag", rag_app)   # KEEP COMMENTED

# @app.get("/")
# async def root():
#     return {
#         "message": "Unified Backend Running",
#         "routes": {
#             "simple": "/simple",
#             "rag": "/rag (disabled temporarily)"
#         }
#     }


import os
import sys
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Make rag_engine importable
sys.path.insert(0, os.path.join(BASE_DIR, "rag_engine"))

from simple_engine.main import app as simple_app
from rag_engine.main import app as rag_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Trigger rag_engine startup
    if rag_app.router.lifespan_context:
        async with rag_app.router.lifespan_context(rag_app):
            yield
    else:
        yield


app = FastAPI(
    title="Digital Memory Twin - Unified Backend",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/simple", simple_app)
app.mount("/rag", rag_app)


@app.get("/")
async def root():
    return {
        "message": "Unified Backend Running",
        "routes": {
            "simple": "/simple",
            "rag": "/rag"
        }
    }