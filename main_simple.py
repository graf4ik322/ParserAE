#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import signal
import sys
from datetime import datetime

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

class PerfumeBotSimple:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager(self.config.database_path)
        self.ai = AIProcessor(self.config.openrouter_api_key, self.config.openrouter_model)
        self.quiz = QuizSystem(self.db, self.ai)
        self.auto_parser = AutoParser(self.db)
        
        logger.info("🤖 Perfume Bot Simple инициализирован")

    async def test_ai_response(self):
        """Тестирует ответ AI"""
        try:
            test_prompt = "Расскажи кратко о парфюмах"
            response = await self.ai.call_openrouter_api(test_prompt, max_tokens=200)
            logger.info(f"🤖 AI ответ: {response}")
            return response
        except Exception as e:
            logger.error(f"❌ Ошибка AI: {e}")
            return None

    async def run(self):
        """Запускает упрощенную версию бота"""
        logger.info("🚀 Perfume Bot Simple запущен!")
        
        # Тестируем AI
        await self.test_ai_response()
        
        logger.info("✅ Тестирование завершено")

def main():
    """Главная функция"""
    try:
        bot = PerfumeBotSimple()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()