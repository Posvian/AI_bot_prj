from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from .core import QAService


class TelegramBot:
    def __init__(self, token: str, qa_service: QAService):
        self.qa = qa_service
        self.app = Application.builder().token(token).build()

        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Привет! Я бот EORA. Спроси меня о наших кейсах, например:\n"
            "• Что вы делали для ритейлеров?\n"
            "• Какие проекты у вас для банков?"
        )

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        response = self.qa.ask_question_api(update.message.text)

        response_dict = response.response.model_dump()

        answer = response_dict["answer"]
        if response_dict["sources"]:
            answer += "\n\nИсточники:\n" + "\n".join(response_dict["sources"])

        await update.message.reply_text(answer)

    def run(self):
        self.app.run_polling()
