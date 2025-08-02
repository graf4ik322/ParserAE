#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import signal
import sys
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import Config
from database.manager import DatabaseManager
from ai.processor import AIProcessor
from quiz.quiz_system import QuizSystem
from parsers.auto_parser import AutoParser

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

class PerfumeBot:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager(self.config.database_path)
        self.ai = AIProcessor(self.config.openrouter_api_key, self.config.openrouter_model)
        self.quiz = QuizSystem(self.db, self.ai)
        self.auto_parser = AutoParser(self.db)
        
        # Инициализация приложения
        self.application = Application.builder().token(self.config.bot_token).build()
        
        # Регистрация обработчиков
        self._register_handlers()
        
        logger.info("🤖 Perfume Bot инициализирован")

    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("parse", self.parse_command))
        
        # Callback-кнопки
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Получаем или создаем пользователя
        user_data = self.db.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Сбрасываем сессию
        self.db.reset_user_session(user.id)
        
        # Показываем главное меню
        await self.show_main_menu(update, context)
        
        logger.info(f"👤 Пользователь {user.id} запустил бота")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
🌸 **Парфюмерный Консультант-Бот**

**Основные функции:**
🎯 **Консультация по парфюмам** - задавайте любые вопросы о ароматах
📝 **Персональный квиз** - определим ваши предпочтения
🔍 **Информация об ароматах** - подробности о конкретных парфюмах
🛒 **Прямые ссылки на покупку** - удобный переход в магазин

**Команды:**
/start - Главное меню
/help - Эта справка

**Как использовать:**
1. Выберите нужную опцию в главном меню
2. Следуйте инструкциям бота
3. Задавайте вопросы в свободной форме

Бот работает с полным каталогом из 1200+ ароматов! 🎉
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats (только для админа)"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав для просмотра статистики")
            return
        
        stats = self.db.get_admin_statistics()
        
        stats_text = f"""
📊 **Статистика бота:**

👥 **Пользователи:**
• Всего пользователей: {stats['total_users']}
• Активных сегодня: {stats['active_users_today']}

🌸 **Каталог:**
• Всего парфюмов: {stats['total_perfumes']}

📈 **Активность:**
• Вопросов о парфюмах: {stats['total_questions']}
• Квизов пройдено: {stats['total_quizzes']}
• Токенов API сегодня: {stats['api_usage_today']}

🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}
        """
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def parse_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /parse (только для админа)"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав для запуска парсера")
            return
        
        await update.message.reply_text("🔄 Запускаю принудительное обновление каталога...")
        
        try:
            result = await self.auto_parser.force_parse_catalog()
            if result:
                await update.message.reply_text("✅ Каталог успешно обновлен!")
            else:
                await update.message.reply_text("⚠️ Обновление не требуется - каталог актуален")
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {e}")
            await update.message.reply_text(f"❌ Ошибка при обновлении каталога: {e}")

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает главное меню"""
        keyboard = [
            [InlineKeyboardButton("🎯 Задать вопрос о парфюмах", callback_data="perfume_question")],
            [InlineKeyboardButton("📝 Пройти квиз-рекомендации", callback_data="start_quiz")],
            [InlineKeyboardButton("🔍 Информация об аромате", callback_data="fragrance_info")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🌸 **Добро пожаловать в Парфюмерного Консультанта!**

Я помогу вам найти идеальный аромат из каталога 1200+ парфюмов.

**Выберите, что вас интересует:**
        """
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Обновляем состояние пользователя
        user_id = update.effective_user.id
        self.db.update_session_state(user_id, "MAIN_MENU")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на inline-кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if query.data == "perfume_question":
            await self.start_perfume_question(update, context)
        elif query.data == "start_quiz":
            await self.quiz.start_quiz(update, context)
        elif query.data == "fragrance_info":
            await self.start_fragrance_info(update, context)
        elif query.data == "help":
            await self.help_command(update, context)
        elif query.data == "back_to_menu":
            await self.show_main_menu(update, context)
        elif query.data.startswith("quiz_"):
            await self.quiz.handle_quiz_callback(update, context)

    async def start_perfume_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает режим вопросов о парфюмах"""
        user_id = update.effective_user.id
        
        # Проверяем кулдаун
        if self.ai.is_api_cooldown_active(user_id):
            await update.callback_query.edit_message_text(
                "⏱️ Пожалуйста, подождите 30 секунд перед следующим вопросом",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]])
            )
            return
        
        question_text = """
🎯 **Режим консультации по парфюмам**

Задайте любой вопрос о парфюмах:
• "Посоветуйте аромат для офиса"
• "Что подходит для свидания?"
• "Ищу что-то похожее на Chanel №5"
• "Парфюм до 3000 рублей для мужчины"

