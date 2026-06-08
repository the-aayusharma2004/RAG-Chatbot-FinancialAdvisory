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
