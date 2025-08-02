#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import pytz

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('perfume_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraSimpleBot:
    def __init__(self):
        # Токен напрямую
        bot_token = "8377061776:AAHSLR8D7w9gbQbSz7gyO73nb_ywYtozJlY"
        
        # Инициализация приложения
        self.application = Application.builder().token(bot_token).build()
        
        # Регистрация обработчиков
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
        
        logger.info("🤖 Ultra Simple Bot инициализирован")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"👋 Команда /start от пользователя {user.id}")
        await update.message.reply_text(f"Привет, {user.first_name}! Бот работает!")

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Простой тестовый обработчик"""
        user = update.effective_user
        logger.info(f"🧪 ТЕСТ: Получена команда /test от пользователя {user.id}")
        await update.message.reply_text("✅ Бот работает! Тест успешен!")

    async def run(self):
        """Запускает бота"""
        try:
            logger.info("🚀 Ultra Simple Bot запущен!")
            logger.info("📡 Запускаем polling...")
            await self.application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            raise

def main():
    """Главная функция"""
    try:
        bot = UltraSimpleBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()