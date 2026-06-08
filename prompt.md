# Build Instructions: RAG-based Investment & FAQ Chatbot (Ollama Local)

## Overview

Build a Flask-based RAG chatbot **from scratch** that answers financial FAQs and suggests
personalized investment options. The LLM backend runs **entirely locally via Ollama** — no API
keys or cloud services required. The design follows a **single-agent** pattern: one LLM call per
user turn, with intent detection and context retrieval handled in pure Python before that call.

Build every file listed below. Do not skip any step. Do not assume any file already exists.

---

## Prerequisites

Before running the app, install Ollama and pull a model:

```bash
# Install Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (choose one based on your hardware)
ollama pull llama3        # Best balance of quality and speed (~4.7 GB)
# ollama pull mistral     # Lighter alternative (~4.1 GB)
# ollama pull phi3        # Smallest/fastest (~2.3 GB)

# Start the Ollama server (runs on http://localhost:11434)
ollama serve
```

---

## Target Project Structure

```
investment-chatbot/
├── app.py
├── requirements.txt
├── .env
├── README.md
├── rag/
│   ├── __init__.py
│   ├── knowledge_base.py
│   ├── user_profile.py
│   ├── router.py
│   └── llm.py
└── data/
    ├── faqs/
    │   └── sample_faqs.txt
    └── investments/
        └── products.txt
```

---

## Step 1: Create `requirements.txt`

```
flask>=3.0.0
chromadb>=0.4.0
sentence-transformers>=2.2.2
langchain>=0.1.0
langchain-community>=0.0.20
pypdf>=3.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## Step 2: Create `.env`

```
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
FLASK_DEBUG=true
```

---

## Step 3: Create `data/faqs/sample_faqs.txt`

```
Q: How do I open an account?
A: You can open an account online by visiting our website, clicking 'Open Account', and completing the KYC process with your PAN card, Aadhaar, and bank details. The process takes 10-15 minutes.

Q: What KYC documents are required?
A: You need a PAN card (mandatory), Aadhaar card or Passport for address proof, a cancelled cheque or bank statement, and a passport-sized photograph.

Q: How long does KYC verification take?
A: KYC verification typically takes 1-2 business days. You will receive an email confirmation once your account is activated.

Q: Can I have a joint account?
A: Yes, we support joint accounts with up to 3 holders. The primary holder must complete full KYC and all joint holders must submit their PAN and address proof.

Q: What is the minimum investment amount?
A: The minimum investment varies by product. SIP starts at Rs.500/month, Lump sum mutual funds at Rs.1000, and Fixed Deposits at Rs.10,000.

Q: How do I withdraw my investments?
A: Log in to your account, go to 'My Portfolio', select the investment, and click 'Redeem'. Funds are credited to your registered bank account within 2-3 business days for mutual funds, and on maturity for FDs.

Q: Is my investment insured?
A: Mutual fund investments are not insured or guaranteed by the government. Fixed Deposits up to Rs.5 lakh are insured under DICGC. All investments are subject to market risks.

Q: How do I update my bank account details?
A: Go to 'Profile Settings' > 'Bank Accounts' and submit a new bank account with a cancelled cheque. Verification takes 24 hours.

Q: What are the tax implications of my investments?
A: ELSS funds qualify for Rs.1.5 lakh deduction under Section 80C. Equity fund gains held over 1 year are taxed at 10% (LTCG). Debt fund gains are taxed as per your income slab.

Q: How do I contact customer support?
A: You can reach us via email at support@example.com, call our helpline at 1800-XXX-XXXX (Mon-Sat, 9 AM-6 PM), or use the live chat on our website.

Q: Can I invest on behalf of a minor?
A: Yes, a guardian can invest on behalf of a minor. The account is held in the minor's name with the guardian as operator until the minor turns 18.

