import chromadb
from chromadb.utils import embedding_functions
import requests
import uuid

# =============================
# EMBEDDING MODEL (Lightweight)
# =============================

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# =============================
# CHROMA INITIALIZATION
# =============================

client = chromadb.Client()

collection = client.get_or_create_collection(
    name="notes",
    embedding_function=embedding_function
)

# =============================
# TEXT SPLITTER
# =============================

def split_text(text, chunk_size=300, overlap=50):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


# =============================
# ADD DOCUMENT
# =============================

def add_document(text: str):
    if not text.strip():
        return "Empty text. Nothing uploaded."

    chunks = split_text(text)

    for chunk in chunks:
        collection.add(
            documents=[chunk],
            ids=[str(uuid.uuid4())]
        )

    return "Document uploaded successfully."


# =============================
# QUERY RAG
# =============================

def query_rag(question: str):

    if not question.strip():
        return "Please enter a valid question."

    results = collection.query(
        query_texts=[question],
        n_results=2   # Keep low for speed
    )

    # Handle empty DB case
    if not results["documents"] or not results["documents"][0]:
        return "No documents found. Please upload notes first."

    context = "\n".join(results["documents"][0])

    return generate_answer(context, question)


# =============================
# LLM GENERATION (OLLAMA)
# =============================

def generate_answer(context, question):

    prompt = f"""
You are a factual AI assistant.

STRICT RULES:
- Use ONLY the provided context.
- If the answer is not explicitly in the context, say:
  "I could not find this information in the uploaded documents."
- Do NOT guess.
- Do NOT use outside knowledge.
- Keep the answer under 4 sentences.
- Be concise and direct.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 80,
                    "num_ctx": 1024
                }
            },
            timeout=60
        )

        response.raise_for_status()

        return response.json()["response"].strip()

    except requests.exceptions.RequestException as e:
        return f"LLM Error: {str(e)}"
