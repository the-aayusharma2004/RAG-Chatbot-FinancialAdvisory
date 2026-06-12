# InvestAI — Hybrid RAG + SQL Investment & FAQ Chatbot

A locally-running, full-stack financial advisor powered by **Ollama** (local LLM), **ChromaDB** (RAG vector store), and **MySQL** (live portfolio data). No API keys or cloud services required.

---

## What's New in Phase 3

A premium **financial dashboard** has been added on top of the existing API backend:

| Feature | Description |
|---|---|
| 📊 Portfolio Summary | Live summary cards: invested, current value, gain/loss, holdings count |
| 📂 Holdings Dashboard | Detailed breakdown of each investment position with risk badges |
| 🎯 Goal Tracking | Progress bars and completion percentages for each financial goal |
| 🔄 Transaction History | Paginated table of recent investment transactions |
| 🤖 AI Advisor Chat | Multi-mode chatbot: FAQ, investment advice, portfolio Q&A, hybrid |
| 🔍 Portfolio Analysis | One-click AI analysis: SQL data + RAG knowledge → personalised advice |
| 👤 User Switcher | Switch between seeded users (Arjun, Priya, Rohit) |
| ⚙️ System Status | Live status indicators for Ollama, MySQL, and RAG |
| 📱 Responsive Design | Full desktop sidebar + chat layout; stacked mobile layout |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask |
| LLM | Ollama (llama3 / mistral / phi3) — runs locally |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`) |
| Vector Store | ChromaDB (persistent, local) |
| Database | MySQL + SQLAlchemy ORM |
| Document Loading | LangChain Community |
| Intent Detection | Keyword-based Python router (no LLM) |
| Frontend | Vanilla HTML + CSS + JavaScript |

---

## Architecture

```
User (Browser)
     │
     ▼
Frontend (HTML + CSS + JS)
     │  calls REST APIs
     ▼
Flask Application (app.py)
     │
     ├── Intent Router (rag/router.py)       ← no LLM, pure keyword matching
     │     faq | investment | sql | hybrid | general
     │
     ├── RAG Layer (rag/)
     │     ├── FAQ Retrieval (ChromaDB)
     │     └── Investment Retrieval (ChromaDB)
     │
     ├── SQL Layer (sql/)
     │     ├── Portfolio queries
     │     ├── Transaction queries
     │     └── Goal queries
     │
     └── Ollama LLM (rag/llm.py)            ← ONE call per request
```

Intent routing:

| Intent | RAG | SQL | Use case |
|---|---|---|---|
| `faq` | ✓ faqs | — | Policy / process questions |
| `investment` | ✓ investments | — | Generic product recommendations |
| `sql` | — | ✓ portfolio + transactions + goals | User's own account data |
| `hybrid` | ✓ investments | ✓ portfolio + goals | Personalised portfolio advice |
| `general` | — | — | Open-ended questions |

---

## Project Structure

```
investment-chatbot/
├── app.py                        # Flask app and all API routes
├── requirements.txt
├── .env                          # Ollama + MySQL config
├── README.md
├── rag/
│   ├── __init__.py
│   ├── llm.py                    # Ollama HTTP wrapper
│   ├── knowledge_base.py         # Document ingestion + ChromaDB retrieval
│   ├── user_profile.py           # UserProfile dataclass + query builder
│   └── router.py                 # Intent classifier
├── sql/
│   ├── __init__.py
│   ├── database.py               # SQLAlchemy engine, session, seed data
│   ├── models.py                 # ORM models: User, Portfolio, Transaction, Goal
│   └── queries.py                # All DB read functions
├── templates/
│   └── index.html                # Dashboard UI (Phase 3)
├── static/
│   ├── css/
│   │   └── main.css              # Dark navy financial theme (Phase 3)
│   └── js/
│       └── app.js                # Dashboard JS logic (Phase 3)
└── data/
    ├── faqs/
    │   └── sample_faqs.txt       # 12 FAQ Q&A pairs
    └── investments/
        └── products.txt          # 8 investment product entries
```

---

## Setup

### 1. Install Ollama and pull a model

```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (choose one)
ollama pull llama3    # Best quality/speed balance (~4.7 GB)
# ollama pull mistral # Lighter (~4.1 GB)
# ollama pull phi3    # Smallest/fastest (~2.3 GB)

