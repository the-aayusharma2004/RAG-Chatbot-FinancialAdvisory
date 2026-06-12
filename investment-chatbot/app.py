import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from rag.knowledge_base import retrieve, ingest_documents
from rag.user_profile import UserProfile, profile_to_query
from rag.router import detect_intent
from rag import llm
from sql.database import init_db, test_connection
from sql import queries

load_dotenv()

app = Flask(__name__)

# ── Startup: Ollama connection check ─────────────────────────────────────────
ollama_status = llm.health_check()
print(f"Ollama status: {ollama_status}")

# ── Startup: RAG knowledge base ───────────────────────────────────────────────
rag_status = "not initialized"
try:
    ingest_documents()
    rag_status = "ready"
except Exception as e:
    print(f"RAG initialization failed: {e}")
    rag_status = f"error: {str(e)}"

# ── Startup: MySQL / SQLAlchemy ───────────────────────────────────────────────
db_status = test_connection()
try:
    init_db()
    print(f"MySQL status: {db_status}")
except Exception as e:
    print(f"MySQL init failed: {e}")
    db_status["init_error"] = str(e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Prompt-building helpers (pure Python, no LLM calls)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_faq_prompt(user_message: str) -> str:
    chunks = retrieve(user_message, collection="faqs", top_k=3)
    context = "\n\n".join(chunks) if chunks else "No relevant FAQ found."
    return (
        "You are a helpful financial services assistant. "
        "Answer the user's question using ONLY the following FAQ context. "
        "If the answer is not in the context, say: 'I don't have information on that — "
        "please contact our support team.'\n\n"
        f"FAQ Context:\n{context}"
    )


def _build_investment_prompt(user_message: str, user_profile_data: dict | None) -> str:
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

    chunks = retrieve(retrieval_query, collection="investments", top_k=4)
    context = "\n\n".join(chunks) if chunks else "No relevant products found."
    return (
        "You are a knowledgeable investment advisor. "
        "Suggest suitable investment options based on the user profile and product information below. "
        "Mention product names, expected returns, risk levels, and suitability reasoning. "
        "Always note that past returns do not guarantee future performance.\n\n"
        f"User Profile: {profile_summary}\n\n"
        f"Available Investment Products:\n{context}"
    )


def _build_sql_prompt(user_id: int, user_message: str) -> str:
    """Build a prompt that injects structured portfolio/transaction/goal data from MySQL."""
    portfolio_ctx = queries.portfolio_to_context_text(user_id)
    tx_data = queries.get_transactions(user_id, limit=5)
    tx_lines = [
        f"  {t['date'][:10]}  {t['type'].upper():6}  Rs.{t['amount']:>10,.0f}  {t['product_name']}"
        for t in tx_data
    ]
    tx_ctx = "\n".join(tx_lines) if tx_lines else "No recent transactions."
    goals_ctx = queries.goals_to_context_text(user_id)
    user_profile = queries.get_user_profile(user_id)
    profile_line = (
        f"Name: {user_profile['name']}, Age: {user_profile['age']}, "
        f"Income: Rs.{user_profile['monthly_income']:,.0f}/month, "
        f"Risk: {user_profile['risk_appetite']}, Goal: {user_profile['investment_goal']}"
        if user_profile else "User profile not found."
    )
    return (
        "You are a personal financial assistant with access to the user's account data. "
        "Answer the user's question using only the data provided below. "
        "Be precise with numbers and present them clearly.\n\n"
        f"User Profile:\n{profile_line}\n\n"
        f"Portfolio Summary:\n{portfolio_ctx}\n\n"
        f"Recent Transactions (last 5):\n{tx_ctx}\n\n"
        f"Financial Goals:\n{goals_ctx}"
    )


def _build_hybrid_prompt(user_id: int, user_message: str) -> str:
    """Combine SQL portfolio context with RAG investment knowledge for personalised advice."""
    portfolio_ctx = queries.portfolio_to_context_text(user_id)
    goals_ctx = queries.goals_to_context_text(user_id)
    user_profile = queries.get_user_profile(user_id)
    profile_line = (
        f"Name: {user_profile['name']}, Age: {user_profile['age']}, "
        f"Risk Appetite: {user_profile['risk_appetite']}, "
        f"Investment Goal: {user_profile['investment_goal']}, "
        f"Horizon: {user_profile['investment_horizon']}"
        if user_profile else "User profile not found."
    )
    rag_chunks = retrieve(user_message, collection="investments", top_k=3)
    rag_ctx = "\n\n".join(rag_chunks) if rag_chunks else "No relevant product knowledge found."
    return (
        "You are a certified financial advisor. "
        "Analyse the user's portfolio and goals using their actual account data, "
        "then apply the general financial knowledge below to give personalised, actionable advice. "
        "Be specific about their current holdings and suggest concrete next steps. "
        "End with a brief risk disclaimer.\n\n"
        f"User Profile:\n{profile_line}\n\n"
        f"Current Portfolio:\n{portfolio_ctx}\n\n"
        f"Financial Goals:\n{goals_ctx}\n\n"
        f"Financial Knowledge (for context):\n{rag_ctx}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "ollama_status": ollama_status,
        "rag_status": rag_status,
        "db_status": db_status,
        "model": ollama_status.get("model"),
    })


