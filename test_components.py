#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from config import Config
from database.manager import DatabaseManager
from ai.processor import AIProcessor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_components():
    """Тестирует основные компоненты приложения"""
    try:
        # Инициализируем конфигурацию
        logger.info("🔧 Инициализация конфигурации...")
        config = Config()
        logger.info(f"✅ Конфигурация загружена. Модель: {config.openrouter_model}")
        
        # Инициализируем базу данных
        logger.info("🗄️ Инициализация базы данных...")
        db = DatabaseManager(config.database_path)
        logger.info("✅ База данных инициализирована")
        
        # Инициализируем AI процессор
        logger.info("🧠 Инициализация AI процессора...")
        ai = AIProcessor(config.openrouter_api_key, config.openrouter_model)
        logger.info("✅ AI процессор инициализирован")
        
        # Тестируем простой запрос к AI
        logger.info("🤖 Тестирование AI запроса...")
        test_prompt = "Привет! Как дела?"
        response = await ai.call_openrouter_api(test_prompt, max_tokens=100)
        logger.info(f"✅ AI ответ получен: {response[:100]}...")
        
        logger.info("🎉 Все компоненты работают корректно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_components())