Q: What happens if I miss a SIP installment?
A: If your bank account has insufficient funds, the SIP installment is skipped for that month. Three consecutive failures may result in SIP cancellation. There is no penalty for a missed installment.
```

---

## Step 4: Create `data/investments/products.txt`

```
PRODUCT: Equity Mutual Funds
Type: Market-linked
Risk Level: High
Minimum Investment: Rs.1000 lump sum, Rs.500/month SIP
Expected Returns: 10-14% per annum (long-term historical average)
Investment Horizon: Long-term (5+ years)
Ideal For: Young investors (age 20-40), high risk appetite, wealth growth goals
Tax Benefit: ELSS category qualifies under Section 80C (Rs.1.5L deduction)
Notes: Returns not guaranteed. Best suited for investors who can tolerate short-term volatility.

PRODUCT: Debt Mutual Funds
Type: Market-linked (lower risk)
Risk Level: Low to Medium
Minimum Investment: Rs.1000 lump sum, Rs.500/month SIP
Expected Returns: 6-8% per annum
Investment Horizon: Short to Medium-term (1-3 years)
Ideal For: Conservative investors, capital preservation goals, parking surplus funds
Tax Benefit: Taxed as per income slab
Notes: Lower volatility than equity. Suitable for investors nearing a financial goal.

PRODUCT: Hybrid / Balanced Funds
Type: Market-linked (mix of equity + debt)
Risk Level: Medium
Minimum Investment: Rs.1000 lump sum, Rs.500/month SIP
Expected Returns: 8-11% per annum
Investment Horizon: Medium to Long-term (3-7 years)
Ideal For: Moderate risk appetite, balanced growth and stability goals
Notes: Auto-rebalancing between equity and debt. Good for first-time investors.

PRODUCT: Fixed Deposit (FD)
Type: Fixed income
Risk Level: Very Low (DICGC insured up to Rs.5 lakh)
Minimum Investment: Rs.10,000
Expected Returns: 6-7.5% per annum
Investment Horizon: Short to Long-term (6 months - 10 years)
Ideal For: Risk-averse investors, senior citizens, capital safety goals
Tax Benefit: 5-year tax-saving FD qualifies under Section 80C
Notes: Premature withdrawal attracts a penalty. Interest is taxable as income.

PRODUCT: Public Provident Fund (PPF)
Type: Government-backed fixed income
Risk Level: None (sovereign guarantee)
Minimum Investment: Rs.500/year, Maximum Rs.1.5 lakh/year
Expected Returns: 7.1% per annum (government-set, revised quarterly)
Investment Horizon: Long-term (15-year lock-in)
Ideal For: Very conservative investors, retirement planning, tax saving
Tax Benefit: EEE status - contribution, interest, and maturity all tax-free
Notes: Partial withdrawal allowed from year 7. Loan facility available from year 3.

PRODUCT: National Pension System (NPS)
Type: Government-backed market-linked
Risk Level: Low to High (depends on asset allocation chosen)
Minimum Investment: Rs.500/contribution, Rs.1000/year minimum
Expected Returns: 8-10% per annum (equity option, long-term)
Investment Horizon: Very Long-term (until age 60)
Ideal For: Salaried individuals, retirement planning, tax optimization
Tax Benefit: Additional Rs.50,000 deduction under Section 80CCD(1B) over 80C limit
Notes: At retirement, 40% must be used to purchase annuity. 60% can be withdrawn tax-free.

PRODUCT: ELSS (Equity Linked Savings Scheme)
Type: Market-linked equity mutual fund
Risk Level: High
Minimum Investment: Rs.500/month SIP or Rs.1000 lump sum
Expected Returns: 10-14% per annum (long-term)
Investment Horizon: Minimum 3 years (shortest lock-in among 80C options)
Ideal For: Tax-saving investors willing to take equity risk, age 25-45
Tax Benefit: Up to Rs.1.5 lakh deduction under Section 80C
Notes: Shortest lock-in among all Section 80C instruments. Returns market-linked.

