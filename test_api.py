#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.api.openrouter_client import OpenRouterClient, APIResponse
from config import OPENROUTER_API_KEY, OPENROUTER_CONFIG
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_api():
    """Тестирует подключение к OpenRouter API"""
    print("🧪 Тестирование OpenRouter API...")
    
    # Создаем клиент
    client = OpenRouterClient(
        api_key=OPENROUTER_API_KEY,
        model=OPENROUTER_CONFIG['model']
    )
    
    # Тест 1: Проверка API ключа
    print("\n1️⃣ Проверка API ключа...")
    key_check = await client.check_api_key()
    if key_check.success:
        print("✅ API ключ действителен")
        if key_check.usage:
            print(f"📊 Данные ключа: {key_check.usage}")
    else:
        print(f"❌ Проблема с API ключом: {key_check.error}")
        return
    
    # Тест 2: Простой запрос
    print("\n2️⃣ Тестовый запрос к AI...")
    test_response = await client.simple_completion(
        prompt="Привет! Напиши короткое приветствие на русском языке.",
        system_message="Ты - дружелюбный помощник. Отвечай кратко и по делу.",
        max_tokens=100,
        temperature=0.7
    )
    
    if test_response.success:
        print("✅ API работает!")
        print(f"📝 Ответ: {test_response.content}")
        if test_response.usage:
            print(f"📊 Использование токенов: {test_response.usage}")
    else:
        print(f"❌ Ошибка API: {test_response.error}")
        return
    
    # Тест 3: Парфюмерный запрос
    print("\n3️⃣ Тестовый парфюмерный запрос...")
    perfume_response = await client.simple_completion(
        prompt="Посоветуй мне свежий летний аромат для мужчин",
        system_message="Ты - эксперт парфюмер. Дай краткий совет.",
        max_tokens=200,
        temperature=0.7
    )
    
    if perfume_response.success:
        print("✅ Парфюмерный запрос работает!")
        print(f"📝 Ответ: {perfume_response.content}")
    else:
        print(f"❌ Ошибка парфюмерного запроса: {perfume_response.error}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_api())