#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class QuestionHandler:
    """Обработчик парфюмерных вопросов пользователей"""
    
    def __init__(self, api_client, data_manager, ai_prompts, prompt_limits):
        self.api_client = api_client
        self.data_manager = data_manager
        self.ai_prompts = ai_prompts
        self.prompt_limits = prompt_limits
        
    async def handle_perfume_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Инициирует диалог для парфюмерного вопроса"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "❓ <b>Парфюмерный консультант</b>\n\n"
            "Задайте мне любой вопрос о парфюмерии, и я подберу для вас идеальные ароматы!\n\n"
            "💡 <b>Примеры вопросов:</b>\n"
            "• <i>Хочу свежий аромат на лето</i>\n"
            "• <i>Нужен дорогой парфюм для особого случая</i>\n"
            "• <i>Что-то похожее на Tom Ford Lost Cherry</i>\n"
            "• <i>Стойкий аромат для работы</i>\n\n"
            "✍️ Напишите ваш вопрос:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return 4  # BotState.WAITING_USER_INPUT.value
    
    async def process_perfume_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает вопрос пользователя через ИИ с улучшенной отладкой"""
        user_question = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"🤔 Получен вопрос от пользователя {user_id}: '{user_question[:50]}...'")
        
        # Отправляем сообщение о обработке
        processing_msg = await update.message.reply_text("🤖 Анализирую ваш вопрос и подбираю идеальные ароматы...")
        
        try:
            # Шаг 1: Получаем данные
            logger.info("📋 Шаг 1: Получение данных для промпта...")
            
            name_factory_list = self.data_manager.get_enhanced_perfume_list()
            if not name_factory_list:
                logger.error("❌ Не удалось получить список парфюмов")
                raise Exception("Не удалось загрузить базу данных ароматов")
            
            factory_analysis = self.data_manager.get_factory_analysis()
            logger.info(f"✅ Данные получены: {len(name_factory_list)} ароматов, {len(factory_analysis)} фабрик")
            
            # Шаг 2: Создаем промпт
            logger.info("🔧 Шаг 2: Создание промпта...")
            
            try:
                prompt = self.ai_prompts.create_perfume_question_prompt(
                    user_question=user_question,
                    perfume_list=name_factory_list[:200],  # Ограничиваем для стабильности
                    factory_analysis=factory_analysis,
                    limit_perfumes=200,
                    limit_factories=10
                )
                logger.info(f"✅ Промпт создан, длина: {len(prompt)} символов")
            except Exception as e:
                logger.error(f"❌ Ошибка создания промпта: {e}")
                raise Exception(f"Ошибка подготовки запроса: {str(e)}")
            
            # Шаг 3: Отправляем запрос к API
            logger.info("🌐 Шаг 3: Отправка запроса к OpenRouter API...")
            
            try:
                # Используем новый API клиент
                system_message = self.ai_prompts.create_system_message()
                api_response = await self.api_client.simple_completion(
                    prompt=prompt,
                    system_message=system_message,
                    max_tokens=self.prompt_limits.MAX_TOKENS_QUESTION,
                    temperature=self.prompt_limits.TEMP_BALANCED,
                    user_id=user_id
                )
                
                if not api_response.success:
                    logger.error(f"❌ API ошибка: {api_response.error}")
                    raise Exception(api_response.error)
                
                ai_response = api_response.content
                logger.info(f"✅ API ответ получен, длина: {len(ai_response)} символов")
                
            except Exception as e:
                logger.error(f"❌ Ошибка API запроса: {e}")
                raise Exception(f"Ошибка получения ответа от ИИ: {str(e)}")
            
            # Шаг 4: Обрабатываем ответ
            logger.info("🔧 Шаг 4: Обработка ответа...")
            
            try:
                processed_response = self.data_manager.process_ai_response_with_urls(ai_response)
                logger.info("✅ Ответ обработан и ссылки добавлены")
            except Exception as e:
                logger.error(f"❌ Ошибка обработки ответа: {e}")
                # Используем оригинальный ответ без обработки ссылок
                processed_response = self._format_text_for_telegram(ai_response)
                logger.info("⚠️ Используется ответ без обработки ссылок")
            
            # Шаг 5: Удаляем сообщение о обработке
            try:
                await processing_msg.delete()
            except Exception as e:
                logger.warning(f"⚠️ Не удалось удалить сообщение о обработке: {e}")
            
            # Шаг 6: Отправляем ответ
            logger.info("📤 Шаг 6: Отправка ответа пользователю...")
            
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
            
            logger.info("✅ Ответ успешно отправлен пользователю")
            return 0  # BotState.MAIN_MENU.value
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в process_perfume_question: {str(e)}")
            
            # Удаляем сообщение о обработке
            try:
                await processing_msg.delete()
            except:
                pass
            
            # Определяем тип ошибки и отправляем соответствующее сообщение
            if "rate-limited" in str(e).lower() or "429" in str(e):
                error_text = (
                    "⏱️ Слишком много запросов. Пожалуйста, подождите несколько секунд и попробуйте снова.\n\n"
                    "💡 Попробуйте:\n"
                    "• Подождать 30-60 секунд\n"
                    "• Пройти квиз для подбора ароматов\n"
                    "• Вернуться в главное меню"
                )
            elif "500" in str(e) or "server" in str(e).lower():
                error_text = (
                    "🔧 Временные технические проблемы на сервере.\n\n"
                    "💡 Попробуйте:\n"
                    "• Повторить запрос через минуту\n"
                    "• Пройти квиз для подбора ароматов\n"
                    "• Вернуться в главное меню"
                )
            elif "api" in str(e).lower() or "ключ" in str(e).lower():
                error_text = (
                    "🔑 Проблема с API сервисом.\n\n"
                    "💡 Попробуйте:\n"
                    "• Повторить запрос через несколько минут\n"
                    "• Пройти квиз для подбора ароматов\n"
                    "• Обратиться к администратору"
                )
            else:
                error_text = (
                    "❌ Извините, произошла техническая ошибка при обработке вашего вопроса.\n\n"
                    "💡 Попробуйте:\n"
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
            
            return 0  # BotState.MAIN_MENU.value
    
    def _split_message(self, text: str, max_length: int = 4000) -> list:
        """Разбивает длинное сообщение на части"""
        if len(text) <= max_length:
            return [text]
        
        parts = []
        current_part = ""
        
        # Разбиваем по абзацам
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_part) + len(paragraph) + 2 <= max_length:
                if current_part:
                    current_part += "\n\n" + paragraph
                else:
                    current_part = paragraph
            else:
                if current_part:
                    parts.append(current_part)
                current_part = paragraph
                
                # Если один абзац слишком длинный, разбиваем по предложениям
                if len(current_part) > max_length:
                    sentences = current_part.split('. ')
                    current_part = ""
                    
                    for sentence in sentences:
                        if len(current_part) + len(sentence) + 2 <= max_length:
                            if current_part:
                                current_part += ". " + sentence
                            else:
                                current_part = sentence
                        else:
                            if current_part:
                                parts.append(current_part + ".")
                            current_part = sentence
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    def _format_text_for_telegram(self, text: str) -> str:
        """Форматирует текст для Telegram"""
        # Заменяем markdown на HTML
        text = text.replace('**', '<b>').replace('**', '</b>')
        text = text.replace('*', '<i>').replace('*', '</i>')
        
        # Убираем лишние переносы строк
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        
        return text