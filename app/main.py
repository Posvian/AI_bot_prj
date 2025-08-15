import os

from dotenv import load_dotenv
from app.bot import TelegramBot
from app.core import QAService

load_dotenv()
my_token = os.getenv("TELEGRAM_BOT_TOKEN")

qa_service = QAService()

bot = TelegramBot(
    token=my_token,
    qa_service=qa_service,
)

bot.run()