@app.route("/chat", methods=["POST"])
def chat():
    """
    General chat endpoint. Detects intent automatically.
    For sql/hybrid intents, requires user_id in the request body.

    Request body:
    {
        "message": "How much have I invested?",
        "user_id": 1,           // required for sql / hybrid intents
        "user_profile": { ... } // optional, used only for investment intent
    }
    """
    try:
        data = request.json or {}
        user_message = data.get("message", "").strip()
        user_profile_data = data.get("user_profile", None)
        user_id = data.get("user_id", None)

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        intent = detect_intent(user_message)

        if intent == "faq":
            system_prompt = _build_faq_prompt(user_message)

        elif intent == "investment":
            system_prompt = _build_investment_prompt(user_message, user_profile_data)

        elif intent == "sql":
            if not user_id:
                return jsonify({"error": "user_id is required for portfolio queries."}), 400
            system_prompt = _build_sql_prompt(int(user_id), user_message)

        elif intent == "hybrid":
            if not user_id:
                return jsonify({"error": "user_id is required for portfolio analysis."}), 400
            system_prompt = _build_hybrid_prompt(int(user_id), user_message)

        else:
            system_prompt = (
                "You are a helpful financial services chatbot. "
                "Answer the user's question in a clear and professional manner."
            )

        response = llm.chat(system_prompt=system_prompt, user_message=user_message)
        return jsonify({"response": response, "intent": intent})

    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@app.route("/profile-chat", methods=["POST"])
def profile_chat():
    """
    Dedicated endpoint for personalised investment recommendations.

    Request body:
    {
        "message": "What should I invest in?",
        "profile": {
            "age": 30, "monthly_income": 80000, "risk_appetite": "medium",
            "investment_goal": "retirement", "investment_horizon": "long",
            "existing_investments": ["PPF"]
        }
    }
    """
    try:
        data = request.json or {}
        user_message = data.get("message", "What investment options suit my profile?").strip()
        profile_data = data.get("profile", {})

        if not profile_data:
            return jsonify({"error": "Profile data is required. Use /chat for general queries."}), 400

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
            return jsonify({"error": f"Invalid profile fields: {str(e)}"}), 400

        chunks = retrieve(retrieval_query, collection="investments", top_k=5)
        context = "\n\n".join(chunks) if chunks else "No relevant products found."
        system_prompt = (
            "You are a certified financial advisor providing personalized investment recommendations. "
            "Based on the user profile and products below, recommend 2-4 suitable investment options. "
            "For each: state product name, why it fits their profile, expected returns, risk level, "
            "and minimum investment. Use bullet points. End with a short market risk disclaimer.\n\n"
            f"User Profile:\n{profile_summary}\n\n"
            f"Available Investment Products:\n{context}"
        )

        response = llm.chat(system_prompt=system_prompt, user_message=user_message)
        return jsonify({
            "response": response,
            "profile_used": profile_summary,
            "intent": "investment",
        })

    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@app.route("/portfolio/<int:user_id>", methods=["GET"])
def get_portfolio(user_id: int):
    """
    Returns portfolio summary and holdings for a user.
    GET /portfolio/1
    """
    try:
        summary = queries.get_total_investment(user_id)
        holdings = queries.get_user_portfolio(user_id)
        if not holdings:
            return jsonify({"error": f"No portfolio found for user_id {user_id}"}), 404
        return jsonify({
            "user_id": user_id,
            "portfolio_value": summary["total_current_value"],
            "total_invested": summary["total_invested"],
            "total_gain_loss": summary["total_gain_loss"],
            "overall_gain_pct": summary["overall_gain_pct"],
            "holdings": holdings,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/transactions/<int:user_id>", methods=["GET"])
def get_transactions(user_id: int):
    """
    Returns recent transactions for a user.
    GET /transactions/1?limit=20   (default limit=10)
    """
    try:
        limit = int(request.args.get("limit", 10))
        txs = queries.get_transactions(user_id, limit=limit)
        return jsonify({"user_id": user_id, "transactions": txs, "count": len(txs)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/goals/<int:user_id>", methods=["GET"])
def get_goals(user_id: int):
    """
    Returns all financial goals and progress for a user.
    GET /goals/1
    """
    try:
        goals = queries.get_goals(user_id)
        return jsonify({"user_id": user_id, "goals": goals})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/portfolio-analysis", methods=["POST"])
def portfolio_analysis():
    """
    Hybrid endpoint: SQL portfolio data + RAG financial knowledge → Ollama advice.

    Request body:
    {
        "user_id": 1,
        "message": "Analyse my portfolio and suggest improvements."  // optional
    }
    """
    try:
        data = request.json or {}
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        user_id = int(user_id)
        user_message = data.get("message", "Analyse my portfolio and suggest improvements.")
        system_prompt = _build_hybrid_prompt(user_id, user_message)
        response = llm.chat(system_prompt=system_prompt, user_message=user_message)

        return jsonify({
            "response": response,
            "user_id": user_id,
            "intent": "hybrid",
        })

    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        port=5000,
    )
