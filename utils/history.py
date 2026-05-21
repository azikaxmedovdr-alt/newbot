from collections import defaultdict

MAX_HISTORY = 20  # messages per agent per chat


class ConversationHistory:
    def __init__(self):
        # {chat_id: {agent_id: [{"role": ..., "content": ...}]}}
        self._store = defaultdict(lambda: defaultdict(list))

    def get(self, chat_id: int, agent_id: str) -> list:
        return list(self._store[chat_id][agent_id])

    def add(self, chat_id: int, agent_id: str, user_message: str, assistant_message: str):
        history = self._store[chat_id][agent_id]
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_message})
        # Keep only last MAX_HISTORY messages
        if len(history) > MAX_HISTORY:
            self._store[chat_id][agent_id] = history[-MAX_HISTORY:]

    def clear(self, chat_id: int):
        self._store[chat_id] = defaultdict(list)
