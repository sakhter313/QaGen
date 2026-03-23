"""
utils/llm.py
------------
Groq API client using open-source models — all free on Groq's free tier.
Compatible with groq>=0.9.0 (the SDK version available on Streamlit Cloud).

Free tier limits: ~14,400 req/day · 6,000 tokens/min · 500K tokens/day
Sign up free (no credit card): https://console.groq.com
"""

from groq import Groq

# ---------------------------------------------------------------------------
# Model registry — all free on Groq
# ---------------------------------------------------------------------------
AVAILABLE_MODELS = {
    "llama-3.3-70b-versatile": {
        "label":    "LLaMA 3.3 70B  ★ Best Quality",
        "size":     "70B",
        "type":     "Meta LLaMA",
        "speed":    "Fast",
        "context":  "128K tokens",
        "best_for": "Complex, multi-page QA docs",
    },
    "llama-3.1-8b-instant": {
        "label":    "LLaMA 3.1 8B  ⚡ Fastest",
        "size":     "8B",
        "type":     "Meta LLaMA",
        "speed":    "Instant",
        "context":  "128K tokens",
        "best_for": "Quick drafts, simple pages",
    },
    "mixtral-8x7b-32768": {
        "label":    "Mixtral 8x7B  ⚖ Balanced",
        "size":     "8×7B MoE",
        "type":     "Mistral AI",
        "speed":    "Fast",
        "context":  "32K tokens",
        "best_for": "Balanced speed and quality",
    },
    "gemma2-9b-it": {
        "label":    "Gemma 2 9B  🪶 Lightweight",
        "size":     "9B",
        "type":     "Google",
        "speed":    "Very Fast",
        "context":  "8K tokens",
        "best_for": "Short pages, quick tests",
    },
}

_SYSTEM_PROMPT = """You are a Senior QA Engineer with 10+ years of experience.
Your ONLY task is to produce structured QA documentation from website UI content.

RULES — zero tolerance:
1. Output ONLY structured markdown. No preamble, no commentary.
2. Functional requirements MUST start with: "System shall"
3. User stories MUST follow: "As a [role], I want [action] so that [benefit]"
4. Acceptance criteria MUST use strict Given / When / Then format
5. Edge cases MUST start with: "System should handle"
6. NEVER invent UI elements not in the provided content
7. NEVER write questions — only testable statements
8. Use EXACT button/input names from the scraped content"""


def generate_qa_requirements(prompt: str, api_key: str, model: str) -> dict:
    """
    Call Groq API. Returns dict: {success, content, tokens, error}.
    Compatible with groq SDK >= 0.9.0.
    """
    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
            top_p=0.9,
        )

        # groq SDK >= 0.9 returns a ChatCompletion object
        content = response.choices[0].message.content
        tokens  = response.usage.total_tokens if response.usage else 0

        return {"success": True, "content": content, "tokens": tokens, "error": None}

    except Exception as e:
        msg = str(e)
        if "invalid_api_key" in msg.lower() or "authentication" in msg.lower() or "401" in msg:
            msg = "Invalid API key. Check at console.groq.com → API Keys."
        elif "rate_limit" in msg.lower() or "429" in msg:
            msg = "Rate limit hit. Wait ~60 seconds and try again (free tier limit)."
        elif "model_not_found" in msg.lower() or "404" in msg:
            msg = f"Model '{model}' unavailable. Select a different model."
        elif "connection" in msg.lower():
            msg = "Connection error. Streamlit Cloud needs outbound HTTPS — check network."
        return {"success": False, "content": "", "tokens": 0, "error": msg}
