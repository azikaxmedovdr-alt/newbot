import os
import json
import urllib.request
import urllib.error
import asyncio
import logging

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


async def ask_agent(system_prompt: str, history: list, user_message: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set!")

    logger.info(f"GROQ_API_KEY starts with: {GROQ_API_KEY[:8]}...")
    logger.info(f"Sending request to Groq, history length: {len(history)}")

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    body = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": 1024
    }).encode("utf-8")

    req = urllib.request.Request(
        GROQ_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        },
        method="POST"
    )

    def do_request():
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            logger.error(f"Groq HTTP {e.code}: {body}")
            raise

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, do_request)
    return data["choices"][0]["message"]["content"]

