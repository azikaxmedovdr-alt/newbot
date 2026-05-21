# 🏢 Виртуальный офис — Telegram Bot

Групповой чат с 7 AI-агентами. Каждый агент отвечает когда его упоминают через @.

## Агенты

| Username | Имя | Роль |
|---|---|---|
| @pm_agent | Алексей | Проект-менеджер |
| @tech_agent | Дмитрий | Технический архитектор |
| @qa_agent | Ольга | QA-инженер |
| @frontend_agent | Марина | Фронтенд-разработчик |
| @backend_agent | Сергей | Бэкенд-разработчик |
| @designer_agent | Анна | UI/UX Дизайнер |
| @marketing_agent | Екатерина | Маркетолог |

## Команды бота

- `/start` — приветствие и список агентов
- `/agents` — подробная информация об агентах
- `/clear` — очистить историю разговоров

## Как использовать

В групповом чате упомяни агента:
```
@pm_agent составь план спринта на 2 недели
@backend_agent спроектируй REST API для авторизации
@designer_agent предложи цветовую палитру для финтех-приложения
```

Можно упомянуть сразу нескольких:
```
@pm_agent @tech_agent обсудите архитектуру нового сервиса
```

---

## Шаг 1 — Создай бота в Telegram

1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Напиши `/newbot`
3. Придумай имя и username для бота
4. Скопируй токен — это `TELEGRAM_BOT_TOKEN`
5. Напиши `/mybots` → выбери бота → *Bot Settings* → *Group Privacy* → **выключи** (чтобы бот видел все сообщения в группе)

## Шаг 2 — Получи Anthropic API Key

1. Зайди на [console.anthropic.com](https://console.anthropic.com)
2. *API Keys* → *Create Key*
3. Скопируй ключ — это `ANTHROPIC_API_KEY`

## Шаг 3 — Деплой на Railway (бесплатно)

1. Залей код на GitHub (создай новый репозиторий, загрузи все файлы)
2. Зайди на [railway.app](https://railway.app) → *New Project* → *Deploy from GitHub*
3. Выбери репозиторий
4. Перейди в *Variables* и добавь:
   ```
   TELEGRAM_BOT_TOKEN = твой_токен
   ANTHROPIC_API_KEY = твой_ключ
   ```
5. Railway автоматически запустит бота

## Шаг 4 — Добавь бота в группу

1. Создай группу в Telegram (или используй существующую)
2. Добавь бота в группу
3. Напиши `/start` — бот поздоровается
4. Начни общаться с агентами через @упоминания!

---

## Локальный запуск (для разработки)

```bash
# Клонируй репозиторий
git clone <your-repo>
cd virtual-office

# Установи зависимости
pip install -r requirements.txt

# Создай .env файл
cp .env.example .env
# Заполни TELEGRAM_BOT_TOKEN и ANTHROPIC_API_KEY

# Запусти
python bot.py
```

## Деплой на Render (альтернатива)

1. Зайди на [render.com](https://render.com) → *New* → *Web Service*
2. Подключи GitHub репозиторий
3. Настройки:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
4. Добавь переменные окружения в *Environment*
5. Deploy!
