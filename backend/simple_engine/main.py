from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
import re
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_store: List[Dict] = []

class UploadRequest(BaseModel):
    text: str

class AskRequest(BaseModel):
    question: str


def chunk_text(text: str):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def extract_entities(text: str):
    # Multi-word capitalized entities
    return re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)


@app.post("/upload")
def upload_notes(data: UploadRequest):
    chunks = chunk_text(data.text)

    for chunk in chunks:
        entities = extract_entities(chunk)

        memory_store.append({
            "id": str(uuid.uuid4()),
            "content": chunk,
            "entities": entities
        })

    return {
        "message": "Stored successfully",
        "chunks_created": len(chunks)
    }


@app.post("/ask")
def ask_question(data: AskRequest):
    stop_words = {"what", "is", "the", "a", "an", "does", "do", "who", "of", "in", "was"}

    question_words = [
        word.lower()
        for word in re.findall(r'\w+', data.question)
        if word.lower() not in stop_words
    ]

    best_match = None
    best_score = 0

    for item in memory_store:
        content_lower = item["content"].lower()

        score = sum(1 for word in question_words if word in content_lower)

        if score > best_score:
            best_score = score
            best_match = item

    if best_match and best_score > 0:
        return {
            "answer": best_match["content"],
            "sources": ["Memory Chunk"]
        }

    return {
        "answer": "No relevant memory found.",
        "sources": []
    }



@app.get("/graph")
def get_graph():
    nodes = {}
    edges = []

    for item in memory_store:
        entities = item.get("entities", [])

        for entity in entities:
            nodes[entity] = {"id": entity}

        # connect entities within same sentence
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                edges.append({
                    "source": entities[i],
                    "target": entities[j]
                })

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }
