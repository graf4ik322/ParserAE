#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import time
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
import aiohttp
import json

logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """Структура ответа API"""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    usage: Optional[Dict[str, Any]] = None

class OpenRouterClient:
    """Улучшенный клиент для работы с OpenRouter API"""
    
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1/chat/completions", 
                 model: str = "anthropic/claude-3-haiku"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        
        # Настройки retry
        self.max_retries = 3
        self.retry_delay = 1  # секунды
        self.backoff_factor = 2
        
        # Настройки таймаутов
        self.connect_timeout = 10
        self.total_timeout = 60
        
        # Кэш для cooldown пользователей
        self.user_last_api_call: Dict[int, float] = {}
        self.api_cooldown_seconds = 30
        
        # Заголовки
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://perfume-bot.com',  # Опционально для аналитики
            'X-Title': 'Perfume Consultant Bot'
        }
        
        logger.info("✅ OpenRouter клиент инициализирован")
    
    def _check_cooldown(self, user_id: Optional[int]) -> Optional[str]:
        """Проверяет cooldown для пользователя"""
        if not user_id:
            return None
            
        current_time = time.time()
        last_call = self.user_last_api_call.get(user_id, 0)
        time_since_last = current_time - last_call
        
        if time_since_last < self.api_cooldown_seconds:
            remaining = self.api_cooldown_seconds - time_since_last
            return f"⏱️ Пожалуйста, подождите {remaining:.0f} секунд перед следующим запросом"
        
        return None
    
    def _update_cooldown(self, user_id: Optional[int]) -> None:
        """Обновляет время последнего запроса пользователя"""
        if user_id:
            self.user_last_api_call[user_id] = time.time()
    
    async def _make_request_with_retry(self, payload: Dict[str, Any]) -> APIResponse:
        """Выполняет запрос с retry механизмом"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(
                    total=self.total_timeout, 
                    connect=self.connect_timeout
                )
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    start_time = time.time()
                    
                    async with session.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload
                    ) as response:
                        request_time = time.time() - start_time
                        response_text = await response.text()
                        
                        logger.info(f"🌐 API запрос #{attempt + 1}: статус={response.status}, время={request_time:.2f}с")
                        
                        if response.status == 200:
                            try:
                                data = json.loads(response_text)
                                content = data['choices'][0]['message']['content']
                                usage = data.get('usage', {})
                                
                                logger.info(f"✅ API успешно: {len(content)} символов, токены: {usage}")
                                
                                return APIResponse(
                                    success=True,
                                    content=content,
                                    status_code=response.status,
                                    usage=usage
                                )
                                
                            except (KeyError, json.JSONDecodeError) as e:
                                error_msg = f"Ошибка парсинга ответа API: {e}"
                                logger.error(f"❌ {error_msg}")
                                return APIResponse(
                                    success=False,
                                    error=error_msg,
                                    status_code=response.status
                                )
                        
                        # Обработка различных HTTP ошибок
                        elif response.status == 429:  # Rate limiting
                            error_msg = "⏱️ Превышен лимит запросов API. Попробуйте позже."
                            logger.warning(f"⚠️ Rate limit: {response_text[:200]}")
                            
                            if attempt < self.max_retries - 1:
                                delay = self.retry_delay * (self.backoff_factor ** attempt) * 2  # Увеличиваем задержку для rate limit
                                logger.info(f"⏳ Ожидание {delay}с перед повтором...")
                                await asyncio.sleep(delay)
                                continue
                                
                            return APIResponse(
                                success=False,
                                error=error_msg,
                                status_code=response.status
                            )
                        
                        elif response.status == 401:  # Unauthorized
                            error_msg = "🔑 Ошибка авторизации API. Проверьте ключ."
                            logger.error(f"❌ Auth error: {response_text[:200]}")
                            return APIResponse(
                                success=False,
                                error=error_msg,
                                status_code=response.status
                            )
                        
                        elif response.status == 400:  # Bad Request
                            error_msg = "📝 Некорректный запрос к API. Попробуйте переформулировать."
                            logger.error(f"❌ Bad request: {response_text[:200]}")
                            return APIResponse(
                                success=False,
                                error=error_msg,
                                status_code=response.status
                            )
                        
                        elif response.status == 500:  # Server Error
                            error_msg = "🔧 Временные проблемы на сервере API."
                            logger.error(f"❌ Server error: {response_text[:200]}")
                            
                            if attempt < self.max_retries - 1:
                                delay = self.retry_delay * (self.backoff_factor ** attempt)
                                logger.info(f"⏳ Повтор через {delay}с...")
                                await asyncio.sleep(delay)
                                continue
                                
                            return APIResponse(
                                success=False,
                                error=error_msg,
                                status_code=response.status
                            )
                        
                        else:  # Другие ошибки
                            error_msg = f"❌ Неожиданная ошибка API: {response.status}"
                            logger.error(f"❌ Unexpected error {response.status}: {response_text[:200]}")
                            
                            if attempt < self.max_retries - 1:
                                delay = self.retry_delay * (self.backoff_factor ** attempt)
                                await asyncio.sleep(delay)
                                continue
                                
                            return APIResponse(
                                success=False,
                                error=error_msg,
                                status_code=response.status
                            )
            
            except asyncio.TimeoutError:
                error_msg = "⏰ Превышено время ожидания ответа API"
                logger.error(f"❌ Timeout на попытке {attempt + 1}")
                last_error = error_msg
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.backoff_factor ** attempt)
                    await asyncio.sleep(delay)
                    continue
            
            except aiohttp.ClientError as e:
                error_msg = f"🌐 Ошибка сетевого соединения: {str(e)}"
                logger.error(f"❌ Network error на попытке {attempt + 1}: {e}")
                last_error = error_msg
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.backoff_factor ** attempt)
                    await asyncio.sleep(delay)
                    continue
            
            except Exception as e:
                error_msg = f"🔥 Неожиданная ошибка: {str(e)}"
                logger.error(f"❌ Unexpected error на попытке {attempt + 1}: {e}")
                last_error = error_msg
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.backoff_factor ** attempt)
                    await asyncio.sleep(delay)
                    continue
        
        # Если все попытки исчерпаны
        return APIResponse(
            success=False,
            error=last_error or "❌ Не удалось выполнить запрос после всех попыток"
        )
    
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            max_tokens: int = 1000,
                            temperature: float = 0.7,
                            user_id: Optional[int] = None) -> APIResponse:
        """Выполняет запрос к OpenRouter API с полной обработкой ошибок"""
        
        # Проверяем cooldown
        cooldown_error = self._check_cooldown(user_id)
        if cooldown_error:
            return APIResponse(success=False, error=cooldown_error)
        
        # Подготавливаем payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        logger.info(f"🤖 Запрос к {self.model}: {len(messages)} сообщений, max_tokens={max_tokens}")
        
        # Выполняем запрос
        response = await self._make_request_with_retry(payload)
        
        # Обновляем cooldown при успешном запросе
        if response.success:
            self._update_cooldown(user_id)
        
        return response
    
    async def simple_completion(self, 
                              prompt: str, 
                              system_message: str = "", 
                              max_tokens: int = 1000,
                              temperature: float = 0.7,
                              user_id: Optional[int] = None) -> APIResponse:
        """Упрощенный метод для одного промпта"""
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            user_id=user_id
        )
    
    async def check_api_key(self) -> APIResponse:
        """Проверяет валидность API ключа"""
        try:
            balance_url = "https://openrouter.ai/api/v1/auth/key"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(balance_url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            content="API ключ действителен",
                            usage=data
                        )
                    else:
                        return APIResponse(
                            success=False,
                            error="API ключ недействителен",
                            status_code=response.status
                        )
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Ошибка при проверке API ключа: {str(e)}"
            )