INVESTMENT_KEYWORDS = [
    "invest", "investment", "returns", "sip", "mutual fund", "stocks", "equity",
    "debt", "fd", "fixed deposit", "wealth", "savings", "nps", "elss", "ppf",
    "retire", "retirement", "goal", "tax saving", "hybrid", "lump sum", "dividend",
    "nav", "fund", "scheme", "maturity", "interest rate", "asset", "capital",
    "grow money", "where to invest", "suggest", "recommend", "should i invest",
]

FAQ_KEYWORDS = [
    "how", "what", "when", "why", "can i", "do i", "is it", "are there",
    "policy", "terms", "process", "eligibility", "document", "account",
    "kyc", "withdraw", "redemption", "login", "register", "support",
    "contact", "charges", "fees", "procedure", "open account", "close account",
]

# SQL intent: queries about the user's own structured data
SQL_KEYWORDS = [
    "my portfolio", "my investments", "my transactions", "my goals",
    "how much have i invested", "how much did i invest", "total invested",
    "total investment", "current value", "portfolio value", "my holdings",
    "recent transactions", "transaction history", "show my", "my balance",
    "how much i have", "portfolio summary", "my progress", "goal progress",
]

# Hybrid intent: combines live portfolio data (SQL) with financial knowledge (RAG)
HYBRID_KEYWORDS = [
    "analyze my portfolio", "portfolio analysis", "review my portfolio",
    "is my portfolio", "assess my portfolio", "portfolio suitable",
    "portfolio diversified", "diversification", "rebalance", "should i rebalance",
    "portfolio performance", "improve my portfolio", "portfolio advice",
    "am i on track", "will i reach my goal", "personalized advice",
    "based on my portfolio", "given my investments",
]


def detect_intent(user_message: str) -> str:
    """
    Keyword-based intent classifier. No LLM call.
    Returns one of: 'hybrid' | 'sql' | 'investment' | 'faq' | 'general'
    """
    msg = user_message.lower()

    for kw in HYBRID_KEYWORDS:
        if kw in msg:
            return "hybrid"

    for kw in SQL_KEYWORDS:
        if kw in msg:
            return "sql"

    for kw in INVESTMENT_KEYWORDS:
        if kw in msg:
            return "investment"

    for kw in FAQ_KEYWORDS:
        if kw in msg:
            return "faq"

    if "?" in user_message:
        return "faq"

    return "general"
