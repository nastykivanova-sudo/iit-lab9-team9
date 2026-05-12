import os
import time

from prometheus_client import (
    start_http_server,
    Counter,
    Gauge,
    Summary
)

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)


TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    "8381915690:AAFR-ZKiK9UX2nfvuGGfOUTzxhyMdrg8q14"
)

METRICS_PORT = 9091

bot_messages_total = Counter(
    "telegram_bot_messages_total",
    "Total number of text messages received by Telegram bot"
)

bot_commands_total = Counter(
    "telegram_bot_commands_total",
    "Total number of commands received by Telegram bot",
    ["command"]
)

bot_unknown_commands_total = Counter(
    "telegram_bot_unknown_commands_total",
    "Total number of unknown commands received by Telegram bot"
)

bot_last_message_length = Gauge(
    "telegram_bot_last_message_length",
    "Length of the last received text message"
)

bot_users_total = Gauge(
    "telegram_bot_users_total",
    "Approximate number of unique users who interacted with the bot"
)

bot_uptime_seconds = Gauge(
    "telegram_bot_uptime_seconds",
    "Telegram bot uptime in seconds"
)

bot_request_processing_seconds = Summary(
    "telegram_bot_request_processing_seconds",
    "Time spent processing Telegram bot request"
)


start_time = time.time()
unique_users = set()


def start_metrics_server():
    start_http_server(METRICS_PORT)
    print(f"Prometheus metrics server started on http://127.0.0.1:{METRICS_PORT}/metrics")


def update_user_metrics(user):
    if user:
        unique_users.add(user.id)
        bot_users_total.set(len(unique_users))


def update_uptime_metric():
    uptime = time.time() - start_time
    bot_uptime_seconds.set(uptime)


@bot_request_processing_seconds.time()
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    update_user_metrics(user)
    update_uptime_metric()

    bot_commands_total.labels(command="start").inc()

    await update.message.reply_text(
        "Привіт! Я бот для лабораторної 9.\n"
        "Я збираю метрики для Prometheus та Grafana.\n\n"
        "Метрики доступні за адресою:\n"
        "http://127.0.0.1:9091/metrics"
    )


@bot_request_processing_seconds.time()
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    update_user_metrics(user)
    update_uptime_metric()

    bot_commands_total.labels(command="help").inc()

    await update.message.reply_text(
        "Доступні команди:\n"
        "/start — почати роботу\n"
        "/help — допомога\n\n"
        "Також можна написати будь-який текст, і бот оновить Prometheus-метрики."
    )


@bot_request_processing_seconds.time()
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    update_user_metrics(user)
    update_uptime_metric()

    bot_messages_total.inc()
    bot_last_message_length.set(len(text))

    await update.message.reply_text(
        "Повідомлення отримано.\n"
        "Метрики Prometheus оновлено."
    )


@bot_request_processing_seconds.time()
async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    update_user_metrics(user)
    update_uptime_metric()

    bot_unknown_commands_total.inc()
    bot_commands_total.labels(command="unknown").inc()

    await update.message.reply_text(
        "Невідома команда. Використай /help."
    )

def main():
    start_metrics_server()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    print("Telegram bot started...")

    app.run_polling()


if __name__ == "__main__":
    main()
