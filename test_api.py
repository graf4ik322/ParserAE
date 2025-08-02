#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json
import logging
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_openrouter_api():
    """Тестирует OpenRouter API напрямую"""
    config = Config()
    
    api_key = config.openrouter_api_key
    model = config.openrouter_model
    
    logger.info(f"🔑 API Key: {api_key[:20]}...")
    logger.info(f"🤖 Model: {model}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://perfume-bot.local",
        "X-Title": "Perfume Bot"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Привет! Как дела?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info("📡 Отправляем запрос к OpenRouter API...")
            
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                logger.info(f"📊 Статус ответа: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Успешный ответ!")
                    logger.info(f"📝 Ответ: {data}")
                    
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        logger.info(f"💬 Содержание: {content}")
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка {response.status}: {error_text}")
                    
                    # Попробуем получить больше информации об ошибке
                    try:
                        error_data = json.loads(error_text)
                        logger.error(f"🔍 Детали ошибки: {json.dumps(error_data, indent=2)}")
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"❌ Исключение: {e}")

if __name__ == "__main__":
    asyncio.run(test_openrouter_api())