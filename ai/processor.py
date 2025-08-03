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
                timeout=aiohttp.ClientTimeout(total=90)  # 90 секунд для оптимизации производительности
            )
        return self.session
    
    async def call_openrouter_api(self, prompt: str, max_tokens: int = 4000, max_retries: int = 3) -> str:
        """Отправляет запрос к OpenRouter API с retry логикой"""
        
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
        
        for attempt in range(max_retries):
            try:
                session = await self._get_session()
                
                logger.info(f"🤖 Отправляем запрос к OpenRouter API (модель: {self.model}, попытка {attempt + 1}/{max_retries})")
                
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
                            if attempt == max_retries - 1:
                                return "Извините, произошла ошибка при получении ответа."
                            continue
                            
                    elif response.status == 429:
                        logger.warning(f"Rate limit превышен для OpenRouter API (попытка {attempt + 1}/{max_retries})")
                        if attempt == max_retries - 1:
                            return "Извините, сервер перегружен. Попробуйте через несколько минут."
                        # Минимальная задержка при rate limit для быстрого ответа
                        await asyncio.sleep(0.1)  # Уменьшенная задержка для быстрого ответа
                        continue
                        
                    elif response.status >= 500:
                        # Серверные ошибки - можно повторить попытку
                        error_text = await response.text()
                        logger.warning(f"Серверная ошибка OpenRouter API ({response.status}): {error_text[:200]} (попытка {attempt + 1}/{max_retries})")
                        if attempt == max_retries - 1:
                            return "Извините, произошла ошибка на сервере ИИ. Попробуйте позже."
                        await asyncio.sleep(0.1)  # Минимальная пауза при серверных ошибках
                        continue
                        
                    else:
                        # Клиентские ошибки - не повторяем
                        error_text = await response.text()
                        logger.error(f"Ошибка OpenRouter API ({response.status}): {error_text}")
                        return "Извините, произошла ошибка при обращении к ИИ. Попробуйте позже."
                        
            except asyncio.TimeoutError:
                logger.warning(f"Таймаут при обращении к OpenRouter API (попытка {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return "Извините, превышено время ожидания ответа. Попробуйте позже."
                continue
                
            except aiohttp.ClientError as e:
                logger.warning(f"Ошибка соединения с OpenRouter API: {e} (попытка {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return "Извините, проблемы с соединением. Попробуйте позже."
                await asyncio.sleep(0.1)  # Минимальная задержка при ошибках соединения
                continue
                
            except Exception as e:
                logger.error(f"Неожиданная ошибка при обращении к OpenRouter API: {e}")
                return "Извините, произошла неожиданная ошибка. Попробуйте позже."
        
        # Если все попытки исчерпаны
        return "Извините, не удалось получить ответ от ИИ. Попробуйте позже."
    
    def create_perfume_question_prompt(self, user_question: str, perfumes_data: List[Dict[str, Any]]) -> str:
        """Создает промпт для вопроса о парфюмах"""
        return PromptTemplates.create_perfume_question_prompt(user_question, perfumes_data)
    
    def create_quiz_results_prompt(self, user_profile: Dict[str, Any], suitable_perfumes: List[Dict[str, Any]]) -> str:
        """Создает промпт для результатов квиза"""
        return PromptTemplates.create_quiz_results_prompt(user_profile, suitable_perfumes)
    

    
    def process_ai_response_with_links(self, ai_response: str, db_manager) -> str:
        """Обрабатывает ответ ИИ и добавляет кликабельные ссылки"""
        try:
            processed_response = ai_response
            
            # Ищем все артикулы в ответе в различных форматах
            patterns = [
                r'Артикул:\s*([A-Z0-9\\\\\-_\.\s]+?)(?=\s|$|\n)',  # Артикул: XXX (обычный формат, включая слеши)
                r'\[Артикул:\s*([A-Z0-9\\\\\-_\.\s]+?)\]',  # [Артикул: XXX] (в скобках)
            ]
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, processed_response, re.IGNORECASE))
                
                # Обрабатываем найденные артикулы в обратном порядке чтобы не сбить позиции
                for match in reversed(matches):
                    article = match.group(1)
                    full_match = match.group(0)
                    
                    # Получаем ссылку из БД
                    url = db_manager.get_perfume_url_by_article(article)
                    
                    if url:
                        # Исправляем URL если содержит /product/ вместо /parfume/
                        if '/product/' in url:
                            url = url.replace('/product/', '/parfume/')
                            
                        # Заменяем на кликабельную ссылку "Заказать"
                        link_mark = f"[📦 Заказать]({url})"
                        processed_response = processed_response.replace(full_match, link_mark)
                        
                        logger.info(f"🔗 Добавлена ссылка для артикула: {article}")
                    else:
                        logger.warning(f"⚠️ Не найден URL для артикула: {article}")
            
            # ИИ теперь возвращает уже готовый для Telegram формат, поэтому просто возвращаем результат
            return processed_response
            
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
        """Упрощенное форматирование - ИИ возвращает готовый для Telegram формат"""
        # Только ограничение длины и уборка лишних строк
        if len(text) > 4000:
            text = text[:3900] + "\n\n📝 *Сообщение сокращено*"
        
        # Убираем лишние пустые строки
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
# Сложные методы экранирования удалены - ИИ возвращает готовый формат
    
    async def close(self):
        """Закрывает HTTP сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("🔌 HTTP сессия AIProcessor закрыта")
    
    async def check_api_status(self) -> Dict[str, Any]:
        """Проверяет состояние API ключа"""
        status = {
            'api_key_valid': False,
            'api_key_masked': self.api_key[:8] + "..." + self.api_key[-4:] if len(self.api_key) > 12 else "***",
            'model': self.model,
            'base_url': self.base_url,
            'last_check': datetime.now().isoformat(),
            'response_time': None,
            'error': None,
            'test_successful': False
        }
        
        try:
            start_time = datetime.now()
            
            # Отправляем тестовый запрос
            session = await self._get_session()
            
            test_payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user", 
                        "content": "Ответь одним словом: работает"
                    }
                ],
                "max_tokens": 10,
                "temperature": 0
            }
            
            async with session.post(f"{self.base_url}/chat/completions", json=test_payload) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                status['response_time'] = round(response_time, 2)
                
                if response.status == 200:
                    data = await response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        test_response = data['choices'][0]['message']['content'].strip().lower()
                        status['api_key_valid'] = True
                        status['test_successful'] = 'работа' in test_response or 'работ' in test_response
                        
                        # Дополнительная информация из ответа
                        if 'usage' in data:
                            status['tokens_used'] = data['usage'].get('total_tokens', 0)
                        
                        if 'model' in data:
                            status['actual_model'] = data['model']
                    else:
                        status['error'] = "Некорректный формат ответа API"
                elif response.status == 401:
                    status['error'] = "Неверный API ключ (401 Unauthorized)"
                elif response.status == 429:
                    status['error'] = "Превышен лимит запросов (429 Too Many Requests)"
                elif response.status == 403:
                    status['error'] = "Доступ запрещен (403 Forbidden)"
                else:
                    error_text = await response.text()
                    status['error'] = f"HTTP {response.status}: {error_text[:200]}"
                    
        except asyncio.TimeoutError:
            status['error'] = "Превышено время ожидания ответа"
        except aiohttp.ClientError as e:
            status['error'] = f"Ошибка соединения: {str(e)}"
        except Exception as e:
            status['error'] = f"Неизвестная ошибка: {str(e)}"
        
        return status

    async def process_message(self, message: str, user_id: int = None) -> str:
        """Обрабатывает сообщение и возвращает ответ от ИИ"""
        try:
            # Проверяем кулдаун пользователя
            if user_id and self.is_api_cooldown_active(user_id):
                return "⏱️ Пожалуйста, подождите перед следующим запросом к ИИ."
            
            # Отправляем запрос к ИИ с таймаутом
            try:
                response = await asyncio.wait_for(
                    self.call_openrouter_api(message),
                    timeout=60.0  # 60 секунд максимум для ИИ-запроса
                )
            except asyncio.TimeoutError:
                logger.error(f"Тайм-аут при запросе к ИИ для пользователя {user_id}")
                return "⏳ Запрос к ИИ занял слишком много времени. Попробуйте упростить вопрос или повторите позже."
            
            # Устанавливаем кулдаун после успешного запроса
            if user_id:
                self.set_api_cooldown(user_id, 30)  # 30 секунд кулдаун
            
            # Форматируем ответ для Telegram
            formatted_response = self._format_text_for_telegram(response)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            return "❌ Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."

    def search_perfumes(self, query: str, perfumes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ищет парфюмы по запросу пользователя"""
        matching = []
        query_lower = query.lower()
        
        for perfume in perfumes_data:
            # Проверяем совпадения в названии, бренде, фабрике или артикуле
            if (query_lower in perfume['name'].lower() or
                query_lower in perfume['brand'].lower() or
                query_lower in perfume['factory'].lower() or
                query_lower in perfume['article'].lower()):
                matching.append(perfume)
        
        logger.info(f"🔍 По запросу '{query}' найдено {len(matching)} ароматов")
        return matching

    def __del__(self):
        """Деструктор"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            asyncio.create_task(self.session.close())