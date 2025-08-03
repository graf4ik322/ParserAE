#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import signal
import sys
import os
import fcntl
import re
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
        self.lock_file = None
        
        # Инициализация приложения
        self.application = Application.builder().token(self.config.bot_token).build()
        
        # Регистрация обработчиков
        self._register_handlers()
        
        logger.info("🤖 Perfume Bot инициализирован")

    def _acquire_lock(self):
        """Создает файл-блокировку для предотвращения множественного запуска"""
        lock_file_path = '/tmp/perfume_bot.lock'
        try:
            self.lock_file = open(lock_file_path, 'w')
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()
            logger.info("🔒 Блокировка получена успешно")
            return True
        except IOError:
            logger.error("❌ Другой экземпляр бота уже запущен!")
            if self.lock_file:
                self.lock_file.close()
            return False

    def _release_lock(self):
        """Освобождает файл-блокировку"""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                os.unlink('/tmp/perfume_bot.lock')
                logger.info("🔓 Блокировка освобождена")
            except Exception as e:
                logger.error(f"Ошибка при освобождении блокировки: {e}")

    def _setup_signal_handlers(self):
        """Настраивает обработчики сигналов для корректного завершения"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Получен сигнал {signum}, завершаем работу...")
            self._release_lock()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений"""
        # Простой тестовый обработчик
        self.application.add_handler(CommandHandler("test", self.test_command))
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("parse", self.parse_command))
        
        # Новые админ команды
        self.application.add_handler(CommandHandler("admin", self.admin_panel_command))
        self.application.add_handler(CommandHandler("admindb", self.admin_database_command))
        self.application.add_handler(CommandHandler("adminapi", self.admin_api_command))
        self.application.add_handler(CommandHandler("adminparser", self.admin_parser_command))
        self.application.add_handler(CommandHandler("adminforce", self.admin_force_parse_command))
        self.application.add_handler(CommandHandler("fixurls", self.fix_urls_command))
        
        # Callback-кнопки
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
        
        logger.info("✅ Обработчики зарегистрированы")

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Простой тестовый обработчик"""
        user = update.effective_user
        logger.info(f"🧪 ТЕСТ: Получена команда /test от пользователя {user.id}")
        await update.message.reply_text("✅ Бот работает! Тест успешен!")
        logger.info("🧪 ТЕСТ: Ответ отправлен")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        error_message = str(context.error)
        
        # Игнорируем устаревшие callback запросы - это нормально при долгой обработке ИИ
        if "Query is too old" in error_message or "response timeout expired" in error_message:
            logger.info(f"ℹ️ Игнорируем устаревший callback запрос: {error_message}")
            return
            
        logger.error(f"❌ Ошибка в обработчике: {context.error}")
        
        try:
            # Определяем тип update и отправляем соответствующий ответ
            if update and hasattr(update, 'callback_query') and update.callback_query:
                # Для callback_query ошибок
                try:
                    await update.callback_query.answer("❌ Произошла ошибка. Попробуйте позже.")
                except Exception:
                    pass  # Игнорируем если callback_query уже был обработан
                
                try:
                    await update.callback_query.edit_message_text(
                        "❌ Произошла ошибка. Попробуйте позже.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                    )
                except Exception:
                    # Если не удается редактировать, отправляем новое сообщение
                    try:
                        await update.effective_chat.send_message(
                            "❌ Произошла ошибка. Попробуйте позже.",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                        )
                    except Exception:
                        pass
                        
            elif update and hasattr(update, 'message') and update.message:
                # Для message ошибок
                try:
                    await update.message.reply_text(
                        "❌ Произошла ошибка. Попробуйте позже.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                    )
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ Ошибка в error_handler: {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        logger.info(f"📨 Получена команда /start от пользователя {user.id} (@{user.username})")
        
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
        user_id = update.effective_user.id
        
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
/stats - Краткая статистика

**Как использовать:**
1. Выберите нужную опцию в главном меню
2. Следуйте инструкциям бота
3. Задавайте вопросы в свободной форме

Бот работает с полным каталогом из 1200+ ароматов! 🎉
        """
        
        # Добавляем админ-команды для администратора
        if user_id == self.config.admin_user_id:
            help_text += """

🔧 **Команды администратора:**
/admin - Главная админ-панель
/admindb - Состояние базы данных
/adminapi - Проверка API ключа
/adminparser - Статус парсера
/adminforce - Принудительный парсинг
/parse - Быстрый парсинг (совместимость)

**Админ-панель включает:**
📊 Подробную информацию о БД
🔑 Тестирование OpenRouter API
🔄 Мониторинг парсера
⚡ Ручной запуск парсинга
📈 Полную статистику системы
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
            result = await self.auto_parser.force_parse_catalog(admin_user_id=user_id)
            if result.get('success', False):
                await update.message.reply_text("✅ Каталог успешно обновлен!")
            else:
                await update.message.reply_text("⚠️ Обновление не требуется - каталог актуален")
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {e}")
            await update.message.reply_text(f"❌ Ошибка при обновлении каталога: {e}")

    async def admin_panel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главная админ-панель"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Состояние БД", callback_data="admin_db")],
            [InlineKeyboardButton("🔑 Проверить API", callback_data="admin_api")],
            [InlineKeyboardButton("🔄 Статус парсера", callback_data="admin_parser")],
            [InlineKeyboardButton("⚡ Запустить парсинг", callback_data="admin_force_parse")],
            [InlineKeyboardButton("📈 Полная статистика", callback_data="admin_full_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_text = f"""