PRODUCT: Systematic Investment Plan (SIP)
Type: Investment method (applicable to mutual funds)
Risk Level: Depends on fund category chosen
Minimum Investment: Rs.500/month
Expected Returns: Varies by fund (6-14% depending on category)
Investment Horizon: Recommended 3+ years for equity SIPs
Ideal For: Salaried investors, rupee cost averaging, disciplined long-term investing
Notes: SIPs reduce timing risk through rupee cost averaging. Can be paused or stopped anytime.
```

---

## Step 5: Create `rag/__init__.py`

Create an empty file at this path. No content needed.

---

## Step 6: Create `rag/llm.py`

This module wraps the Ollama HTTP API. It is the **only** place in the codebase that calls an LLM.

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def chat(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    """
    Single-agent LLM call via Ollama's /api/chat endpoint.
    Returns the assistant reply as a plain string.
    Raises RuntimeError if Ollama is unreachable or returns an error.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"num_predict": max_tokens},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot reach Ollama at {OLLAMA_BASE_URL}. "
            "Make sure 'ollama serve' is running."
        )
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")


def health_check() -> dict:
    """Returns model name and connection status. Used by the /status route."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        model_found = any(OLLAMA_MODEL in m for m in models)
        if not model_found:
            return {
                "status": f"warning: model '{OLLAMA_MODEL}' not pulled. "
                          f"Run: ollama pull {OLLAMA_MODEL}",
                "model": OLLAMA_MODEL,
                "available_models": models,
            }
        return {"status": "ok", "model": OLLAMA_MODEL, "available_models": models}
    except Exception as e:
        return {"status": f"error: {e}", "model": OLLAMA_MODEL}
```

---

## Step 7: Create `rag/knowledge_base.py`

This module handles document loading, chunking, embedding, and ChromaDB retrieval.

```python
import os
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
```

---

## Step 8: Create `rag/user_profile.py`

```python
from dataclasses import dataclass, field


@dataclass
class UserProfile:
    age: int
    monthly_income: float
    risk_appetite: str        # "low" | "medium" | "high"
    investment_goal: str      # e.g. "retirement", "wealth growth", "child education"
    investment_horizon: str   # "short" | "medium" | "long"
    existing_investments: list = field(default_factory=list)


def profile_to_query(profile: UserProfile) -> str:
    """Convert a UserProfile into a natural language retrieval query."""
    existing = (
        f"already has {', '.join(profile.existing_investments)}"
        if profile.existing_investments
        else "no existing investments"
    )
    return (
        f"investment options for {profile.age} year old, "
        f"monthly income Rs.{profile.monthly_income:,.0f}, "
        f"{profile.risk_appetite} risk appetite, "
        f"goal: {profile.investment_goal}, "
        f"{profile.investment_horizon}-term investment horizon, "
        f"{existing}"
    )
```

---

## Step 9: Create `rag/router.py`

```python
INVESTMENT_KEYWORDS = [
    "invest", "investment", "returns", "sip", "mutual fund", "stocks", "equity",
    "debt", "fd", "fixed deposit", "portfolio", "risk", "wealth", "savings",
    "nps", "elss", "ppf", "retire", "retirement", "goal", "tax saving",
    "hybrid", "lump sum", "dividend", "nav", "fund", "scheme", "maturity",
    "interest rate", "asset", "capital", "grow money", "where to invest",
    "suggest", "recommend", "should i invest",
]

FAQ_KEYWORDS = [
    "how", "what", "when", "why", "can i", "do i", "is it", "are there",
    "policy", "terms", "process", "eligibility", "document", "account",
    "kyc", "withdraw", "redemption", "login", "register", "support",
    "contact", "charges", "fees", "procedure", "open account", "close account",
]


def detect_intent(user_message: str) -> str:
    """
    Keyword-based intent classifier. No LLM call.
    Returns one of: 'faq' | 'investment' | 'general'
    """
    msg = user_message.lower()

    for kw in INVESTMENT_KEYWORDS:
        if kw in msg:
            return "investment"

    for kw in FAQ_KEYWORDS:
        if kw in msg:
            return "faq"

    if "?" in user_message:
        return "faq"

    return "general"
```

