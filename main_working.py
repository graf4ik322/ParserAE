#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import pytz
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import Config

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

class PerfumeBotWorking:
    def __init__(self):
        self.config = Config()
        
        # Инициализация приложения с правильной timezone
        self.application = Application.builder().token(self.config.bot_token).timezone(pytz.UTC).build()
        
        # Регистрация обработчиков
        self._register_handlers()
        
        logger.info("🤖 Perfume Bot Working инициализирован")

    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
        
        logger.info("✅ Обработчики зарегистрированы")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"👋 Команда /start от пользователя {user.id} ({user.first_name})")
        
        welcome_text = f"""
🌸 Добро пожаловать в парфюмерного консультанта, {user.first_name}!

Я помогу вам:
• 🔍 Найти идеальный парфюм
• 📊 Узнать о составе и нотах
• 💡 Получить персональные рекомендации
• 🎯 Пройти тест на подбор аромата

Напишите мне любое сообщение или используйте команды:
/help - помощь
/test - проверить работу бота
        """
        
        keyboard = [
            [InlineKeyboardButton("🔍 Поиск парфюма", callback_data="search")],
            [InlineKeyboardButton("🎯 Тест на подбор", callback_data="quiz")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        
        await update.message.reply_text(
            welcome_text.strip(),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Простой тестовый обработчик"""
        user = update.effective_user
        logger.info(f"🧪 ТЕСТ: Получена команда /test от пользователя {user.id}")
        await update.message.reply_text("✅ Бот работает! Тест успешен!")
        logger.info("🧪 ТЕСТ: Ответ отправлен")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
🆘 Помощь по боту:

/start - Начать работу с ботом
/test - Проверить работу бота
/help - Показать эту справку

Просто напишите мне сообщение, и я помогу вам с выбором парфюма!
        """
        await update.message.reply_text(help_text.strip())

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        text = update.message.text
        logger.info(f"💬 Сообщение от {user.id}: {text}")
        
        # Простой ответ
        response = f"Привет! Вы написали: '{text}'\n\nИспользуйте /start для начала работы или /help для справки."
        await update.message.reply_text(response)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"❌ Ошибка в обработчике: {context.error}")
        if update and hasattr(update, 'message') and update.message:
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

    async def run(self):
        """Запускает бота"""
        try:
            logger.info("🚀 Perfume Bot Working запущен и готов к работе!")
            
            # Запускаем polling
            logger.info("📡 Запускаем polling для получения обновлений...")
            await self.application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            raise

def main():
    """Главная функция"""
    try:
        bot = PerfumeBotWorking()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()