import os
import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ChatAction
from agents.registry import AGENTS
from utils.history import ConversationHistory
from utils.anthropic_client import ask_agent

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

history = ConversationHistory()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["👋 *Виртуальный офис запущен!*\n", "Упомяните агента, чтобы он ответил:\n"]
    for agent in AGENTS.values():
        lines.append(f"{agent['avatar']} @{agent['username']} — {agent['role']}")
    lines.append("\nПример: `@pm_agent Составь план спринта`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def agents_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🏢 *Команда виртуального офиса:*\n"]
    for agent in AGENTS.values():
        lines.append(f"{agent['avatar']} *{agent['name']}* (@{agent['username']})")
        lines.append(f"   {agent['role']}")
        lines.append(f"   _{agent['description']}_\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat_id = message.chat_id
    user = message.from_user
    text = message.text
    entities = message.entities or []

    # Find mentioned agents
    mentioned_agents = []
    for entity in entities:
        if entity.type == "mention":
            mention = text[entity.offset: entity.offset + entity.length]
            username = mention.lstrip("@").lower()
            for agent_id, agent in AGENTS.items():
                if agent["username"].lower() == username:
                    mentioned_agents.append((agent_id, agent))
                    break

    if not mentioned_agents:
        return

    # Clean text: remove all @mentions from user message
    clean_text = text
    for entity in sorted(entities, key=lambda e: e.offset, reverse=True):
        if entity.type == "mention":
            clean_text = clean_text[: entity.offset] + clean_text[entity.offset + entity.length :]
    clean_text = clean_text.strip()

    if not clean_text:
        clean_text = "Привет! Представься и расскажи, чем можешь помочь команде."

    # Reply from each mentioned agent
    for agent_id, agent in mentioned_agents:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Build context: who else is in the team
        team_context = "Ты работаешь в виртуальном офисе вместе с:\n"
        for other_id, other in AGENTS.items():
            if other_id != agent_id:
                team_context += f"- {other['name']} ({other['role']}) @{other['username']}\n"

        conv_history = history.get(chat_id, agent_id)

        try:
            reply = await ask_agent(
                system_prompt=agent["system"] + "\n\n" + team_context,
                history=conv_history,
                user_message=f"{user.first_name}: {clean_text}",
            )
            history.add(chat_id, agent_id, user_message=f"{user.first_name}: {clean_text}", assistant_message=reply)
            await message.reply_text(f"{agent['avatar']} *{agent['name']}*\n{reply}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error from agent {agent_id}: {e}")
            await message.reply_text(f"{agent['avatar']} {agent['name']} сейчас недоступен. Попробуй позже.")


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    history.clear(chat_id)
    await update.message.reply_text("🗑️ История разговоров очищена.")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("agents", agents_list))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
