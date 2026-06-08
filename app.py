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
