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
