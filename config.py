#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# OpenRouter API Key  
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', 'YOUR_OPENROUTER_API_KEY_HERE')

# Настройки OpenRouter
OPENROUTER_CONFIG = {
    'base_url': 'https://openrouter.ai/api/v1/chat/completions',
    'model': 'anthropic/claude-3-haiku',  # Экономичная модель
    'max_tokens': 1000,
    'temperature': 0.7
}

# Настройки бота
BOT_CONFIG = {
    'max_message_length': 4096,
    'quiz_timeout': 300,  # 5 минут на квиз
    'cache_size': 100,    # Количество сессий в кэше
}

# Пути к файлам данных
DATA_FILES = {
    'names_only': 'names_only.json',
    'brand_name': 'brand_name.json',
    'name_factory': 'name_factory.json',
    'brand_name_factory': 'brand_name_factory.json',
    'full_data_compact': 'full_data_compact.json',
    'factory_analysis': 'factory_analysis.json',
    'quiz_reference': 'quiz_reference.json'
}

# Ограничения для оптимизации LLM запросов
LLM_LIMITS = {
    'question_list_limit': 200,     # Ароматов в списке для вопросов
    'quiz_list_limit': 300,         # Ароматов в списке для квиза
    'factory_summary_limit': 10,    # Фабрик в сводке
    'top_factories_limit': 8        # Топ фабрик для анализа
}