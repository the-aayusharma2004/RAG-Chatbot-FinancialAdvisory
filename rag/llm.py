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
