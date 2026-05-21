import os
import json
import urllib.request
import urllib.error
import asyncio
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Read model from Railway variable, fallback list if not set
PRIMARY_MODEL = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-r1:free")
FALLBACK_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]


def build_request(model, messages):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 1024
    }).encode("utf-8")
    return urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://virtual-office-bot.railway.app",
            "X-Title": "Virtual Office Bot"
        },
        method="POST"
    )


def do_request(req):
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return content.strip() if content else None
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        logger.error(f"HTTP {e.code}: {err[:200]}")
        raise


async def ask_agent(system_prompt: str, history: list, user_message: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set!")

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    loop = asyncio.get_event_loop()
    all_models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]

    for model in all_models:
        logger.info(f"Trying: {model}")
        req = build_request(model, messages)
        try:
            for attempt in range(2):
                try:
                    content = await loop.run_in_executor(None, lambda r=req: do_request(r))
                    if content:
                        return content
                    if attempt == 0:
                        await asyncio.sleep(5)
                except urllib.error.HTTPError as e:
                    if e.code == 429 and attempt == 0:
                        await asyncio.sleep(10)
                    else:
                        raise
        except Exception as e:
            logger.warning(f"{model} failed: {e}, trying next...")
            continue

    raise Exception("Все модели недоступны. Попробуйте позже.")

