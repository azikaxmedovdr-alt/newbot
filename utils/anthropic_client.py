import os
import anthropic

client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


async def ask_agent(system_prompt: str, history: list, user_message: str) -> str:
    messages = history + [{"role": "user", "content": user_message}]

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    return response.content[0].text
