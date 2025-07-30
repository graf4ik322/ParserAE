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

# Admin User ID (получить можно через @userinfobot)
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))  # Замените на ваш Telegram User ID

# Настройки OpenRouter
OPENROUTER_CONFIG = {
    'base_url': 'https://openrouter.ai/api/v1/chat/completions',
    'model': os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-haiku'),
    'max_tokens': int(os.getenv('OPENROUTER_MAX_TOKENS', '1000')),
    'temperature': float(os.getenv('OPENROUTER_TEMPERATURE', '0.7'))
}

# Настройки бота
BOT_CONFIG = {
    'max_message_length': int(os.getenv('MAX_MESSAGE_LENGTH', '4096')),
    'quiz_timeout': int(os.getenv('QUIZ_TIMEOUT', '300')),  # 5 минут на квиз
    'cache_size': int(os.getenv('CACHE_SIZE', '100')),    # Количество сессий в кэше
}

# Настройки форматирования текста
TEXT_FORMATTING = {
    'max_emojis_per_message': int(os.getenv('MAX_EMOJIS_PER_MESSAGE', '4')),
    'max_lines_per_block': int(os.getenv('MAX_LINES_PER_BLOCK', '6')),
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
    'question_list_limit': int(os.getenv('QUESTION_LIST_LIMIT', '200')),     # Ароматов в списке для вопросов
    'quiz_list_limit': int(os.getenv('QUIZ_LIST_LIMIT', '300')),         # Ароматов в списке для квиза
    'factory_summary_limit': int(os.getenv('FACTORY_SUMMARY_LIMIT', '10')),    # Фабрик в сводке
    'top_factories_limit': int(os.getenv('TOP_FACTORIES_LIMIT', '8'))        # Топ фабрик для анализа
}