---

## Step 10: Create `app.py`

This is the main Flask application. Build it entirely from scratch as shown below.

```python
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from rag.knowledge_base import retrieve, ingest_documents
from rag.user_profile import UserProfile, profile_to_query
from rag.router import detect_intent
from rag import llm

load_dotenv()

app = Flask(__name__)

# --- Startup: check Ollama connection ---
connection_status = llm.health_check()
print(f"Ollama status: {connection_status}")

# --- Startup: build RAG knowledge base ---
rag_status = "not initialized"
try:
    ingest_documents()
    rag_status = "ready"
except Exception as e:
    print(f"RAG initialization failed: {e}")
    rag_status = f"error: {str(e)}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'ollama_status': connection_status,
        'rag_status': rag_status,
        'model': connection_status.get('model'),
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    General chat endpoint. Detects intent, retrieves context, calls Ollama once.

    Expected JSON body:
    {
        "message": "How do I open an account?",
        "user_profile": { ... }   // optional, used only for investment intent
    }
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        user_profile_data = data.get('user_profile', None)

        if not user_message:
            return jsonify({'error': 'Empty message'}), 400

        intent = detect_intent(user_message)

        if intent == "faq":
            context_chunks = retrieve(user_message, collection="faqs", top_k=3)
            context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant FAQ found."
            system_prompt = (
                "You are a helpful financial services assistant. "
                "Answer the user's question using ONLY the following FAQ context. "
                "If the answer is not in the context, say: 'I don't have information on that — "
                "please contact our support team.'\n\n"
                f"FAQ Context:\n{context_text}"
            )

        elif intent == "investment":
            if user_profile_data:
                try:
                    profile = UserProfile(**user_profile_data)
                    retrieval_query = profile_to_query(profile)
                    profile_summary = (
                        f"Age: {profile.age}, Income: Rs.{profile.monthly_income:,.0f}/month, "
                        f"Risk: {profile.risk_appetite}, Goal: {profile.investment_goal}, "
                        f"Horizon: {profile.investment_horizon}, "
                        f"Existing: {', '.join(profile.existing_investments) or 'None'}"
                    )
                except Exception:
                    retrieval_query = user_message
                    profile_summary = "Not provided"
            else:
                retrieval_query = user_message
                profile_summary = "Not provided"

            context_chunks = retrieve(retrieval_query, collection="investments", top_k=4)
            context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant products found."
            system_prompt = (
                "You are a knowledgeable investment advisor. "
                "Suggest suitable investment options based on the user profile and product information below. "
                "Mention product names, expected returns, risk levels, and suitability reasoning. "
                "Always note that past returns do not guarantee future performance.\n\n"
                f"User Profile: {profile_summary}\n\n"
                f"Available Investment Products:\n{context_text}"
            )

        else:
            system_prompt = (
                "You are a helpful financial services chatbot. "
                "Answer the user's question in a clear and professional manner."
            )

        assistant_message = llm.chat(system_prompt=system_prompt, user_message=user_message)
        return jsonify({'response': assistant_message, 'intent': intent})

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500


@app.route('/profile-chat', methods=['POST'])
def profile_chat():
    """
    Dedicated endpoint for personalized investment recommendations.

    Expected JSON body:
    {
        "message": "What should I invest in?",
        "profile": {
            "age": 30,
            "monthly_income": 80000,
            "risk_appetite": "medium",
            "investment_goal": "retirement",
            "investment_horizon": "long",
            "existing_investments": ["PPF"]
        }
    }
    """
    try:
        data = request.json
        user_message = data.get('message', 'What investment options suit my profile?').strip()
        profile_data = data.get('profile', {})

        if not profile_data:
            return jsonify({'error': 'Profile data is required. Use /chat for general queries.'}), 400

        try:
            profile = UserProfile(**profile_data)
            retrieval_query = profile_to_query(profile)
            profile_summary = (
                f"Age: {profile.age}, Income: Rs.{profile.monthly_income:,.0f}/month, "
                f"Risk Appetite: {profile.risk_appetite}, Goal: {profile.investment_goal}, "
                f"Horizon: {profile.investment_horizon}, "
                f"Existing Investments: {', '.join(profile.existing_investments) or 'None'}"
            )
        except TypeError as e:
            return jsonify({'error': f'Invalid profile fields: {str(e)}'}), 400

        context_chunks = retrieve(retrieval_query, collection="investments", top_k=5)
        context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant products found."

        system_prompt = (
            "You are a certified financial advisor providing personalized investment recommendations. "
            "Based on the user profile and products below, recommend 2-4 suitable investment options. "
            "For each: state product name, why it fits their profile, expected returns, risk level, "
            "and minimum investment. Use bullet points. End with a short market risk disclaimer.\n\n"
            f"User Profile:\n{profile_summary}\n\n"
            f"Available Investment Products:\n{context_text}"
        )

        assistant_message = llm.chat(system_prompt=system_prompt, user_message=user_message)
        return jsonify({
            'response': assistant_message,
            'profile_used': profile_summary,
            'intent': 'investment'
        })

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", port=5000)
```