Напишите ваш вопрос, и я подберу идеальные варианты из нашего каталога!
        """
        
        await update.callback_query.edit_message_text(
            text=question_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]),
            parse_mode='Markdown'
        )
        
        self.db.update_session_state(user_id, "PERFUME_QUESTION")

    async def start_fragrance_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает режим информации об аромате"""
        user_id = update.effective_user.id
        
        info_text = """
🔍 **Информация об аромате**

Введите название парфюма, бренд или артикул:
• "Tom Ford Black Orchid"
• "Chanel"
• "TF001"

Я найду всю доступную информацию об аромате из нашего каталога!
        """
        
        await update.callback_query.edit_message_text(
            text=info_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]),
            parse_mode='Markdown'
        )
        
        self.db.update_session_state(user_id, "FRAGRANCE_INFO")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Получаем текущую сессию
        session = self.db.get_user_session(user_id)
        
        if not session or not session.get('current_state'):
            # Если нет активной сессии, показываем главное меню
            await self.show_main_menu(update, context)
            return
        
        current_state = session['current_state']
        
        if current_state == "PERFUME_QUESTION":
            await self.handle_perfume_question(update, context, message_text)
        elif current_state == "QUIZ_IN_PROGRESS":
            await self.quiz.handle_quiz_answer(update, context, message_text)
        elif current_state == "FRAGRANCE_INFO":
            await self.handle_fragrance_info(update, context, message_text)
        else:
            # Неизвестное состояние - возвращаем в главное меню
            await self.show_main_menu(update, context)

    async def handle_perfume_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
        """Обрабатывает вопросы о парфюмах"""
        user_id = update.effective_user.id
        
        # Проверяем кулдаун
        if self.ai.is_api_cooldown_active(user_id):
            await update.message.reply_text("⏱️ Пожалуйста, подождите 30 секунд перед следующим вопросом")
            return
        
        # Отправляем уведомление о обработке
        processing_msg = await update.message.reply_text("🤔 Анализирую ваш запрос и подбираю лучшие варианты...")
        
        try:
            # Получаем все парфюмы из БД (без лимитов!)
            perfumes_data = self.db.get_all_perfumes_from_database()
            
            # Создаем промпт для ИИ
            prompt = self.ai.create_perfume_question_prompt(message_text, perfumes_data)
            
            # Получаем ответ от ИИ
            ai_response = await self.ai.call_openrouter_api(prompt, max_tokens=4000)
            
            # Обрабатываем ответ и добавляем ссылки
            processed_response = self.ai.process_ai_response_with_links(ai_response, self.db)
            
            # Удаляем сообщение о обработке
            await processing_msg.delete()
            
            # Отправляем ответ
            await update.message.reply_text(
                processed_response,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            
            # Сохраняем статистику
            self.db.save_usage_stat(user_id, "perfume_question", None, message_text, len(processed_response))
            
            # Устанавливаем кулдаун
            self.ai.set_api_cooldown(user_id, 30)
            
            # Возвращаем в главное меню
            self.db.update_session_state(user_id, "MAIN_MENU")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса: {e}")
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке вашего вопроса. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )

    async def handle_fragrance_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
        """Обрабатывает запросы информации об аромате"""
        user_id = update.effective_user.id
        
        # Отправляем уведомление о поиске
        searching_msg = await update.message.reply_text("🔍 Ищу информацию об аромате...")
        
        try:
            # Получаем все парфюмы для поиска
            all_perfumes = self.db.get_all_perfumes_from_database()
            
            # Ищем подходящие ароматы
            matching_perfumes = self.ai.find_perfumes_by_query(message_text, all_perfumes)
            
            if not matching_perfumes:
                await searching_msg.delete()
                await update.message.reply_text(
                    "😔 Не удалось найти информацию по вашему запросу. Попробуйте изменить поисковой запрос.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                )
                return
            
            # Создаем промпт для информации об аромате
            prompt = self.ai.create_fragrance_info_prompt(message_text, matching_perfumes)
            
            # Получаем информацию от ИИ
            ai_response = await self.ai.call_openrouter_api(prompt, max_tokens=3000)
            
            # Обрабатываем ответ
            processed_response = self.ai.process_ai_response_with_links(ai_response, self.db)
            
            # Удаляем сообщение о поиске
            await searching_msg.delete()
            
            # Отправляем информацию
            await update.message.reply_text(
                processed_response,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            
            # Возвращаем в главное меню
            self.db.update_session_state(user_id, "MAIN_MENU")
            
        except Exception as e:
            logger.error(f"Ошибка при поиске информации: {e}")
            await searching_msg.delete()
            await update.message.reply_text(
                "❌ Произошла ошибка при поиске информации. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )

    async def run(self):
        """Запускает бота"""
        # Запускаем автопарсер в фоне
        asyncio.create_task(self.auto_parser.start_scheduler())
        
        # Запускаем бота
        await self.application.initialize()
        await self.application.start()
        
        logger.info("🚀 Perfume Bot запущен и готов к работе!")
        
        # Обработка graceful shutdown
        def signal_handler(sig, frame):
            logger.info("🛑 Получен сигнал завершения, останавливаем бота...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запускаем polling
        await self.application.updater.start_polling()
        await self.application.updater.idle()

def main():
    """Главная функция"""
    try:
        bot = PerfumeBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()