🔧 **Административная панель**

Добро пожаловать, администратор!

**Доступные функции:**
📊 **Состояние БД** - подробная информация о базе данных
🔑 **Проверить API** - тестирование OpenRouter API
🔄 **Статус парсера** - мониторинг системы парсинга
⚡ **Запустить парсинг** - принудительное обновление каталога
📈 **Полная статистика** - детальная аналитика

🕐 Время: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
        """
        
        await update.message.reply_text(
            admin_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def admin_database_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подробная информация о базе данных"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        try:
            db_info = self.db.get_detailed_database_info()
            
            # Формируем отчет
            report = f"📊 **Подробная информация о базе данных**\n\n"
            
            report += f"📁 **Файл БД:** `{db_info['database_path']}`\n"
            report += f"💾 **Размер:** {db_info['database_size']}\n\n"
            
            # Информация о таблицах
            report += "📋 **Таблицы:**\n"
            for table, info in db_info['tables'].items():
                status = "✅" if info['exists'] else "❌"
                report += f"{status} `{table}`: {info['count']} записей\n"
            
            # Топ пользователи
            if db_info['top_users']:
                report += f"\n👥 **Топ-{len(db_info['top_users'])} активных пользователей:**\n"
                for user in db_info['top_users'][:5]:
                    username = user['username'] or user['first_name'] or f"ID{user['telegram_id']}"
                    report += f"• {username}: {user['activity_count']} действий\n"
            
            # Статистика парфюмов
            if 'top_brands' in db_info['perfume_stats']:
                report += f"\n🌸 **Топ-5 брендов:**\n"
                for brand in db_info['perfume_stats']['top_brands'][:5]:
                    report += f"• {brand['brand']}: {brand['count']} ароматов\n"
            
            # API использование
            if db_info['api_usage']:
                recent_api = db_info['api_usage'][0]
                report += f"\n🔑 **API за последний день:**\n"
                report += f"• Запросов: {recent_api['requests']}\n"
                report += f"• Токенов: {recent_api['total_tokens']}\n"
            
            # Ошибки
            if db_info['errors']:
                report += f"\n⚠️ **Ошибки:**\n"
                for error in db_info['errors'][:3]:
                    report += f"• {error}\n"
            
            await update.message.reply_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")]])
            )
            
        except Exception as e:
            logger.error(f"Ошибка в admin_database_command: {e}")
            await update.message.reply_text(f"❌ Ошибка при получении информации о БД: {e}")

    async def admin_api_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка состояния API"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        checking_msg = await update.message.reply_text("🔍 Проверяю состояние API...")
        
        try:
            api_status = await self.ai.check_api_status()
            
            # Формируем отчет
            status_icon = "✅" if api_status['api_key_valid'] else "❌"
            report = f"🔑 **Состояние OpenRouter API** {status_icon}\n\n"
            
            report += f"🔐 **API Key:** `{api_status['api_key_masked']}`\n"
            report += f"🤖 **Модель:** `{api_status['model']}`\n"
            report += f"🌐 **URL:** `{api_status['base_url']}`\n"
            report += f"⏰ **Проверено:** {datetime.fromisoformat(api_status['last_check']).strftime('%H:%M:%S')}\n"
            
            if api_status['response_time']:
                report += f"⚡ **Время ответа:** {api_status['response_time']}с\n"
            
            if api_status['api_key_valid']:
                report += f"✅ **Статус:** API работает корректно\n"
                if api_status.get('tokens_used'):
                    report += f"🎯 **Токенов в тесте:** {api_status['tokens_used']}\n"
                if api_status.get('actual_model'):
                    report += f"🔧 **Фактическая модель:** `{api_status['actual_model']}`\n"
            else:
                report += f"❌ **Ошибка:** {api_status.get('error', 'Неизвестная ошибка')}\n"
            
            await checking_msg.delete()
            await update.message.reply_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")]])
            )
            
        except Exception as e:
            logger.error(f"Ошибка в admin_api_command: {e}")
            await checking_msg.delete()
            await update.message.reply_text(f"❌ Ошибка при проверке API: {e}")

    async def admin_parser_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статус парсера"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        try:
            parser_status = self.auto_parser.get_parser_status()
            
            # Формируем отчет
            status_icon = "🔄" if parser_status['is_running'] else "⏸️"
            report = f"🔄 **Статус парсера** {status_icon}\n\n"
            
            # Текущее состояние
            report += f"📊 **Текущее состояние:**\n"
            report += f"• Запущен: {'✅ Да' if parser_status['running_since_start'] else '❌ Нет'}\n"
            report += f"• Активен: {'✅ Да' if parser_status['is_running'] else '❌ Нет'}\n"
            
            if parser_status['current_operation']:
                report += f"• Операция: {parser_status['current_operation']}\n"
            
            if parser_status['last_operation_time']:
                last_op = datetime.fromisoformat(parser_status['last_operation_time'])
                report += f"• Последняя операция: {last_op.strftime('%H:%M:%S %d.%m')}\n"
            
            # Статистика
            stats = parser_status['statistics']
            report += f"\n📈 **Статистика:**\n"
            report += f"• Всего запусков: {stats['total_runs']}\n"
            report += f"• Успешных: {stats['successful_runs']}\n"
            report += f"• Ошибок: {stats['failed_runs']}\n"
            report += f"• Последний результат: +{stats['last_items_added']}, ~{stats['last_items_updated']}\n"
            
            # Исходные файлы
            report += f"\n📁 **Исходные файлы:**\n"
            for filename, file_info in parser_status['source_files'].items():
                status = "✅" if file_info['exists'] else "❌"
                size = f" ({file_info['size']} байт)" if file_info['exists'] else ""
                report += f"{status} `{filename}`{size}\n"
            
            # БД статистика
            if 'database_statistics' in parser_status and not parser_status['database_statistics'].get('error'):
                db_stats = parser_status['database_statistics']
                if db_stats['last_parse_time']:
                    last_parse = datetime.fromisoformat(db_stats['last_parse_time'])
                    report += f"\n🕐 **Последний парсинг:** {last_parse.strftime('%H:%M:%S %d.%m.%Y')}\n"
            
            await update.message.reply_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚡ Запустить парсинг", callback_data="admin_force_parse")],
                    [InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")]
                ])
            )
            
        except Exception as e:
            logger.error(f"Ошибка в admin_parser_command: {e}")
            await update.message.reply_text(f"❌ Ошибка при получении статуса парсера: {e}")

    async def admin_force_parse_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Принудительный запуск парсинга"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        # Проверяем, не запущен ли уже парсер
        parser_status = self.auto_parser.get_parser_status()
        if parser_status['is_running']:
            await update.message.reply_text(
                "⚠️ Парсер уже выполняется. Дождитесь завершения текущей операции.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Статус парсера", callback_data="admin_parser")]])
            )
            return
        
        processing_msg = await update.message.reply_text("🔄 Запускаю принудительный парсинг каталога...")
        
        try:
            result = await self.auto_parser.force_parse_catalog(admin_user_id=user_id)
            
            # Формируем детальный отчет
            status_icon = "✅" if result['success'] else "❌"
            report = f"🔄 **Результат парсинга** {status_icon}\n\n"
            
            report += f"⏰ **Время выполнения:** {result['execution_time']}с\n"
            report += f"👤 **Запущен админом:** ID{result['started_by']}\n"
            report += f"🕐 **Время:** {datetime.fromisoformat(result['start_time']).strftime('%H:%M:%S %d.%m.%Y')}\n\n"
            
            if result['success']:
                report += f"📊 **Результаты:**\n"
                report += f"• Обработано из источника: {result.get('total_items_in_source', 'N/A')}\n"
                report += f"• Было в БД: {result.get('items_before', 'N/A')}\n"
                report += f"• Стало в БД: {result.get('items_after', 'N/A')}\n"
                report += f"• Добавлено: {result['items_added']}\n"
                report += f"• Обновлено: {result['items_updated']}\n"
            else:
                report += f"❌ **Ошибки:**\n"
                for error in result['errors'][:3]:
                    report += f"• {error}\n"
            
            # Статус исходных файлов
            if 'source_files_status' in result:
                report += f"\n📁 **Исходные файлы:**\n"
                for filename, file_info in result['source_files_status'].items():
                    status = "✅" if file_info['exists'] else "❌"
                    report += f"{status} {filename}\n"
            
            await processing_msg.delete()
            await update.message.reply_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Статус парсера", callback_data="admin_parser")],
                    [InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")]
                ])
            )
            
        except Exception as e:
            logger.error(f"Ошибка в admin_force_parse_command: {e}")
            await processing_msg.delete()
            await update.message.reply_text(f"❌ Ошибка при запуске парсинга: {e}")

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает главное меню"""
        user_id = update.effective_user.id
        
        # Основные кнопки для всех пользователей
        keyboard = [
            [InlineKeyboardButton("🎯 Задать вопрос о парфюмах", callback_data="perfume_question")],
            [InlineKeyboardButton("📝 Пройти квиз-рекомендации", callback_data="start_quiz")],
            [InlineKeyboardButton("🔍 Информация об аромате", callback_data="fragrance_info")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        
        # Добавляем кнопку админ-панели для администраторов
        if user_id == self.config.admin_user_id:
            keyboard.append([InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")])
        
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
        # Админ-панель callbacks
        elif query.data == "admin_panel":
            await self._handle_admin_panel_callback(update, context)
        elif query.data == "admin_db":
            await self._handle_admin_db_callback(update, context)
        elif query.data == "admin_api":
            await self._handle_admin_api_callback(update, context)
        elif query.data == "admin_parser":
            await self._handle_admin_parser_callback(update, context)
        elif query.data == "admin_force_parse":
            await self._handle_admin_force_parse_callback(update, context)
        elif query.data == "admin_full_stats":
            await self._handle_admin_full_stats_callback(update, context)
        else:
            # Обработка неизвестных callback'ов с защитой от рекурсии
            logger.warning(f"Неизвестный callback: {query.data} от пользователя {user_id}")
            
            # Если back_to_menu тоже неизвестен, показываем /start без кнопок
            if query.data == "back_to_menu":
                try:
                    await query.edit_message_text(
                        "❌ Произошла ошибка навигации. Используйте команду /start для перезапуска."
                    )
                except Exception as e:
                    logger.error(f"Критическая ошибка callback: {e}")
                    await update.effective_chat.send_message(
                        "❌ Критическая ошибка. Используйте /start для перезапуска."
                    )
            else:
                # Для других неизвестных callback'ов - возврат в меню
                try:
                    await query.edit_message_text(
                        "❌ Неизвестная команда. Возвращаюсь в главное меню.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                    )
                except Exception as e:
                    logger.error(f"Ошибка при обработке неизвестного callback: {e}")
                    # Fallback - отправляем новое сообщение
                    await update.effective_chat.send_message(
                        "❌ Произошла ошибка. Возвращаюсь в главное меню.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                    )

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
        
        # Валидация входных данных
        if not message_text or not message_text.strip():
            await update.message.reply_text(
                "❌ Пожалуйста, введите ваш вопрос о парфюмах.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            return
        
        message_text = message_text.strip()
        
        if len(message_text) < 2:
            await update.message.reply_text(
                "❌ Вопрос должен содержать минимум 2 символа.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            return
        
        if len(message_text) > 1000:
            await update.message.reply_text(
                "❌ Вопрос слишком длинный. Пожалуйста, сократите его до 1000 символов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            return
        
        # Отправляем уведомление о обработке
        processing_msg = await update.message.reply_text("🤔 Анализирую ваш запрос и подбираю лучшие варианты...")
        
        try:
            # Получаем все парфюмы из БД (без лимитов!)
            perfumes_data = self.db.get_all_perfumes_from_database()
            
            # Создаем промпт для ИИ
            prompt = self.ai.create_perfume_question_prompt(message_text, perfumes_data)
            
            # Получаем ответ от ИИ
            ai_response = await self.ai.process_message(prompt, user_id)
            
            # Проверяем, не вернулся ли ответ о кулдауне
            if "Пожалуйста, подождите" in ai_response:
                await processing_msg.delete()
                await update.message.reply_text(ai_response)
                return
            
            # Обрабатываем ответ и добавляем ссылки
            processed_response = self.ai.process_ai_response_with_links(ai_response, self.db)
            
            # Удаляем сообщение о обработке
            await processing_msg.delete()
            
            # Безопасно отправляем ответ с защитой от ошибок форматирования
            try:
                await update.message.reply_text(
                    processed_response,
                    parse_mode='Markdown',
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                )
            except Exception as format_error:
                logger.warning(f"Ошибка форматирования ответа о парфюмах: {format_error}")
                # Fallback к простому тексту без форматирования
                plain_response = re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', processed_response)[:4000]
                await update.message.reply_text(
                    plain_response,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                )
            
            # Сохраняем статистику
            self.db.save_usage_stat(user_id, "perfume_question", None, message_text, len(processed_response))
            
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
        
        # Валидация входных данных
        if not message_text or not message_text.strip():
            await update.message.reply_text(
                "❌ Пожалуйста, введите название аромата или ваш запрос.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            return
        
        message_text = message_text.strip()
        
        if len(message_text) < 2:
            await update.message.reply_text(
                "❌ Запрос должен содержать минимум 2 символа.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            return
        
        if len(message_text) > 1000:
            await update.message.reply_text(
                "❌ Запрос слишком длинный. Пожалуйста, сократите его до 1000 символов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            return
        
        # Отправляем уведомление о поиске
        searching_msg = await update.message.reply_text("🔍 Ищу информацию об аромате...")
        
        try:
            # Используем улучшенный промпт для профессиональной информации об ароматах
            from ai.prompts import PromptTemplates
            prompt = PromptTemplates.create_fragrance_info_prompt(message_text)

            # Получаем ответ от ИИ
            ai_response_raw = await self.ai.process_message(prompt, user_id)
            
            # Проверяем, не вернулся ли ответ о кулдауне
            if "Пожалуйста, подождите" in ai_response_raw:
                await searching_msg.delete()
                await update.message.reply_text(ai_response_raw)
                return
            
            # Обрабатываем ответ и добавляем ссылки по артикулам
            ai_response = self.ai.process_ai_response_with_links(ai_response_raw, self.db)
            
            # Удаляем сообщение о поиске
            await searching_msg.delete()
            
            # Безопасно отправляем информацию с защитой от ошибок форматирования
            try:
                # НЕ форматируем повторно, так как это уже сделано в process_message()
                await update.message.reply_text(
                    ai_response,
                    parse_mode='Markdown',
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                )
            except Exception as format_error:
                logger.warning(f"Ошибка форматирования ответа об аромате: {format_error}")
                # Fallback к простому тексту без форматирования
                plain_response = re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', ai_response)[:4000]
                await update.message.reply_text(
                    plain_response,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
                )
            
            # Сохраняем статистику
            self.db.save_usage_stat(user_id, "fragrance_info", None, message_text, len(ai_response))
            
            # Возвращаем в главное меню
            self.db.update_session_state(user_id, "MAIN_MENU")
            
        except Exception as e:
            logger.error(f"Ошибка при поиске информации: {e}")
            await searching_msg.delete()
            await update.message.reply_text(
                "❌ Произошла ошибка при поиске информации. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )

    async def _handle_admin_panel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает callback для главной админ-панели"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.callback_query.edit_message_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Состояние БД", callback_data="admin_db")],
            [InlineKeyboardButton("🔑 Проверить API", callback_data="admin_api")],
            [InlineKeyboardButton("🔄 Статус парсера", callback_data="admin_parser")],
            [InlineKeyboardButton("⚡ Запустить парсинг", callback_data="admin_force_parse")],
            [InlineKeyboardButton("📈 Полная статистика", callback_data="admin_full_stats")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_text = f"""
🔧 **Административная панель**

Добро пожаловать, администратор!

**Доступные функции:**
📊 **Состояние БД** - подробная информация о базе данных
🔑 **Проверить API** - тестирование OpenRouter API
🔄 **Статус парсера** - мониторинг системы парсинга
⚡ **Запустить парсинг** - принудительное обновление каталога
📈 **Полная статистика** - детальная аналитика

🕐 Время: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
        """
        
        await update.callback_query.edit_message_text(
            admin_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _handle_admin_db_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает callback для информации о БД"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.callback_query.edit_message_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        await update.callback_query.edit_message_text("🔍 Получаю информацию о базе данных...")
        
        try:
            db_info = self.db.get_detailed_database_info()
            
            # Формируем отчет (укороченная версия для callback)
            report = f"📊 **База данных**\n\n"
            report += f"💾 **Размер:** {db_info['database_size']}\n\n"
            
            # Информация о таблицах
            report += "📋 **Таблицы:**\n"
            for table, info in db_info['tables'].items():
                status = "✅" if info['exists'] else "❌"
                report += f"{status} `{table}`: {info['count']}\n"
            
            # Топ брендов
            if 'top_brands' in db_info['perfume_stats']:
                report += f"\n🌸 **Топ-3 бренда:**\n"
                for brand in db_info['perfume_stats']['top_brands'][:3]:
                    report += f"• {brand['brand']}: {brand['count']}\n"
            
            await update.callback_query.edit_message_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")]])
            )
            
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка: {e}")

    async def _handle_admin_api_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает callback для проверки API"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.callback_query.edit_message_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        await update.callback_query.edit_message_text("🔍 Проверяю состояние API...")
        
        try:
            api_status = await self.ai.check_api_status()
            
            status_icon = "✅" if api_status['api_key_valid'] else "❌"
            report = f"🔑 **API Status** {status_icon}\n\n"
            
            report += f"🔐 **Key:** `{api_status['api_key_masked']}`\n"
            report += f"🤖 **Model:** `{api_status['model']}`\n"
            
            if api_status['response_time']:
                report += f"⚡ **Response:** {api_status['response_time']}s\n"
            
            if api_status['api_key_valid']:
                report += f"✅ **Status:** Working\n"
            else:
                report += f"❌ **Error:** {api_status.get('error', 'Unknown')[:50]}...\n"
            
            await update.callback_query.edit_message_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")]])
            )
            
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка: {e}")

    async def _handle_admin_parser_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает callback для статуса парсера"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.callback_query.edit_message_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        await update.callback_query.edit_message_text("🔍 Получаю статус парсера...")
        
        try:
            parser_status = self.auto_parser.get_parser_status()
            
            status_icon = "🔄" if parser_status['is_running'] else "⏸️"
            report = f"🔄 **Parser Status** {status_icon}\n\n"
            
            report += f"• Running: {'✅' if parser_status['running_since_start'] else '❌'}\n"
            report += f"• Active: {'✅' if parser_status['is_running'] else '❌'}\n"
            
            stats = parser_status['statistics']
            report += f"\n📈 **Stats:**\n"
            report += f"• Total: {stats['total_runs']}\n"
            report += f"• Success: {stats['successful_runs']}\n"
            report += f"• Errors: {stats['failed_runs']}\n"
            
            await update.callback_query.edit_message_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚡ Run Parser", callback_data="admin_force_parse")],
                    [InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel")]
                ])
            )
            
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка: {e}")

    async def _handle_admin_force_parse_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает callback для принудительного парсинга"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.callback_query.edit_message_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        # Проверяем статус парсера
        parser_status = self.auto_parser.get_parser_status()
        if parser_status['is_running']:
            await update.callback_query.edit_message_text(
                "⚠️ Парсер уже выполняется",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Статус", callback_data="admin_parser")]])
            )
            return
        
        await update.callback_query.edit_message_text("🔄 Запускаю парсинг...")
        
        try:
            result = await self.auto_parser.force_parse_catalog(admin_user_id=user_id)
            
            status_icon = "✅" if result['success'] else "❌"
            report = f"🔄 **Parse Result** {status_icon}\n\n"
            report += f"⏰ **Time:** {result['execution_time']}s\n"
            
            if result['success']:
                report += f"• Added: {result['items_added']}\n"
                report += f"• Updated: {result['items_updated']}\n"
            else:
                report += f"❌ **Errors:**\n"
                for error in result['errors'][:2]:
                    report += f"• {error[:50]}...\n"
            
            await update.callback_query.edit_message_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")]])
            )
            
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка: {e}")

    async def _handle_admin_full_stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает callback для полной статистики"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.callback_query.edit_message_text("❌ У вас нет прав доступа к админ-панели")
            return
        
        await update.callback_query.edit_message_text("📊 Собираю полную статистику...")
        
        try:
            # Получаем всю статистику
            basic_stats = self.db.get_admin_statistics()
            db_info = self.db.get_detailed_database_info()
            parser_status = self.auto_parser.get_parser_status()
            
            report = f"📈 **Полная статистика системы**\n\n"
            
            # Основные цифры
            report += f"👥 **Пользователи:** {basic_stats['total_users']} (активных сегодня: {basic_stats['active_users_today']})\n"
            report += f"🌸 **Парфюмы:** {basic_stats['total_perfumes']}\n"
            report += f"❓ **Вопросов:** {basic_stats['total_questions']}\n"
            report += f"📝 **Квизов:** {basic_stats['total_quizzes']}\n"
            report += f"🔑 **API токенов сегодня:** {basic_stats['api_usage_today']}\n\n"
            
            # Статус систем
            report += f"💾 **БД размер:** {db_info['database_size']}\n"
            parser_icon = "🔄" if parser_status['is_running'] else "⏸️"
            report += f"🔄 **Парсер:** {parser_icon} ({parser_status['statistics']['total_runs']} запусков)\n\n"
            
            # Топ активности
            if db_info['top_users']:
                report += f"🏆 **Топ пользователь:** {db_info['top_users'][0]['activity_count']} действий\n"
            
            if 'top_brands' in db_info['perfume_stats']:
                top_brand = db_info['perfume_stats']['top_brands'][0]
                report += f"🌟 **Топ бренд:** {top_brand['brand']} ({top_brand['count']} ароматов)\n"
            
            await update.callback_query.edit_message_text(
                report,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_panel")]])
            )
            
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Ошибка: {e}")

    async def _post_init_callback(self, application):
        """Callback для инициализации после запуска бота"""
        try:
            logger.info("🔄 Запускаем автоматический планировщик парсера...")
            await self.auto_parser.start_scheduler()
            logger.info("✅ Планировщик парсера запущен успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика парсера: {e}")
            # Парсер не критичен для работы бота, поэтому продолжаем

    def run(self):
        """Запускает бота"""
        try:
            # Проверяем, не запущен ли уже другой экземпляр
            if not self._acquire_lock():
                logger.error("❌ Бот уже запущен! Завершаем работу.")
                sys.exit(1)
            
            # Настраиваем обработчики сигналов
            self._setup_signal_handlers()
            
            # Настраиваем post_init callback для автозапуска парсера
            self.application.post_init = self._post_init_callback
            
            logger.info("🚀 Perfume Bot запущен и готов к работе!")
            
            # Запускаем polling с логированием
            logger.info("📡 Запускаем polling для получения обновлений...")
            self.application.run_polling(drop_pending_updates=True)
            
        except KeyboardInterrupt:
            logger.info("🛑 Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            raise
        finally:
            # Освобождаем блокировку при любом завершении
            self._release_lock()

    async def fix_urls_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для исправления URL с /product/ на /parfume/ в базе данных"""
        user_id = update.effective_user.id
        
        if user_id != self.config.admin_user_id:
            await update.message.reply_text("❌ У вас нет прав для исправления URL")
            return
        
        try:
            await update.message.reply_text("🔧 Исправляю URL в базе данных...")
            
            # Исправляем URL в базе данных
            fixed_count = self.db.fix_product_urls_to_parfume()
            
            await update.message.reply_text(
                f"✅ Исправление URL завершено!\n"
                f"📊 Обновлено записей: {fixed_count}\n"
                f"🔗 Все ссылки теперь используют /parfume/ вместо /product/"
            )
            
        except Exception as e:
            logger.error(f"Ошибка при исправлении URL: {e}")
            await update.message.reply_text(f"❌ Ошибка при исправлении URL: {e}")

def main():
    """Главная функция"""
    bot = None
    try:
        bot = PerfumeBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except SystemExit:
        # Нормальное завершение при множественном запуске
        pass
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        if bot:
            bot._release_lock()

if __name__ == "__main__":
    main()