#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    def __init__(self):
        # Telegram Bot
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        if not self.bot_token or self.bot_token == 'your_telegram_bot_token_here':
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
        
        # OpenRouter API
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY', '')
        if not self.openrouter_api_key or self.openrouter_api_key == 'your_openrouter_api_key_here':
            raise ValueError("OPENROUTER_API_KEY не установлен в переменных окружения")
        
        # Админ
        admin_user_id_str = os.getenv('ADMIN_USER_ID', '0')
        if admin_user_id_str == '0' or not admin_user_id_str:
            raise ValueError("ADMIN_USER_ID не установлен в переменных окружения")
        
        try:
            self.admin_user_id = int(admin_user_id_str)
        except ValueError:
            raise ValueError("ADMIN_USER_ID должен быть числом")
        
        # База данных
        self.database_path = os.getenv('DATABASE_PATH', 'data/perfumes.db')
        
        # API настройки
        self.api_cooldown_seconds = int(os.getenv('API_COOLDOWN_SECONDS', '30'))
        self.max_tokens_per_request = int(os.getenv('MAX_TOKENS_PER_REQUEST', '8000'))
        
        # Парсер настройки
        self.parse_interval_hours = int(os.getenv('PARSE_INTERVAL_HOURS', '6'))
        self.parser_max_workers = int(os.getenv('PARSER_MAX_WORKERS', '3'))
        
        # Режим без лимитов (согласно техническому заданию)
        self.use_all_perfumes = True
        self.no_limits_mode = True
        
        # Настройки OpenRouter
        self.openrouter_model = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4-turbo-preview')
        self.openrouter_base_url = 'https://openrouter.ai/api/v1'
        
        # Парсер настройки
        self.aroma_euro_base_url = 'https://aroma-euro.ru'
        self.aroma_euro_catalog_url = 'https://aroma-euro.ru/perfume/'
        
        # Настройки кэширования
        self.cache_ttl_seconds = int(os.getenv('CACHE_TTL_SECONDS', '3600'))  # 1 час
        
        # Логирование
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'perfume_bot.log')
        
        # Дополнительные настройки
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
    def validate(self):
        """Валидация конфигурации"""
        errors = []
        
        if not self.bot_token:
            errors.append("TELEGRAM_BOT_TOKEN не может быть пустым")
        
        if not self.openrouter_api_key:
            errors.append("OPENROUTER_API_KEY не может быть пустым")
        
        if self.admin_user_id <= 0:
            errors.append("ADMIN_USER_ID должен быть положительным числом")
        
        if self.api_cooldown_seconds < 0:
            errors.append("API_COOLDOWN_SECONDS не может быть отрицательным")
        
        if self.max_tokens_per_request <= 0:
            errors.append("MAX_TOKENS_PER_REQUEST должен быть положительным")
        
        if errors:
            raise ValueError("Ошибки конфигурации:\n" + "\n".join(errors))
        
        return True
    
    def __str__(self):
        """Строковое представление конфигурации (без секретов)"""
        return f"""
📋 Конфигурация Perfume Bot:
├── 🤖 Bot Token: {'✅ установлен' if self.bot_token else '❌ не установлен'}
├── 🧠 OpenRouter API: {'✅ установлен' if self.openrouter_api_key else '❌ не установлен'}
├── 👤 Admin ID: {self.admin_user_id}
├── 🗄️ Database: {self.database_path}
├── ⏱️ API Cooldown: {self.api_cooldown_seconds}s
├── 🎯 Max Tokens: {self.max_tokens_per_request}
├── 🔄 Parse Interval: {self.parse_interval_hours}h
├── 🚀 No Limits Mode: {'✅ включен' if self.no_limits_mode else '❌ выключен'}
└── 📝 Log Level: {self.log_level}
        """.strip()