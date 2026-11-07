import os

from openai import OpenAI

MODEL = "asi1"
_client = None


def llm_available() -> bool:
    """True when the ASI:One credential is present in the environment."""
    return bool(os.environ.get("ASI1_API_KEY")) and bool(os.environ.get("ASI1_BASE_URL"))


def _get_client():
    """Build (once) an OpenAI-compatible client for ASI:One, or None if unconfigured."""
    global _client
    if _client is None:
        api_key = os.environ.get("ASI1_API_KEY")
        base_url = os.environ.get("ASI1_BASE_URL")
        if not api_key or not base_url:
            return None
        _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client


def ask_asi1(messages):
    """Call ASI:One with a prepared message list; returns reply text or None."""
    client = _get_client()
    if client is None:
        return None
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=2400,  # room for a complete brief; prompt still limits length
    )
    return completion.choices[0].message.content or ""