# Keep Ollama running in a separate terminal
ollama serve
```

### 2. Install and configure MySQL

```bash
# Create the database (run once)
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS financial_advisor;"
```

### 3. Set up Python environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

### 4. Configure environment

Edit `.env` with your settings:

```env
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
FLASK_DEBUG=true

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=financial_advisor
MYSQL_USER=root
MYSQL_PASSWORD=your_password
```

### 5. Run the app

```bash
# Make sure Ollama is running first!
ollama serve   # in a separate terminal

python app.py
```

Open your browser at:

```
http://localhost:5000
```

On first run, the app will:
1. Check Ollama connectivity
2. Load, chunk, embed, and index all documents into ChromaDB
3. Create MySQL tables and seed 3 sample users with portfolio data

---

## Frontend Dashboard

Open `http://localhost:5000` after starting the server.

### Dashboard Tab

- **Portfolio Overview** — 4 summary cards with total invested, current value, gain/loss
- **Holdings Breakdown** — all positions with risk badges and gain percentages
- **Financial Goals** — animated progress bars per goal
- **Recent Transactions** — styled table with buy/sell/SIP badges

### AI Advisor Tab

Four chat modes selectable from the sidebar:

| Mode | Endpoint | What it does |
|---|---|---|
| General Chat | `POST /chat` | Auto-detects intent |
| FAQ Lookup | `POST /chat` | Routes to FAQ RAG |
| Investment Advice | `POST /profile-chat` | Profile-based product recommendations |
| Portfolio Q&A | `POST /chat` with `user_id` | SQL + RAG hybrid answers |

**Portfolio Analysis** button (gold accent) calls `POST /portfolio-analysis` — combines live MySQL data with RAG investment knowledge for deep personalised advice.

---

## API Reference

### `GET /status`

Returns Ollama, RAG, and MySQL health.

### `POST /chat`

General chat with auto intent detection.

```json
{
  "message": "How much have I invested?",
  "user_id": 1,
  "user_profile": { "age": 28, "monthly_income": 60000, "risk_appetite": "medium", "investment_goal": "wealth growth", "investment_horizon": "long", "existing_investments": [] }
}
```

Response includes `intent`: `faq | investment | sql | hybrid | general`

### `POST /profile-chat`

Personalised investment recommendations.

```json
{
  "message": "What should I invest in?",
  "profile": { "age": 30, "monthly_income": 80000, "risk_appetite": "medium", "investment_goal": "retirement", "investment_horizon": "long", "existing_investments": ["PPF"] }
}
```

### `GET /portfolio/<user_id>`

Returns portfolio summary and all holdings.

### `GET /transactions/<user_id>?limit=10`

Returns recent transactions.

### `GET /goals/<user_id>`

Returns all financial goals and progress.

### `POST /portfolio-analysis`

Hybrid endpoint — live portfolio data + RAG knowledge → Ollama advice.

```json
{ "user_id": 1, "message": "Analyze my portfolio and suggest improvements." }
```

---

## Sample Users (seeded automatically)

| ID | Name | Age | Risk | Goal |
|---|---|---|---|---|
| 1 | Arjun Sharma | 28 | Medium | Wealth Growth |
| 2 | Priya Nair | 45 | Low | Retirement |
| 3 | Rohit Verma | 32 | High | Wealth Growth |

---

## Extending the Knowledge Base

Drop `.txt` or `.pdf` files into:
- `data/faqs/` — FAQ content
- `data/investments/` — product/scheme information

Then delete `chroma_db/` and restart the app. Documents are re-indexed automatically.

---

## Switching Models

Edit `.env`:

```env
OLLAMA_MODEL=mistral   # or phi3, llama3, gemma, etc.
```

Pull the model first: `ollama pull mistral`

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Cannot reach Ollama` | Run `ollama serve` in a separate terminal |
| `model 'llama3' not found` | Run `ollama pull llama3` |
| `MySQL connection refused` | Ensure MySQL is running and `.env` credentials are correct |
| `Slow first response` | Normal — model loads into memory on first use |
| `Re-index documents` | Delete `chroma_db/` folder and restart |
