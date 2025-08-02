#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiohttp
import asyncio
import logging
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .prompts import PromptTemplates

logger = logging.getLogger(__name__)

class AIProcessor:
    """Процессор для работы с ИИ через OpenRouter API"""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4-turbo-preview"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.session = None
        self.cooldowns = {}  # Кулдауны для пользователей
        
        logger.info(f"🧠 AIProcessor инициализирован с моделью: {model}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает HTTP сессию"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://perfume-bot.local",
                    "X-Title": "Perfume Bot"
                },
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return self.session
    
    async def call_openrouter_api(self, prompt: str, max_tokens: int = 4000) -> str:
        """Отправляет запрос к OpenRouter API"""
        try:
            session = await self._get_session()
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
            }
            
            logger.info(f"🤖 Отправляем запрос к OpenRouter API (модель: {self.model})")
            
            async with session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        
                        # Логируем использование токенов
                        usage = data.get('usage', {})
                        total_tokens = usage.get('total_tokens', 0)
                        logger.info(f"✅ Получен ответ от ИИ ({total_tokens} токенов)")
                        
                        return content
                    else:
                        logger.error("Неожиданная структура ответа от OpenRouter API")
                        return "Извините, произошла ошибка при получении ответа."
                        
                elif response.status == 429:
                    logger.warning("Rate limit превышен для OpenRouter API")
                    return "Извините, сервер перегружен. Попробуйте через несколько минут."
                    
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка OpenRouter API ({response.status}): {error_text}")
                    return "Извините, произошла ошибка при обращении к ИИ. Попробуйте позже."
                    
        except asyncio.TimeoutError:
            logger.error("Таймаут при обращении к OpenRouter API")
            return "Извините, превышено время ожидания ответа. Попробуйте позже."
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обращении к OpenRouter API: {e}")
            return "Извините, произошла неожиданная ошибка. Попробуйте позже."
    
    def create_perfume_question_prompt(self, user_question: str, perfumes_data: List[Dict[str, Any]]) -> str:
        """Создает промпт для вопроса о парфюмах"""
        return PromptTemplates.create_perfume_question_prompt(user_question, perfumes_data)
    
    def create_quiz_results_prompt(self, user_profile: Dict[str, Any], suitable_perfumes: List[Dict[str, Any]]) -> str:
        """Создает промпт для результатов квиза"""
        return PromptTemplates.create_quiz_results_prompt(user_profile, suitable_perfumes)
    
    def create_fragrance_info_prompt(self, query: str, matching_perfumes: List[Dict[str, Any]]) -> str:
        """Создает промпт для информации об аромате"""
        return PromptTemplates.create_fragrance_info_prompt(query, matching_perfumes)
    
    def process_ai_response_with_links(self, ai_response: str, db_manager) -> str:
        """Обрабатывает ответ ИИ и добавляет кликабельные ссылки"""
        try:
            # Ищем все артикулы в ответе в формате [Артикул: XXX]
            article_pattern = r'\[Артикул:\s*([A-Z0-9\-_]+)\]'
            matches = re.finditer(article_pattern, ai_response, re.IGNORECASE)
            
            processed_response = ai_response
            
            # Обрабатываем найденные артикулы
            for match in matches:
                article = match.group(1)
                
                # Получаем ссылку из БД
                url = db_manager.get_perfume_url_by_article(article)
                
                if url:
                    # Заменяем артикул на кликабельную ссылку "Приобрести"
                    article_mark = f"[Артикул: {article}]"
                    link_mark = f"[Приобрести]({url})"
                    processed_response = processed_response.replace(article_mark, link_mark)
                    
                    logger.info(f"🔗 Добавлена ссылка для артикула: {article}")
            
            # Форматируем текст для Telegram
            formatted_response = self._format_text_for_telegram(processed_response)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Ошибка при обработке ответа ИИ: {e}")
            return ai_response  # Возвращаем оригинальный ответ в случае ошибки
    
    def find_perfumes_by_query(self, query: str, all_perfumes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ищет парфюмы по запросу пользователя"""
        matching = []
        query_lower = query.lower()
        
        for perfume in all_perfumes:
            # Проверяем совпадения в названии, бренде, фабрике или артикуле
            if (query_lower in perfume['name'].lower() or
                query_lower in perfume['brand'].lower() or
                query_lower in perfume['factory'].lower() or
                query_lower in perfume['article'].lower()):
                matching.append(perfume)
        
        logger.info(f"🔍 По запросу '{query}' найдено {len(matching)} ароматов")
        return matching
    
    def is_api_cooldown_active(self, user_id: int) -> bool:
        """Проверяет, активен ли кулдаун для пользователя"""
        if user_id not in self.cooldowns:
            return False
        
        cooldown_end = self.cooldowns[user_id]
        return datetime.now() < cooldown_end
    
    def set_api_cooldown(self, user_id: int, seconds: int):
        """Устанавливает кулдаун для пользователя"""
        self.cooldowns[user_id] = datetime.now() + timedelta(seconds=seconds)
        logger.info(f"⏱️ Установлен кулдаун {seconds}с для пользователя {user_id}")
    
    def _format_text_for_telegram(self, text: str) -> str:
        """Форматирует текст для корректного отображения в Telegram"""
        # Ограничиваем длину сообщения (Telegram лимит ~4096 символов)
        if len(text) > 4000:
            text = text[:3900] + "\n\n📝 *Сообщение сокращено из-за ограничений Telegram*"
        
        # Экранируем специальные символы Markdown, которые могут вызвать проблемы
        # Но оставляем основные форматирующие символы
        text = text.replace('\\', '\\\\')
        text = text.replace('`', '\\`')
        
        # Убираем лишние пустые строки
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    async def close(self):
        """Закрывает HTTP сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("🔌 HTTP сессия AIProcessor закрыта")
    
    def __del__(self):
        """Деструктор"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            asyncio.create_task(self.session.close())