import os
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
FAQ_DIR = os.path.join(BASE_DIR, "data", "faqs")
INVESTMENT_DIR = os.path.join(BASE_DIR, "data", "investments")

print("Loading embedding model (all-MiniLM-L6-v2)...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model loaded.")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)


def _load_documents_from_dir(directory: str) -> list:
    docs = []
    if not os.path.exists(directory):
        print(f"Warning: directory not found: {directory}")
        return docs
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        try:
            if filename.endswith(".txt"):
                loader = TextLoader(filepath, encoding="utf-8")
            elif filename.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
            else:
                continue
            loaded = loader.load()
            docs.extend(loaded)
            print(f"  Loaded: {filename} ({len(loaded)} page(s))")
        except Exception as e:
            print(f"  Error loading {filename}: {e}")
    return docs


def _chunk_documents(docs: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    return [chunk.page_content for chunk in splitter.split_documents(docs)]


def _upsert_to_collection(collection_name: str, texts: list):
    collection = chroma_client.get_or_create_collection(name=collection_name)
    if collection.count() > 0:
        print(f"  '{collection_name}' already indexed ({collection.count()} chunks). Skipping.")
        return
    if not texts:
        print(f"  No texts to index for '{collection_name}'.")
        return
    print(f"  Embedding {len(texts)} chunks into '{collection_name}'...")
    embeddings = embedding_model.encode(texts, show_progress_bar=False).tolist()
    ids = [f"{collection_name}_{i}" for i in range(len(texts))]
    collection.add(documents=texts, embeddings=embeddings, ids=ids)
    print(f"  Done: {len(texts)} chunks indexed.")


def ingest_documents():
    """Load, chunk, embed, and store all documents into ChromaDB. Called once at startup."""
    print("\n--- Ingesting documents into RAG knowledge base ---")
    faq_docs = _load_documents_from_dir(FAQ_DIR)
    _upsert_to_collection("faqs", _chunk_documents(faq_docs))

    inv_docs = _load_documents_from_dir(INVESTMENT_DIR)
    _upsert_to_collection("investments", _chunk_documents(inv_docs))
    print("--- RAG knowledge base ready ---\n")


def retrieve(query: str, collection: str, top_k: int = 3) -> list:
    """Return the top_k most relevant text chunks for a given query."""
    try:
        col = chroma_client.get_collection(name=collection)
        query_embedding = embedding_model.encode([query]).tolist()
        results = col.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, col.count())
        )
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        print(f"Retrieval error from '{collection}': {e}")
        return []
