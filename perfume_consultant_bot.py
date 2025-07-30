#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
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
    
    def __post_init__(self):
        if self.quiz_answers is None:
            self.quiz_answers = {}
        if self.context_data is None:
            self.context_data = {}

class PerfumeConsultantBot:
    """Главный класс парфюмерного консультанта"""
    
    def __init__(self, bot_token: str, openrouter_api_key: str):
        self.bot_token = bot_token
        self.openrouter_api_key = openrouter_api_key
        self.user_sessions: Dict[int, UserSession] = {}
        
        # Загружаем нормализованные данные
        self.normalized_data = self._load_normalized_data()
        
        # Конфигурация OpenRouter
        self.openrouter_config = {
            'base_url': 'https://openrouter.ai/api/v1/chat/completions',
            'model': 'anthropic/claude-3-haiku',  # Экономичная модель
            'headers': {
                'Authorization': f'Bearer {openrouter_api_key}',
                'Content-Type': 'application/json'
            }
        }
    
    def _load_normalized_data(self) -> Dict[str, Any]:
        """Загружает все нормализованные данные"""
        data = {}
        files_to_load = [
            'names_only.json',
            'brand_name.json', 
            'name_factory.json',
            'brand_name_factory.json',
            'full_data_compact.json',
            'factory_analysis.json',
            'quiz_reference.json'
        ]
        
        for filename in files_to_load:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    key = filename.replace('.json', '')
                    data[key] = json.load(f)
                logger.info(f"Загружен файл: {filename}")
            except FileNotFoundError:
                logger.error(f"Файл не найден: {filename}")
                data[filename.replace('.json', '')] = []
        
        return data
    
    def get_user_session(self, user_id: int) -> UserSession:
        """Получает или создает сессию пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession()
        return self.user_sessions[user_id]
    
    async def send_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отправляет главное меню"""
        keyboard = [
            [
                InlineKeyboardButton("🤔 Парфюмерный вопрос", callback_data="perfume_question"),
                InlineKeyboardButton("🎯 Подбор парфюма", callback_data="perfume_quiz")
            ],
            [
                InlineKeyboardButton("📖 Что за аромат?", callback_data="fragrance_info"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton("🏭 Анализ фабрик", callback_data="factory_analysis"),
                InlineKeyboardButton("❓ Помощь", callback_data="help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🌟 <b>Парфюмерный консультант</b>\n\n"
            "Добро пожаловать! Я помогу вам:\n"
            "• Ответить на вопросы о парфюмерии\n"
            "• Подобрать идеальный аромат\n"
            "• Узнать подробности об ароматах\n"
            "• Проанализировать фабрики и бренды\n\n"
            f"📚 В моей базе: <b>{len(self.normalized_data.get('full_data_compact', []))}</b> ароматов\n"
            f"🏷️ Брендов: <b>{len(self.normalized_data.get('quiz_reference', {}).get('brands', []))}</b>\n"
            f"🏭 Фабрик: <b>{len(self.normalized_data.get('factory_analysis', {}))}</b>\n\n"
            "Выберите нужную функцию:"
        )
        
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
            "Задайте любой вопрос о парфюмерии!\n\n"
            "<i>Примеры вопросов:</i>\n"
            "• Какой аромат подойдет для добавления в гель для стирки?\n"
            "• Что лучше использовать для освежителя воздуха?\n"
            "• Какие ароматы подходят для мыловарения?\n"
            "• Посоветуй что-то свежее и цитрусовое\n\n"
            "Напишите ваш вопрос:"
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
        processing_msg = await update.message.reply_text("🤖 Анализирую ваш вопрос...")
        
        try:
            # Формируем промпт для ИИ
            name_factory_list = self.normalized_data.get('name_factory', [])
            factory_analysis = self.normalized_data.get('factory_analysis', {})
            
            prompt = self._create_question_prompt(user_question, name_factory_list, factory_analysis)
            
            # Отправляем запрос к OpenRouter
            ai_response = await self._call_openrouter_api(prompt)
            
            # Удаляем сообщение о обработке
            await processing_msg.delete()
            
            # Отправляем ответ
            keyboard = [
                [InlineKeyboardButton("❓ Задать еще вопрос", callback_data="perfume_question")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            response_text = f"🤔 <b>Ответ на ваш вопрос:</b>\n\n{ai_response}"
            
            await update.message.reply_text(
                text=response_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            await processing_msg.delete()
            await update.message.reply_text(
                f"❌ Произошла ошибка при обработке вопроса: {str(e)}\n\n"
                "Попробуйте еще раз или вернитесь в главное меню.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")
                ]])
            )
        
        return BotState.MAIN_MENU.value
    
    def _create_question_prompt(self, user_question: str, name_factory_list: List[str], 
                               factory_analysis: Dict[str, Any]) -> str:
        """Создает промпт для обработки вопроса пользователя"""
        
        # Ограничиваем список для экономии токенов (первые 200 позиций)
        limited_list = name_factory_list[:200]
        
        # Создаем краткую сводку по фабрикам
        factory_summary = []
        for factory, data in list(factory_analysis.items())[:10]:  # Топ-10 фабрик
            factory_summary.append(
                f"- {factory}: {data['perfume_count']} ароматов, "
                f"качество: {', '.join(data['quality_levels'][:3])}"
            )
        
        prompt = f"""Ты - эксперт-парфюмер и консультант по ароматам. 

Пользователь задал вопрос: "{user_question}"

Из перечисленных ароматов выбери наиболее подходящие для запроса пользователя:

ДОСТУПНЫЕ АРОМАТЫ (название + фабрика):
{chr(10).join(limited_list)}

ИНФОРМАЦИЯ О ФАБРИКАХ:
{chr(10).join(factory_summary)}

ИНСТРУКЦИИ:
1. Проанализируй запрос пользователя и выбери 3-5 наиболее подходящих ароматов
2. Для каждого выбранного аромата укажи фабрику-производителя
3. Объясни, почему именно эти ароматы подходят для запроса
4. Дай рекомендации по фабрикам - какая лучше передает характер аромата
5. Добавь практические советы по использованию

Ответ должен быть структурированным и полезным."""

        return prompt
    
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
            "Введите название аромата и бренд для получения подробной информации.\n\n"
            "<i>Примеры:</i>\n"
            "• Tom Ford Lost Cherry\n"
            "• Chanel Coco Mademoiselle\n"
            "• Dior Sauvage\n\n"
            "Напишите название:"
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
        
        processing_msg = await update.message.reply_text("🔍 Ищу информацию об аромате...")
        
        try:
            # Создаем промпт для получения информации об аромате
            prompt = self._create_fragrance_info_prompt(fragrance_query)
            
            # Получаем ответ от ИИ
            ai_response = await self._call_openrouter_api(prompt)
            
            await processing_msg.delete()
            
            keyboard = [
                [InlineKeyboardButton("🔍 Найти еще аромат", callback_data="fragrance_info")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            response_text = f"📖 <b>Информация об аромате:</b>\n\n{ai_response}"
            
            await update.message.reply_text(
                text=response_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            await processing_msg.delete()
            await update.message.reply_text(
                f"❌ Ошибка при поиске информации: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")
                ]])
            )
        
        return BotState.MAIN_MENU.value
    
    def _create_fragrance_info_prompt(self, fragrance_query: str) -> str:
        """Создает промпт для получения информации об аромате"""
        return f"""Ты - эксперт-парфюмер с энциклопедическими знаниями о парфюмерии.

Пользователь спрашивает об аромате: "{fragrance_query}"

ЗАДАЧА:
1. Исправь возможные ошибки в написании названия аромата и бренда
2. Дай полное описание аромата как на сайте Fragrantica
3. Опиши пирамиду ароматов (верхние, средние, базовые ноты)
4. Расскажи в повествовательном стиле, чем пахнет аромат
5. Укажи, когда лучше носить (сезон, время суток, мероприятия)
6. Дай рекомендации по использованию
7. Укажи целевую аудиторию (пол, возраст)

Ответ должен быть подробным, но читаемым, с эмоциональными описаниями и практическими советами."""
    
    async def _send_quiz_question(self, query_or_update, user_session: UserSession) -> None:
        """Отправляет вопрос квиза"""
        # Здесь будет логика квиза - пока заглушка
        questions = [
            {
                'text': '👤 Для кого подбираем аромат?',
                'options': ['Для себя (мужчина)', 'Для себя (женщина)', 'Универсальный', 'В подарок'],
                'key': 'target_gender'
            },
            {
                'text': '🌡️ Какой сезон предпочитаете?',
                'options': ['Весна', 'Лето', 'Осень', 'Зима', 'Универсальный'],
                'key': 'season'
            },
            {
                'text': '⏰ Время использования?',
                'options': ['Утро/День', 'Вечер/Ночь', 'Особые случаи', 'Ежедневно'],
                'key': 'time_of_day'
            }
        ]
        
        if user_session.quiz_step < len(questions):
            question = questions[user_session.quiz_step]
            keyboard = []
            
            for option in question['options']:
                keyboard.append([InlineKeyboardButton(option, callback_data=f"quiz_{question['key']}_{option}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"🎯 <b>Подбор парфюма</b> ({user_session.quiz_step + 1}/{len(questions)})\n\n{question['text']}"
            
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
        else:
            # Квиз завершен, показываем результаты
            await self._show_quiz_results(query_or_update, user_session)
    
    async def _show_quiz_results(self, query_or_update, user_session: UserSession) -> None:
        """Показывает результаты квиза"""
        processing_text = "🤖 Анализирую ваши предпочтения и подбираю идеальные ароматы..."
        
        if hasattr(query_or_update, 'edit_message_text'):
            await query_or_update.edit_message_text(text=processing_text)
        
        try:
            # Создаем промпт для подбора ароматов на основе ответов квиза
            brand_name_factory_list = self.normalized_data.get('brand_name_factory', [])
            factory_analysis = self.normalized_data.get('factory_analysis', {})
            
            prompt = self._create_quiz_results_prompt(user_session.quiz_answers, brand_name_factory_list, factory_analysis)
            
            ai_response = await self._call_openrouter_api(prompt)
            
            keyboard = [
                [InlineKeyboardButton("🎯 Пройти квиз снова", callback_data="perfume_quiz")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            result_text = f"🎯 <b>Ваши персональные рекомендации:</b>\n\n{ai_response}"
            
            if hasattr(query_or_update, 'edit_message_text'):
                await query_or_update.edit_message_text(
                    text=result_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        
        except Exception as e:
            error_text = f"❌ Ошибка при подборе ароматов: {str(e)}"
            keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
            
            if hasattr(query_or_update, 'edit_message_text'):
                await query_or_update.edit_message_text(
                    text=error_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    
    def _create_quiz_results_prompt(self, quiz_answers: Dict[str, str], 
                                   brand_name_factory_list: List[str], 
                                   factory_analysis: Dict[str, Any]) -> str:
        """Создает промпт для результатов квиза"""
        
        # Ограничиваем список ароматов для экономии токенов
        limited_list = brand_name_factory_list[:300]
        
        # Формируем описание предпочтений пользователя
        preferences_text = []
        for key, value in quiz_answers.items():
            preferences_text.append(f"- {key}: {value}")
        
        # Краткая информация о топ фабриках
        top_factories = []
        for factory, data in list(factory_analysis.items())[:8]:
            top_factories.append(f"- {factory}: {data['perfume_count']} ароматов")
        
        prompt = f"""Ты - эксперт-парфюмер и персональный консультант по ароматам.

ПРЕДПОЧТЕНИЯ ПОЛЬЗОВАТЕЛЯ:
{chr(10).join(preferences_text)}

ЗАДАЧА: Подобрать из списка 5-7 наиболее подходящих композиций под эти предпочтения.

ДОСТУПНЫЕ АРОМАТЫ (бренд - название + фабрика):
{chr(10).join(limited_list)}

ИНФОРМАЦИЯ О ФАБРИКАХ:
{chr(10).join(top_factories)}

ИНСТРУКЦИИ:
1. Выбери 5-7 ароматов, максимально соответствующих предпочтениям
2. Для каждого аромата укажи, почему он подходит
3. Проанализируй фабрики и укажи, какие лучше исполняют эти композиции
4. Дай краткие описания выбранных ароматов
5. Расположи рекомендации по приоритету (от наиболее подходящего)

Ответ должен быть персонализированным и практичным."""

        return prompt
    
    async def _call_openrouter_api(self, prompt: str, max_tokens: int = 1000) -> str:
        """Вызывает OpenRouter API"""
        payload = {
            "model": self.openrouter_config['model'],
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
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
                value = parts[2]
                user_session.quiz_answers[key] = value
                user_session.quiz_step += 1
                await self._send_quiz_question(query, user_session)
            return BotState.QUIZ_IN_PROGRESS.value
        
        elif data == "stats":
            await self._show_statistics(query)
            return BotState.MAIN_MENU.value
        
        elif data == "factory_analysis":
            await self._show_factory_analysis(query)
            return BotState.MAIN_MENU.value
        
        elif data == "help":
            await self._show_help(query)
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
            f"<b>Топ-5 фабрик по количеству ароматов:</b>\n"
        )
        
        # Добавляем топ фабрик
        factory_analysis = stats_data.get('factory_analysis', {})
        sorted_factories = sorted(factory_analysis.items(), key=lambda x: x[1]['perfume_count'], reverse=True)
        
        for i, (factory, data) in enumerate(sorted_factories[:5], 1):
            text += f"{i}. {factory}: {data['perfume_count']} ароматов\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def _show_factory_analysis(self, query) -> None:
        """Показывает анализ фабрик"""
        factory_analysis = self.normalized_data.get('factory_analysis', {})
        
        text = "🏭 <b>Анализ фабрик</b>\n\n"
        
        sorted_factories = sorted(factory_analysis.items(), key=lambda x: x[1]['perfume_count'], reverse=True)
        
        for factory, data in sorted_factories[:10]:
            text += f"<b>{factory}</b>\n"
            text += f"  • Ароматов: {data['perfume_count']}\n"
            text += f"  • Брендов: {len(data['brands'])}\n"
            if data['quality_levels']:
                text += f"  • Качество: {', '.join(data['quality_levels'][:3])}\n"
            text += "\n"
        
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
            "❓ <b>Справка по боту</b>\n\n"
            "<b>🤔 Парфюмерный вопрос</b>\n"
            "Задайте любой вопрос о парфюмерии, и ИИ подберет подходящие ароматы из базы.\n\n"
            "<b>🎯 Подбор парфюма</b>\n"
            "Пройдите короткий квиз, и получите персональные рекомендации.\n\n"
            "<b>📖 Что за аромат?</b>\n"
            "Введите название аромата для получения подробной информации.\n\n"
            "<b>📊 Статистика</b>\n"
            "Посмотрите статистику по базе данных ароматов.\n\n"
            "<b>🏭 Анализ фабрик</b>\n"
            "Изучите информацию о фабриках-производителях.\n\n"
            "Бот использует ИИ для анализа и подбора ароматов из базы более чем 1200 позиций."
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
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
    # Здесь нужно будет указать реальные токены
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY_HERE"
    
    bot = PerfumeConsultantBot(BOT_TOKEN, OPENROUTER_API_KEY)
    application = bot.create_application()
    
    print("🤖 Парфюмерный консультант запущен!")
    print("📚 База данных загружена")
    print("🚀 Бот готов к работе...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()