import os
import threading

import chromadb
from chromadb.errors import NotFoundError
from sentence_transformers import SentenceTransformer

from logic.agents import KB_PATH

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")
COLLECTION_NAME = "knowledge_base"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 128
AVAILABLE_CHUNK_SIZES = [64, 128, 192, 256]
TOP_K = 3

_model = None
_model_lock = threading.Lock()

_client = None
_client_lock = threading.Lock()

_status = "not_started"  # not_started | building | ready | error
_status_error = None
_status_lock = threading.Lock()

# Serializes build_index calls so an overlapping rebuild (e.g. a settings save
# racing a /chunks re-run) queues up instead of corrupting the collection.
_build_lock = threading.Lock()

_last_chunk_size = DEFAULT_CHUNK_SIZE
_last_chunks = []


def _get_model():
    global _model
    with _model_lock:
        if _model is None:
            _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def _get_client():
    global _client
    with _client_lock:
        if _client is None:
            _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def _count_tokens(text):
    tokenizer = _get_model().tokenizer
    return len(tokenizer(text, add_special_tokens=False)["input_ids"])


def _load_kb_text():
    with open(KB_PATH, encoding="utf-8") as f:
        return f.read()


def chunk_markdown(text, chunk_size=DEFAULT_CHUNK_SIZE, count_tokens=None):
    """Splits markdown into ~chunk_size token chunks, keeping related lines together.

    Lines are never split mid-line. Each heading starts a new section, and its
    text is prefixed onto every chunk under it so a chunk stays readable on its
    own. A chunk closes once the next line would push it past chunk_size tokens.
    """
    count_tokens = count_tokens or _count_tokens
    lines = text.split("\n")

    raw_chunks = []
    section = ""
    header_tokens = 0
    current_lines = []
    current_tokens = header_tokens

    def flush():
        nonlocal current_lines, current_tokens
        if current_lines:
            body = "\n".join(current_lines).strip()
            if body:
                full_text = f"{section}\n{body}" if section else body
                raw_chunks.append({"section": section, "text": full_text})
        current_lines = []
        current_tokens = header_tokens

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line:
            continue

        if line.startswith("#"):
            flush()
            section = line.lstrip("#").strip()
            header_tokens = count_tokens(section)
            current_tokens = header_tokens
            continue

        line_tokens = count_tokens(line)
        if current_lines and current_tokens + line_tokens > chunk_size:
            flush()

        current_lines.append(line)
        current_tokens += line_tokens

    flush()

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunks.append({
            "id": str(i),
            "section": chunk["section"],
            "text": chunk["text"],
            "token_count": count_tokens(chunk["text"]),
        })
    return chunks


def build_index(chunk_size=None):
    """Chunks the knowledge base, embeds each chunk, and stores them in ChromaDB.

    Runs synchronously on the calling thread/process; use rebuild_index_async
    or ensure_index_building for a non-blocking call.
    """
    global _status, _status_error, _last_chunk_size, _last_chunks

    with _status_lock:
        _status = "building"
        _status_error = None

    try:
        with _build_lock:
            size = chunk_size or _last_chunk_size
            chunks = chunk_markdown(_load_kb_text(), chunk_size=size)
            if not chunks:
                raise RuntimeError("No chunks produced from the knowledge base file.")

            model = _get_model()
            embeddings = model.encode([c["text"] for c in chunks], normalize_embeddings=True).tolist()

            client = _get_client()
            try:
                client.delete_collection(COLLECTION_NAME)
            except NotFoundError:
                pass
            collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

            collection.add(
                ids=[c["id"] for c in chunks],
                embeddings=embeddings,
                documents=[c["text"] for c in chunks],
                metadatas=[{"section": c["section"], "token_count": c["token_count"]} for c in chunks],
            )

            _last_chunk_size = size
            _last_chunks = chunks

        with _status_lock:
            _status = "ready"
    except Exception as e:
        with _status_lock:
            _status = "error"
            _status_error = str(e)
        raise


def rebuild_index_async(chunk_size=None):
    thread = threading.Thread(target=build_index, args=(chunk_size,), daemon=True)
    thread.start()


def ensure_index_building():
    """Triggers a background build the first time this is called; a no-op after that."""
    global _status
    with _status_lock:
        if _status != "not_started":
            return
        _status = "building"

    thread = threading.Thread(target=build_index, args=(_last_chunk_size,), daemon=True)
    thread.start()


def get_status():
    with _status_lock:
        return {"status": _status, "error": _status_error}


def get_chunks():
    return _last_chunks


def get_chunk_size():
    return _last_chunk_size


def retrieve(query, top_k=TOP_K):
    """Embeds the query and returns the top_k most similar chunks with similarity scores."""
    client = _get_client()
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except NotFoundError:
        return []

    model = _get_model()
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    sources = []
    for i, (chunk_id, doc, distance, meta) in enumerate(zip(ids, documents, distances, metadatas), start=1):
        similarity = max(0.0, min(1.0, 1 - distance))
        sources.append({
            "index": i,
            "id": chunk_id,
            "text": doc,
            "section": meta.get("section", ""),
            "similarity": round(similarity, 3),
        })

    return sources
