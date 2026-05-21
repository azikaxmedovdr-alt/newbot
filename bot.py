import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
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

# Store selected agent per chat: {chat_id: agent_id}
selected_agent = {}


def make_agent_keyboard(current=None):
    buttons = []
    row = []
    for agent_id, agent in AGENTS.items():
        mark = " ✅" if agent_id == current else ""
        row.append(InlineKeyboardButton(
            f"{agent['avatar']} {agent['name']}{mark}",
            callback_data=f"select:{agent_id}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Виртуальный офис запущен!</b>\n\n"
        "Выберите агента кнопкой ниже и просто пишите сообщения — "
        "не нужно упоминать @ каждый раз.\n\n"
        "Или упомяните агента напрямую: <code>@pm_agent привет</code>"
    )
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=make_agent_keyboard()
    )


async def agents_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    current = selected_agent.get(chat_id)
    text = "<b>Выберите агента:</b>"
    if current and current in AGENTS:
        a = AGENTS[current]
        text += f"\n\nСейчас активен: {a['avatar']} <b>{a['name']}</b> ({a['role']})"
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=make_agent_keyboard(current)
    )


async def select_agent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    agent_id = query.data.split(":")[1]
    chat_id = query.message.chat_id

    if agent_id not in AGENTS:
        return

    selected_agent[chat_id] = agent_id
    agent = AGENTS[agent_id]

    await query.edit_message_text(
        f"{agent['avatar']} <b>{agent['name']}</b> выбран!\n"
        f"<i>{agent['role']} — {agent['description']}</i>\n\n"
        f"Просто напишите сообщение — отвечу без @ упоминания.",
        parse_mode="HTML",
        reply_markup=make_agent_keyboard(agent_id)
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat_id = message.chat_id
    user = message.from_user
    text = message.text
    entities = message.entities or []

    # Check for @mentions first
    mentioned_agents = []
    for entity in entities:
        if entity.type == "mention":
            mention = text[entity.offset: entity.offset + entity.length]
            username = mention.lstrip("@").lower()
            for agent_id, agent in AGENTS.items():
                if agent["username"].lower() == username:
                    mentioned_agents.append((agent_id, agent))
                    break

    # If no mention — use selected agent
    if not mentioned_agents:
        current = selected_agent.get(chat_id)
        if current and current in AGENTS:
            mentioned_agents = [(current, AGENTS[current])]
        else:
            # No agent selected — show keyboard
            await message.reply_text(
                "Выберите агента с которым хотите общаться:",
                reply_markup=make_agent_keyboard()
            )
            return

    # Clean @mentions from text
    clean_text = text
    for entity in sorted(entities, key=lambda e: e.offset, reverse=True):
        if entity.type == "mention":
            clean_text = clean_text[: entity.offset] + clean_text[entity.offset + entity.length:]
    clean_text = clean_text.strip()

    if not clean_text:
        clean_text = "Привет! Представься и расскажи, чем можешь помочь."

    for agent_id, agent in mentioned_agents:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

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
            safe_reply = reply.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # Show agent selector after reply
            current = selected_agent.get(chat_id)
            await message.reply_text(
                f"{agent['avatar']} <b>{agent['name']}</b>\n{safe_reply}",
                parse_mode="HTML",
                reply_markup=make_agent_keyboard(current)
            )
        except Exception as e:
            logger.error(f"Error from agent {agent_id}: {e}")
            await message.reply_text(
                f"{agent['avatar']} {agent['name']} сейчас недоступен. Попробуй позже.",
                reply_markup=make_agent_keyboard(selected_agent.get(chat_id))
            )


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    history.clear(chat_id)
    selected_agent.pop(chat_id, None)
    await update.message.reply_text(
        "История очищена, агент сброшен.",
        reply_markup=make_agent_keyboard()
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    app = (
        Application.builder()
        .token(token)
        .drop_pending_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("agents", agents_list))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CallbackQueryHandler(select_agent_callback, pattern="^select:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

