#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import asyncio
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# Импорты наших модулей
from config import BOT_TOKEN, OPENROUTER_API_KEY, OPENROUTER_CONFIG, DATA_FILES, LLM_LIMITS, ADMIN_USER_ID, TEXT_FORMATTING
from quiz_system import PerfumeQuizSystem, create_quiz_system
from ai_prompts import AIPrompts, PromptLimits

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('perfume_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
class BotState(Enum):
    MAIN_MENU = 0
    PERFUME_QUESTION = 1
    QUIZ_IN_PROGRESS = 2
    FRAGRANCE_INFO = 3
    WAITING_USER_INPUT = 4

@dataclass
class UserSession:
    """Данные пользовательской сессии"""
    current_state: BotState = BotState.MAIN_MENU
    quiz_answers: Dict[str, Any] = None
    quiz_step: int = 0
    last_message_id: Optional[int] = None
    context_data: Dict[str, Any] = None
    # Добавляем маппинг для callback данных
    callback_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        if self.quiz_answers is None:
            self.quiz_answers = {}
        if self.context_data is None:
            self.context_data = {}
        if self.callback_mapping is None:
            self.callback_mapping = {}

class PerfumeConsultantBot:
    """Главный класс парфюмерного консультанта"""
    
    def __init__(self, bot_token: str, openrouter_api_key: str):
        self.bot_token = bot_token
        self.openrouter_api_key = openrouter_api_key
        self.user_sessions: Dict[int, UserSession] = {}
        
        # Загружаем нормализованные данные
        self.normalized_data = self._load_normalized_data()
        
        # Инициализируем систему квиза
        self.quiz_system = create_quiz_system()
        
        # Конфигурация OpenRouter
        self.openrouter_config = {
            'base_url': OPENROUTER_CONFIG['base_url'],
            'model': OPENROUTER_CONFIG['model'],
            'headers': {
                'Authorization': f'Bearer {openrouter_api_key}',
                'Content-Type': 'application/json'
            }
        }
        
        logger.info("✅ Парфюмерный консультант инициализирован")
    
    def _load_normalized_data(self) -> Dict[str, Any]:
        """Загружает все нормализованные данные"""
        data = {}
        
        for key, filename in DATA_FILES.items():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data[key] = json.load(f)
                logger.info(f"✅ Загружен файл: {filename}")
            except FileNotFoundError:
                logger.error(f"❌ Файл не найден: {filename}")
                data[key] = [] if 'json' in filename else {}
        
        # Загружаем полный каталог для получения URL
        try:
            with open('full_perfumes_catalog_complete.json', 'r', encoding='utf-8') as f:
                full_catalog = json.load(f)
                data['full_catalog'] = full_catalog
                logger.info("✅ Загружен полный каталог с URL")
        except FileNotFoundError:
            logger.error("❌ Полный каталог не найден")
            data['full_catalog'] = {'perfumes': []}
        
        return data
    
    def _format_text_for_telegram(self, text: str) -> str:
        """Форматирует текст для лучшей читаемости в Telegram"""
        import re
        
        # Убираем лишние звездочки и заменяем на HTML теги
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Ограничиваем количество эмодзи
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001f900-\U0001f9ff\U0001f018-\U0001f270]', text))
        if emoji_count > TEXT_FORMATTING['max_emojis_per_message']:
            # Удаляем лишние эмодзи, оставляя только первые
            emojis_found = 0
            def replace_emoji(match):
                nonlocal emojis_found
                emojis_found += 1
                if emojis_found <= TEXT_FORMATTING['max_emojis_per_message']:
                    return match.group(0)
                return ''
            
            text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001f900-\U0001f9ff\U0001f018-\U0001f270]', replace_emoji, text)
        
        # Разбиваем длинные блоки текста
        lines = text.split('\n')
        formatted_lines = []
        current_block = []
        
        for line in lines:
            if line.strip() == '':
                if current_block:
                    formatted_lines.extend(current_block)
                    formatted_lines.append('')
                    current_block = []
            else:
                current_block.append(line)
                
                # Если блок становится слишком длинным, добавляем разделитель
                if len(current_block) >= TEXT_FORMATTING['max_lines_per_block']:
                    formatted_lines.extend(current_block)
                    formatted_lines.append('—' * 20)  # Разделитель
                    current_block = []
        
        # Добавляем оставшиеся строки
        if current_block:
            formatted_lines.extend(current_block)
        
        # Убираем лишние пустые строки
        result = []
        prev_empty = False
        for line in formatted_lines:
            if line.strip() == '':
                if not prev_empty:
                    result.append(line)
                prev_empty = True
            else:
                result.append(line)
                prev_empty = False
        
        return '\n'.join(result)

    def _create_perfume_url_mapping(self) -> Dict[str, str]:
        """Создает словарь сопоставления названий ароматов с URL"""
        url_mapping = {}
        
        if 'full_catalog' in self.normalized_data:
            perfumes = self.normalized_data['full_catalog'].get('perfumes', [])
            
            for perfume in perfumes:
                # Создаем различные варианты ключей для поиска
                brand = perfume.get('brand', '').strip()
                name = perfume.get('name', '').strip()
                url = perfume.get('url', '')
                
                if brand and name and url:
                    # Основной ключ: "Бренд Название"
                    main_key = f"{brand} {name}".lower()
                    url_mapping[main_key] = url
                    
                    # Дополнительный ключ: только название
                    name_key = name.lower()
                    if name_key not in url_mapping:
                        url_mapping[name_key] = url
                    
                    # Ключ с полным названием
                    full_title = perfume.get('full_title', '').strip()
                    if full_title:
                        full_key = full_title.lower().replace('(мотив)', '').replace(',', '').strip()
                        url_mapping[full_key] = url
        
        logger.info(f"✅ Создан словарь URL для {len(url_mapping)} ароматов")
        return url_mapping

    def _find_perfume_url(self, perfume_name: str) -> Optional[str]:
        """Находит URL для конкретного аромата"""
        if 'full_catalog' not in self.normalized_data:
            return None
            
        perfumes = self.normalized_data['full_catalog'].get('perfumes', [])
        normalized_search = perfume_name.lower().strip()
        
        # Сначала ищем точное совпадение по имени
        for perfume in perfumes:
            if perfume.get('name', '').lower() == normalized_search:
                return perfume.get('url')
        
        # Затем ищем по полному названию
        for perfume in perfumes:
            full_title = perfume.get('full_title', '').lower()
            if normalized_search in full_title:
                return perfume.get('url')
        
        # Ищем по бренду + имени
        for perfume in perfumes:
            brand_name = f"{perfume.get('brand', '')} {perfume.get('name', '')}".lower().strip()
            if normalized_search in brand_name or brand_name in normalized_search:
                return perfume.get('url')
        
        return None

    def _process_ai_response_with_urls(self, ai_response: str) -> str:
        """Обрабатывает ответ ИИ и заменяет PLACEHOLDER_URL на реальные ссылки"""
        import re
        
        # Паттерн для поиска названий ароматов в ответе
        # Ищем строки вида "**Название аромата**" или "1. **Название аромата**"
        pattern = r'\*\*([^*]+)\*\*\s*\([^)]+\)'
        
        def replace_placeholder(match):
            full_match = match.group(0)
            perfume_name = match.group(1).strip()
            
            # Находим URL для этого аромата
            url = self._find_perfume_url(perfume_name)
            
            if url:
                # Заменяем PLACEHOLDER_URL на реальную ссылку в пределах этого блока
                # Ищем PLACEHOLDER_URL после найденного названия аромата
                return full_match
            else:
                return full_match
        
        # Сначала находим все названия ароматов
        processed_response = ai_response
        
        # Теперь заменяем все PLACEHOLDER_URL на реальные ссылки
        lines = processed_response.split('\n')
        current_perfume_url = None
        
        for i, line in enumerate(lines):
            # Если нашли название аромата, запоминаем его URL
            perfume_match = re.search(pattern, line)
            if perfume_match:
                perfume_name = perfume_match.group(1).strip()
                current_perfume_url = self._find_perfume_url(perfume_name)
            
            # Если нашли PLACEHOLDER_URL и у нас есть URL для текущего аромата
            if 'PLACEHOLDER_URL' in line and current_perfume_url:
                lines[i] = line.replace('PLACEHOLDER_URL', current_perfume_url)
                current_perfume_url = None  # Сбрасываем после использования
            elif 'PLACEHOLDER_URL' in line:
                # Если нет URL, убираем строку со ссылкой
                lines[i] = ''
        
        # Применяем форматирование для лучшей читаемости
        formatted_response = self._format_text_for_telegram('\n'.join(lines))
        return formatted_response

    def _extract_perfume_names_from_response(self, response: str) -> List[str]:
        """Извлекает названия ароматов из ответа ИИ"""
        import re
        
        # Паттерны для поиска названий ароматов
        patterns = [
            r'\*\*([^*]+)\*\*\s*\([^)]+\)',  # **Название** (Фабрика)
            r'^\d+\.\s*\*\*([^*]+)\*\*',     # 1. **Название**
            r'^\d+\.\s*([^(]+)\s*\(',        # 1. Название (
        ]
        
        perfume_names = []
        lines = response.split('\n')
        
        for line in lines:
            for pattern in patterns:
                match = re.search(pattern, line.strip())
                if match:
                    name = match.group(1).strip()
                    if name and name not in perfume_names:
                        perfume_names.append(name)
                    break
        
        return perfume_names

    def _is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом"""
        return user_id == ADMIN_USER_ID and ADMIN_USER_ID != 0

    def _get_admin_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру с админскими функциями"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton("💰 Баланс API", callback_data="admin_balance")
            ],
            [
                InlineKeyboardButton("🏭 Анализ фабрик", callback_data="admin_factory_analysis"),
                InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def _show_admin_menu(self, query_or_update) -> None:
        """Показывает админское меню"""
        text = (
            "🔧 <b>Панель администратора</b>\n\n"
            "Добро пожаловать в админскую панель!\n\n"
            "📊 <b>Доступные функции:</b>\n"
            "• <b>Статистика</b> - детальная статистика базы данных\n"
            "• <b>Баланс API</b> - информация об использовании OpenRouter\n"
            "• <b>Анализ фабрик</b> - подробный анализ производителей\n"
            "• <b>Пользователи</b> - статистика активности пользователей\n\n"
            "Выберите нужную функцию:"
        )
        
        keyboard = self._get_admin_keyboard()
        
        if hasattr(query_or_update, 'edit_message_text'):
            await query_or_update.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await query_or_update.message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
    def get_user_session(self, user_id: int) -> UserSession:
        """Получает или создает сессию пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession()
        return self.user_sessions[user_id]
    
    async def send_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отправляет главное меню"""
        user_id = update.effective_user.id
        is_admin = self._is_admin(user_id)
        
        # Основные функции для всех пользователей
        keyboard = [
            [
                InlineKeyboardButton("🤔 Парфюмерный вопрос", callback_data="perfume_question"),
                InlineKeyboardButton("🎯 Подбор парфюма", callback_data="perfume_quiz")
            ],
            [
                InlineKeyboardButton("📖 Что за аромат?", callback_data="fragrance_info"),
                InlineKeyboardButton("❓ Помощь", callback_data="help")
            ]
        ]
        
        # Добавляем админскую кнопку только для админа
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("🔧 Админ-панель", callback_data="admin_menu")
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        stats = self._get_database_stats()
        
        user_id = update.effective_user.id
        is_admin = self._is_admin(user_id)
        
        base_text = (
            "🌟 <b>Парфюмерный консультант</b>\n\n"
            "Добро пожаловать! Я ваш персональный ИИ-консультант по парфюмерии.\n\n"
            "🎯 <b>Мои возможности:</b>\n"
            "• Отвечаю на любые вопросы о парфюмерии\n"
            "• Подбираю идеальные ароматы по вашим предпочтениям\n"
            "• Даю подробную информацию об ароматах\n"
            "• Добавляю прямые ссылки на товары для заказа\n\n"
            f"📚 <b>База данных:</b>\n"
            f"• Ароматов: <b>{stats['total_perfumes']}</b>\n"
            f"• Брендов: <b>{stats['total_brands']}</b>\n"
            f"• Фабрик: <b>{stats['total_factories']}</b>\n\n"
        )
        
        if is_admin:
            text = base_text + "🔧 <b>Админ-панель доступна</b>\n\nВыберите нужную функцию:"
        else:
            text = base_text + "Выберите нужную функцию:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text, 
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            message = await update.message.reply_text(
                text=text, 
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            # Сохраняем ID сообщения для последующего редактирования
            user_session = self.get_user_session(update.effective_user.id)
            user_session.last_message_id = message.message_id
        
        return BotState.MAIN_MENU.value
    
    def _get_database_stats(self) -> Dict[str, int]:
        """Получает статистику базы данных"""
        return {
            'total_perfumes': len(self.normalized_data.get('full_data_compact', [])),
            'total_brands': len(self.normalized_data.get('quiz_reference', {}).get('brands', [])),
            'total_factories': len(self.normalized_data.get('factory_analysis', {}))
        }
    
    async def handle_perfume_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка парфюмерных вопросов"""
        query = update.callback_query
        await query.answer()
        
        user_session = self.get_user_session(update.effective_user.id)
        user_session.current_state = BotState.PERFUME_QUESTION
        
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🤔 <b>Парфюмерный вопрос</b>\n\n"
            "Задайте любой вопрос о парфюмерии, и я подберу идеальные ароматы из нашей базы!\n\n"
            "💡 <b>Примеры вопросов:</b>\n"
            "• <i>Какой аромат подойдет для добавления в гель для стирки?</i>\n"
            "• <i>Что лучше использовать для освежителя воздуха?</i>\n"
            "• <i>Какие ароматы подходят для мыловарения?</i>\n"
            "• <i>Посоветуй что-то свежее и цитрусовое для лета</i>\n"
            "• <i>Нужен стойкий мужской аромат для вечера</i>\n\n"
            "✍️ Напишите ваш вопрос:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return BotState.WAITING_USER_INPUT.value
    
    async def process_perfume_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает вопрос пользователя через ИИ"""
        user_question = update.message.text
        user_id = update.effective_user.id
        
        # Отправляем сообщение о обработке
        processing_msg = await update.message.reply_text("🤖 Анализирую ваш вопрос и подбираю идеальные ароматы...")
        
        try:
            # Получаем данные для промпта
            name_factory_list = self.normalized_data.get('name_factory', [])
            factory_analysis = self.normalized_data.get('factory_analysis', {})
            
            # Создаем промпт с помощью нашего модуля
            prompt = AIPrompts.create_perfume_question_prompt(
                user_question=user_question,
                perfume_list=name_factory_list,
                factory_analysis=factory_analysis,
                limit_perfumes=LLM_LIMITS['question_list_limit'],
                limit_factories=LLM_LIMITS['factory_summary_limit']
            )
            
            # Отправляем запрос к OpenRouter
            ai_response = await self._call_openrouter_api(
                prompt, 
                max_tokens=PromptLimits.MAX_TOKENS_QUESTION,
                temperature=PromptLimits.TEMP_BALANCED
            )
            
            # Обрабатываем ответ и добавляем ссылки
            processed_response = self._process_ai_response_with_urls(ai_response)
            
            # Удаляем сообщение о обработке
            await processing_msg.delete()
            
            # Отправляем ответ
            keyboard = [
                [InlineKeyboardButton("❓ Задать еще вопрос", callback_data="perfume_question")],
                [InlineKeyboardButton("🎯 Пройти квиз", callback_data="perfume_quiz")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            response_text = f"🤔 <b>Ответ эксперта:</b>\n\n{processed_response}"
            
            # Разбиваем длинный ответ на части если нужно
            if len(response_text) > 4000:
                parts = self._split_message(response_text, 4000)
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Последняя часть с кнопками
                        await update.message.reply_text(
                            text=part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    else:
                        await update.message.reply_text(text=part, parse_mode='HTML')
            else:
                await update.message.reply_text(
                    text=response_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            await processing_msg.delete()
            
            # Создаем промпт для обработки ошибки
            error_prompt = AIPrompts.create_error_handling_prompt(
                error_context=str(e),
                user_input=user_question
            )
            
            try:
                error_response = await self._call_openrouter_api(
                    error_prompt, 
                    max_tokens=PromptLimits.MAX_TOKENS_ERROR
                )
                error_text = f"⚠️ {error_response}"
            except:
                error_text = (
                    "❌ Извините, произошла техническая ошибка при обработке вашего вопроса.\n\n"
                    "Попробуйте:\n"
                    "• Переформулировать вопрос\n"
                    "• Пройти квиз для подбора ароматов\n"
                    "• Вернуться в главное меню"
                )
            
            await update.message.reply_text(
                text=error_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")
                ]]),
                parse_mode='HTML'
            )
        
        return BotState.MAIN_MENU.value
    
    def _split_message(self, text: str, max_length: int) -> List[str]:
        """Разбивает длинное сообщение на части"""
        if len(text) <= max_length:
            return [text]
        
        parts = []
        current_part = ""
        
        for line in text.split('\n'):
            if len(current_part + line + '\n') <= max_length:
                current_part += line + '\n'
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = line + '\n'
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts
    
    async def start_perfume_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Запускает квиз для подбора парфюма"""
        query = update.callback_query
        await query.answer()
        
        user_session = self.get_user_session(update.effective_user.id)
        user_session.current_state = BotState.QUIZ_IN_PROGRESS
        user_session.quiz_step = 0
        user_session.quiz_answers = {}
        
        # Первый вопрос квиза
        await self._send_quiz_question(query, user_session)
        
        return BotState.QUIZ_IN_PROGRESS.value
    
    async def _send_quiz_question(self, query_or_update, user_session: UserSession) -> None:
        """Отправляет вопрос квиза"""
        current_question = self.quiz_system.get_next_question(
            user_session.quiz_answers, 
            user_session.quiz_step
        )
        
        if current_question is None:
            # Квиз завершен, показываем результаты
            await self._show_quiz_results(query_or_update, user_session)
            return
        
        # Создаем клавиатуру для вопроса
        keyboard = []
        for i, option in enumerate(current_question.options):
            # Создаем короткий callback_data на основе индекса
            callback_data = f"quiz_{current_question.key}_{i}"
            # Сохраняем соответствие между индексом и полным текстом
            user_session.callback_mapping[callback_data] = option
            keyboard.append([InlineKeyboardButton(option, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total_questions = self.quiz_system.get_total_questions()
        progress = f"({user_session.quiz_step + 1}/{total_questions})"
        
        text = f"🎯 <b>Подбор парфюма</b> {progress}\n\n{current_question.text}"
        
        if hasattr(query_or_update, 'edit_message_text'):
            await query_or_update.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await query_or_update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    async def _show_quiz_results(self, query_or_update, user_session: UserSession) -> None:
        """Показывает результаты квиза"""
        processing_text = "🤖 Анализирую ваши предпочтения и подбираю идеальные ароматы...\n\n⏳ Это может занять несколько секунд"
        
        if hasattr(query_or_update, 'edit_message_text'):
            await query_or_update.edit_message_text(text=processing_text)
        
        try:
            # Анализируем ответы квиза
            user_profile = self.quiz_system.analyze_answers(user_session.quiz_answers)
            
            # Получаем данные для рекомендаций
            brand_name_factory_list = self.normalized_data.get('brand_name_factory', [])
            factory_analysis = self.normalized_data.get('factory_analysis', {})
            
            # Создаем промпт для рекомендаций
            prompt = self.quiz_system.create_recommendation_prompt(
                profile=user_profile,
                available_perfumes=brand_name_factory_list,
                factory_analysis=factory_analysis
            )
            
            # Получаем рекомендации от ИИ
            ai_response = await self._call_openrouter_api(
                prompt, 
                max_tokens=PromptLimits.MAX_TOKENS_QUIZ,
                temperature=PromptLimits.TEMP_CREATIVE
            )
            
            # Обрабатываем ответ и добавляем ссылки
            processed_response = self._process_ai_response_with_urls(ai_response)
            
            # Сбрасываем состояние квиза после завершения
            user_session.current_state = BotState.MAIN_MENU
            user_session.quiz_step = 0
            user_session.quiz_answers = {}
            user_session.callback_mapping = {}
            
            keyboard = [
                [InlineKeyboardButton("🎯 Пройти квиз снова", callback_data="perfume_quiz")],
                [InlineKeyboardButton("❓ Задать вопрос", callback_data="perfume_question")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            result_text = f"🎯 <b>Ваши персональные рекомендации:</b>\n\n{processed_response}"
            
            # Разбиваем длинный ответ если нужно
            if len(result_text) > 4000:
                parts = self._split_message(result_text, 4000)
                for i, part in enumerate(parts):
                    if i == 0 and hasattr(query_or_update, 'edit_message_text'):
                        await query_or_update.edit_message_text(
                            text=part,
                            parse_mode='HTML'
                        )
                    elif i == len(parts) - 1:  # Последняя часть с кнопками
                        await query_or_update.message.reply_text(
                            text=part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    else:
                        await query_or_update.message.reply_text(text=part, parse_mode='HTML')
            else:
                if hasattr(query_or_update, 'edit_message_text'):
                    await query_or_update.edit_message_text(
                        text=result_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
        
        except Exception as e:
            error_text = f"❌ Ошибка при подборе ароматов: {str(e)}\n\nПопробуйте пройти квиз еще раз или задайте вопрос напрямую."
            keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
            
            if hasattr(query_or_update, 'edit_message_text'):
                await query_or_update.edit_message_text(
                    text=error_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    
    async def handle_fragrance_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка запроса информации об аромате"""
        query = update.callback_query
        await query.answer()
        
        user_session = self.get_user_session(update.effective_user.id)
        user_session.current_state = BotState.FRAGRANCE_INFO
        
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📖 <b>Информация об аромате</b>\n\n"
            "Введите название аромата и бренд для получения подробной экспертной информации.\n\n"
            "💡 <b>Примеры запросов:</b>\n"
            "• <i>Tom Ford Lost Cherry</i>\n"
            "• <i>Chanel Coco Mademoiselle</i>\n"
            "• <i>Dior Sauvage</i>\n"
            "• <i>Creed Aventus</i>\n\n"
            "✍️ Напишите название аромата:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return BotState.WAITING_USER_INPUT.value
    
    async def process_fragrance_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает запрос информации об аромате"""
        fragrance_query = update.message.text
        
        processing_msg = await update.message.reply_text("🔍 Ищу подробную информацию об аромате...")
        
        try:
            # Создаем промпт для получения информации об аромате
            prompt = AIPrompts.create_fragrance_info_prompt(fragrance_query)
            
            # Получаем ответ от ИИ
            ai_response = await self._call_openrouter_api(
                prompt, 
                max_tokens=PromptLimits.MAX_TOKENS_INFO,
                temperature=PromptLimits.TEMP_FACTUAL
            )
            
            await processing_msg.delete()
            
            keyboard = [
                [InlineKeyboardButton("🔍 Найти еще аромат", callback_data="fragrance_info")],
                [InlineKeyboardButton("🎯 Пройти квиз", callback_data="perfume_quiz")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            response_text = f"📖 <b>Экспертная информация:</b>\n\n{ai_response}"
            
            # Разбиваем длинный ответ если нужно
            if len(response_text) > 4000:
                parts = self._split_message(response_text, 4000)
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Последняя часть с кнопками
                        await update.message.reply_text(
                            text=part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    else:
                        await update.message.reply_text(text=part, parse_mode='HTML')
            else:
                await update.message.reply_text(
                    text=response_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            await processing_msg.delete()
            await update.message.reply_text(
                f"❌ Ошибка при поиске информации: {str(e)}\n\nПопробуйте еще раз или вернитесь в главное меню.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")
                ]]),
                parse_mode='HTML'
            )
        
        return BotState.MAIN_MENU.value
    
    async def _call_openrouter_api(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Вызывает OpenRouter API"""
        payload = {
            "model": self.openrouter_config['model'],
            "messages": [
                {
                    "role": "system",
                    "content": AIPrompts.create_system_message()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.openrouter_config['base_url'],
                headers=self.openrouter_config['headers'],
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error: {response.status} - {error_text}")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработчик callback запросов"""
        query = update.callback_query
        data = query.data
        user_id = update.effective_user.id
        user_session = self.get_user_session(user_id)
        
        if data == "main_menu":
            await self.send_main_menu(update, context)
            return BotState.MAIN_MENU.value
        
        elif data == "perfume_question":
            return await self.handle_perfume_question(update, context)
        
        elif data == "perfume_quiz":
            return await self.start_perfume_quiz(update, context)
        
        elif data == "fragrance_info":
            return await self.handle_fragrance_info(update, context)
        
        elif data.startswith("quiz_"):
            # Обработка ответов квиза
            parts = data.split("_", 2)
            if len(parts) >= 3:
                key = parts[1]
                # Получаем полный текст ответа из маппинга
                full_answer = user_session.callback_mapping.get(data)
                if full_answer:
                    user_session.quiz_answers[key] = full_answer
                    user_session.quiz_step += 1
                    logger.info(f"Quiz step {user_session.quiz_step}/{self.quiz_system.get_total_questions()}: {key} = {full_answer}")
                    await self._send_quiz_question(query, user_session)
                else:
                    logger.warning(f"Не найден маппинг для callback_data: {data}")
                    # Пропускаем вопрос если нет маппинга
                    user_session.quiz_step += 1
                    await self._send_quiz_question(query, user_session)
            return BotState.QUIZ_IN_PROGRESS.value
        
        elif data == "help":
            await self._show_help(query)
            return BotState.MAIN_MENU.value
        
        elif data == "admin_menu":
            if self._is_admin(update.effective_user.id):
                await self._show_admin_menu(query)
            else:
                await query.answer("❌ Доступ запрещен. Только для администраторов.")
            return BotState.MAIN_MENU.value
        
        elif data == "admin_stats":
            if self._is_admin(update.effective_user.id):
                await self._show_statistics(query)
            else:
                await query.answer("❌ Доступ запрещен. Только для администраторов.")
            return BotState.MAIN_MENU.value
        
        elif data == "admin_balance":
            if self._is_admin(update.effective_user.id):
                await self._show_api_balance(query)
            else:
                await query.answer("❌ Доступ запрещен. Только для администраторов.")
            return BotState.MAIN_MENU.value
        
        elif data == "admin_factory_analysis":
            if self._is_admin(update.effective_user.id):
                await self._show_factory_analysis(query)
            else:
                await query.answer("❌ Доступ запрещен. Только для администраторов.")
            return BotState.MAIN_MENU.value
        
        elif data == "admin_users":
            if self._is_admin(update.effective_user.id):
                await self._show_user_statistics(query)
            else:
                await query.answer("❌ Доступ запрещен. Только для администраторов.")
            return BotState.MAIN_MENU.value
        
        return BotState.MAIN_MENU.value
    
    async def _show_statistics(self, query) -> None:
        """Показывает статистику базы данных"""
        stats_data = self.normalized_data
        
        text = (
            "📊 <b>Статистика базы данных</b>\n\n"
            f"🧪 Всего ароматов: <b>{len(stats_data.get('full_data_compact', []))}</b>\n"
            f"🏷️ Уникальных названий: <b>{len(stats_data.get('names_only', []))}</b>\n"
            f"🏭 Фабрик: <b>{len(stats_data.get('factory_analysis', {}))}</b>\n"
            f"🎯 Брендов: <b>{len(stats_data.get('quiz_reference', {}).get('brands', []))}</b>\n\n"
            f"<b>🏆 Топ-5 фабрик по количеству ароматов:</b>\n"
        )
        
        # Добавляем топ фабрик
        factory_analysis = stats_data.get('factory_analysis', {})
        sorted_factories = sorted(factory_analysis.items(), key=lambda x: x[1]['perfume_count'], reverse=True)
        
        for i, (factory, data) in enumerate(sorted_factories[:5], 1):
            text += f"{i}. <b>{factory}</b>: {data['perfume_count']} ароматов\n"
        
        text += f"\n💡 <i>Все данные актуальны и готовы для консультаций!</i>"
        
        keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def _show_factory_analysis(self, query) -> None:
        """Показывает анализ фабрик"""
        factory_analysis = self.normalized_data.get('factory_analysis', {})
        
        text = "🏭 <b>Анализ фабрик-производителей</b>\n\n"
        
        sorted_factories = sorted(factory_analysis.items(), key=lambda x: x[1]['perfume_count'], reverse=True)
        
        for factory, data in sorted_factories[:10]:
            text += f"<b>🏭 {factory}</b>\n"
            text += f"  • Ароматов в каталоге: <b>{data['perfume_count']}</b>\n"
            text += f"  • Представленных брендов: <b>{len(data['brands'])}</b>\n"
            if data['quality_levels']:
                text += f"  • Уровни качества: <i>{', '.join(data['quality_levels'][:3])}</i>\n"
            text += "\n"
        
        text += "💡 <i>Используйте эту информацию при выборе ароматов!</i>"
        
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def _show_help(self, query) -> None:
        """Показывает справку"""
        text = (
            "❓ <b>Справка по парфюмерному консультанту</b>\n\n"
            
            "<b>🤔 Парфюмерный вопрос</b>\n"
            "Задайте любой вопрос о парфюмерии. ИИ-эксперт проанализирует вашу потребность и подберет "
            "подходящие ароматы из нашей базы с учетом фабрик-производителей.\n\n"
            
            "<b>🎯 Подбор парфюма</b>\n"
            "Пройдите детальный квиз из 12 вопросов. Система проанализирует ваши предпочтения и создаст "
            "персональную подборку из 5-7 идеальных ароматов.\n\n"
            
            "<b>📖 Что за аромат?</b>\n"
            "Введите название любого аромата для получения подробной экспертной информации: описание, "
            "ноты, история создания, советы по использованию.\n\n"
            
            "<b>📊 Статистика</b>\n"
            "Актуальная информация о нашей базе данных: количество ароматов, брендов, фабрик.\n\n"
            
            "<b>🏭 Анализ фабрик</b>\n"
            "Подробная информация о фабриках-производителях парфюмерных композиций.\n\n"
            
            "<b>🤖 Технологии:</b>\n"
            "• База: 1200+ ароматов с детальной информацией\n"
            "• ИИ: Claude 3 Haiku через OpenRouter\n"
            "• Оптимизация: специальные промпты для экономии токенов\n\n"
            
            "💡 <i>Все рекомендации основаны на реальных данных из парсинга aroma-euro.ru</i>"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def _show_api_balance(self, query) -> None:
        """Показывает информацию об API OpenRouter"""
        try:
            # Попробуем получить информацию о лимитах через специальный эндпоинт
            balance_url = "https://openrouter.ai/api/v1/auth/key"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    balance_url,
                    headers=self.openrouter_config['headers']
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        balance_text = f"💰 <b>Информация об API OpenRouter:</b>\n\n"
                        balance_text += f"🔑 <b>Ключ API:</b> Активен\n"
                        balance_text += f"🤖 <b>Модель:</b> {self.openrouter_config['model']}\n"
                        
                        # Если есть данные о лимитах
                        if 'data' in data:
                            key_data = data['data']
                            if 'usage' in key_data:
                                usage = key_data['usage']
                                balance_text += f"💸 <b>Использовано:</b> ${usage.get('total_cost', 'N/A')}\n"
                                balance_text += f"📊 <b>Запросов:</b> {usage.get('requests', 'N/A')}\n"
                            
                            if 'limit' in key_data:
                                limit = key_data['limit']
                                balance_text += f"💳 <b>Лимит:</b> ${limit.get('amount', 'N/A')}\n"
                        
                        balance_text += f"\n📈 <b>Статистика бота:</b>\n"
                        balance_text += f"• Средняя стоимость вопроса: ~$0.001-0.002\n"
                        balance_text += f"• Средняя стоимость квиза: ~$0.002-0.003\n"
                        balance_text += f"• Рекомендуемый месячный бюджет: $5-15\n\n"
                        balance_text += f"🌐 <b>Ссылка на панель управления:</b>\n"
                        balance_text += f"[OpenRouter Dashboard](https://openrouter.ai/keys)\n\n"
                        balance_text += "💡 <i>Для точного баланса проверьте панель управления OpenRouter</i>"
                        
                    else:
                        # Если не удалось получить данные, показываем общую информацию
                        balance_text = f"💰 <b>Информация об API OpenRouter:</b>\n\n"
                        balance_text += f"🔑 <b>Статус ключа:</b> Проверяется...\n"
                        balance_text += f"🤖 <b>Модель:</b> {self.openrouter_config['model']}\n\n"
                        balance_text += f"📈 <b>Примерная стоимость:</b>\n"
                        balance_text += f"• Вопрос: ~$0.001-0.002\n"
                        balance_text += f"• Квиз: ~$0.002-0.003\n"
                        balance_text += f"• Информация об аромате: ~$0.001-0.002\n\n"
                        balance_text += f"🌐 <b>Проверить баланс:</b>\n"
                        balance_text += f"[OpenRouter Dashboard](https://openrouter.ai/keys)\n\n"
                        balance_text += "💡 <i>Для точного баланса используйте панель управления OpenRouter</i>"
            
            keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=balance_text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации об API: {e}")
            error_text = (
                "💰 <b>Информация об API OpenRouter:</b>\n\n"
                f"🤖 <b>Модель:</b> {self.openrouter_config['model']}\n\n"
                f"📈 <b>Примерная стоимость:</b>\n"
                f"• Парфюмерный вопрос: ~$0.001-0.002\n"
                f"• Прохождение квиза: ~$0.002-0.003\n"
                f"• Информация об аромате: ~$0.001-0.002\n\n"
                f"🌐 <b>Проверить точный баланс:</b>\n"
                f"[OpenRouter Dashboard](https://openrouter.ai/keys)\n\n"
                f"💡 <i>Рекомендуемый месячный бюджет: $5-15</i>\n\n"
                f"⚠️ <i>Не удалось получить данные API. Проверьте панель управления.</i>"
            )
            keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text=error_text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    
    async def _show_user_statistics(self, query) -> None:
        """Показывает статистику пользователей (только для админа)"""
        try:
            total_users = len(self.user_sessions)
            active_sessions = sum(1 for session in self.user_sessions.values() 
                                if session.current_state != BotState.MAIN_MENU)
            
            # Статистика по состояниям
            state_stats = {}
            for session in self.user_sessions.values():
                state = session.current_state.name if hasattr(session.current_state, 'name') else str(session.current_state)
                state_stats[state] = state_stats.get(state, 0) + 1
            
            stats_text = f"👥 <b>Статистика пользователей:</b>\n\n"
            stats_text += f"📊 <b>Общая статистика:</b>\n"
            stats_text += f"• Всего пользователей: <b>{total_users}</b>\n"
            stats_text += f"• Активных сессий: <b>{active_sessions}</b>\n\n"
            
            if state_stats:
                stats_text += f"📈 <b>По состояниям:</b>\n"
                for state, count in state_stats.items():
                    stats_text += f"• {state}: <b>{count}</b>\n"
            
            stats_text += f"\n💡 <i>Статистика обновляется в реальном времени</i>"
            
            keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=stats_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики пользователей: {e}")
            error_text = (
                "❌ <b>Ошибка при получении статистики пользователей</b>\n\n"
                "Произошла техническая ошибка. Попробуйте позже."
            )
            keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text=error_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    def create_application(self) -> Application:
        """Создает приложение Telegram бота"""
        application = Application.builder().token(self.bot_token).build()
        
        # Conversation handler для управления состояниями
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.send_main_menu)],
            states={
                BotState.MAIN_MENU.value: [
                    CallbackQueryHandler(self.handle_callback_query)
                ],
                BotState.WAITING_USER_INPUT.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_user_input),
                    CallbackQueryHandler(self.handle_callback_query)
                ],
                BotState.QUIZ_IN_PROGRESS.value: [
                    CallbackQueryHandler(self.handle_callback_query)
                ],
            },
            fallbacks=[
                CommandHandler("start", self.send_main_menu),
                CallbackQueryHandler(self.handle_callback_query)
            ],
        )
        
        application.add_handler(conv_handler)
        return application
    
    async def process_user_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает пользовательский ввод в зависимости от состояния"""
        user_session = self.get_user_session(update.effective_user.id)
        
        if user_session.current_state == BotState.PERFUME_QUESTION:
            return await self.process_perfume_question(update, context)
        elif user_session.current_state == BotState.FRAGRANCE_INFO:
            return await self.process_fragrance_info(update, context)
        
        return BotState.MAIN_MENU.value

def main():
    """Основная функция запуска бота"""
    
    # Проверяем наличие токенов
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY_HERE":
        print("❌ Ошибка: Необходимо настроить токены в файле .env")
        print("📝 Скопируйте .env.example в .env и укажите ваши токены")
        return
    
    print("🚀 Запуск парфюмерного консультанта...")
    print("📚 Загрузка базы данных...")
    
    try:
        bot = PerfumeConsultantBot(BOT_TOKEN, OPENROUTER_API_KEY)
        application = bot.create_application()
        
        print("✅ Парфюмерный консультант готов к работе!")
        print(f"📊 Загружено ароматов: {len(bot.normalized_data.get('full_data_compact', []))}")
        print(f"🏭 Фабрик в базе: {len(bot.normalized_data.get('factory_analysis', {}))}")
        print("🤖 ИИ-консультант активирован")
        print("💬 Бот запущен и ожидает сообщений...")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()