---

## Step 11: Create `README.md`

Create a `README.md` file at the project root with the following content:

````markdown
# Investment & FAQ Chatbot

A locally-running RAG-based chatbot that answers financial FAQs and provides personalised
investment recommendations. No API keys or cloud services required — powered entirely by
**Ollama** (local LLM) and **ChromaDB** (local vector store).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask |
| LLM | Ollama (llama3 / mistral / phi3) |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`) |
| Vector Store | ChromaDB (persistent, local) |
| Document Loading | LangChain Community |
| Intent Detection | Keyword-based Python router |

---

## Architecture

```
User message
     │
     ▼
detect_intent()          ← keyword-based Python router (no LLM call)
     │
     ▼
retrieve() from ChromaDB ← dense vector search (SentenceTransformers)
     │
     ▼
Build system_prompt      ← Python string construction
     │
     ▼
llm.chat()               ← ONE Ollama LLM call (llama3 / mistral / phi3)
     │
     ▼
JSON response to client
```

There is exactly **one LLM call per user request**. Intent detection and retrieval are pure
Python — fast, deterministic, and free.

---

## Project Structure

```
investment-chatbot/
├── app.py                        # Flask app and all API routes
├── requirements.txt
├── .env                          # Ollama model config
├── README.md
├── rag/
│   ├── __init__.py
│   ├── llm.py                    # Ollama HTTP wrapper (single LLM call)
│   ├── knowledge_base.py         # Document ingestion + ChromaDB retrieval
│   ├── user_profile.py           # UserProfile dataclass + query builder
│   └── router.py                 # Keyword-based intent classifier
└── data/
    ├── faqs/
    │   └── sample_faqs.txt       # FAQ knowledge base
    └── investments/
        └── products.txt          # Investment product catalogue
```

---

## Setup

### 1. Install Ollama and pull a model

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3     # or: mistral, phi3
ollama serve           # keep this running in a separate terminal
```

### 2. Clone / create the project and install Python dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

The `.env` file ships with sensible defaults. Edit if needed:

```
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
FLASK_DEBUG=true
```

### 4. Run the app

```bash
python app.py
```

The server starts at `http://localhost:5000`. On first run, documents are automatically
loaded, chunked, embedded, and indexed into ChromaDB. Subsequent runs skip re-indexing
(unless you delete the `chroma_db/` folder).

---

## API Reference

### `GET /status`

Returns Ollama connection health and RAG status.

**Response:**
```json
{
  "ollama_status": { "status": "ok", "model": "llama3", "available_models": ["llama3"] },
  "rag_status": "ready",
  "model": "llama3"
}
```

---

### `POST /chat`

General chat endpoint. Intent is detected automatically.

**Request:**
```json
{
  "message": "How do I open an account?",
  "user_profile": {              
    "age": 28,
    "monthly_income": 60000,
    "risk_appetite": "medium",
    "investment_goal": "wealth growth",
    "investment_horizon": "long",
    "existing_investments": []
  }
}
```
`user_profile` is optional and only used when the message is classified as investment intent.

**Response:**
```json
{
  "response": "To open an account, visit our website and click 'Open Account'...",
  "intent": "faq"
}
```

Possible `intent` values: `faq` | `investment` | `general`

---

### `POST /profile-chat`

Dedicated endpoint for personalised investment recommendations. Requires a `profile` object.

**Request:**
```json
{
  "message": "What should I invest in?",
  "profile": {
    "age": 30,
    "monthly_income": 80000,
    "risk_appetite": "medium",
    "investment_goal": "retirement",
    "investment_horizon": "long",
    "existing_investments": ["PPF"]
  }
}
```

**Response:**
```json
{
  "response": "Based on your profile, here are 3 suitable options...",
  "profile_used": "Age: 30, Income: Rs.80,000/month, Risk Appetite: medium...",
  "intent": "investment"
}
```

**Profile field reference:**

| Field | Type | Allowed values |
|---|---|---|
| `age` | int | Any positive integer |
| `monthly_income` | float | Monthly income in Rs. |
| `risk_appetite` | string | `"low"` / `"medium"` / `"high"` |
| `investment_goal` | string | e.g. `"retirement"`, `"wealth growth"`, `"child education"` |
| `investment_horizon` | string | `"short"` / `"medium"` / `"long"` |
| `existing_investments` | list[string] | e.g. `["PPF", "FD"]` or `[]` |

---

## Extending the Knowledge Base

To add more documents, drop `.txt` or `.pdf` files into:

- `data/faqs/` — for FAQ content
- `data/investments/` — for product/scheme information

Then delete the `chroma_db/` folder and restart the app. Documents are re-indexed automatically.

---

## Switching Models

Edit `.env`:

```
OLLAMA_MODEL=mistral    # or phi3, llama3, gemma, etc.
```

Make sure the model is pulled first: `ollama pull mistral`

---

## Troubleshooting

**`Cannot reach Ollama`** — Run `ollama serve` in a separate terminal before starting Flask.

**`model 'llama3' not found`** — Run `ollama pull llama3`.

**Slow first response** — Normal. The model loads into memory on first use. Subsequent calls are faster.

**Re-index documents** — Delete the `chroma_db/` folder and restart the app.
````

---

## Final Checklist

After building all files, verify:

- [ ] `requirements.txt` created with all 8 dependencies
- [ ] `.env` created with `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `FLASK_DEBUG`
- [ ] `data/faqs/sample_faqs.txt` exists with all 12 Q&A pairs
- [ ] `data/investments/products.txt` exists with all 8 product entries
- [ ] `rag/__init__.py` exists (empty)
- [ ] `rag/llm.py` has `chat()` and `health_check()` functions
- [ ] `rag/knowledge_base.py` has `ingest_documents()` and `retrieve()` functions
- [ ] `rag/user_profile.py` has `UserProfile` dataclass and `profile_to_query()` function
- [ ] `rag/router.py` has `detect_intent()` function
- [ ] `app.py` imports from all `rag/` modules; has `/status`, `/chat`, `/profile-chat` routes
- [ ] `app.py` calls `ingest_documents()` at startup, before any route
- [ ] `README.md` created at project root with full documentation
- [ ] `ollama serve` is running and the chosen model has been pulled before `python app.py`

---

## Architecture Notes

This is a **single-agent** design — one LLM call per request, no tool-calling loops or agent
orchestration. Intent detection (`router.py`) and retrieval (`knowledge_base.py`) are pure Python,
making the pipeline fast and deterministic. The LLM (`llm.py`) is only responsible for generating
the final natural language response.
