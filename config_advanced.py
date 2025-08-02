#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class ConfigAdvanced:
    """Расширенная конфигурация приложения с поддержкой разных БД"""
    
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
        if admin_user_id_str == '123456789' or admin_user_id_str == '0':
            raise ValueError("ADMIN_USER_ID не установлен в переменных окружения")
        self.admin_user_id = int(admin_user_id_str)
        
        # Настройки базы данных
        self.db_type = os.getenv('DB_TYPE', 'sqlite')  # sqlite, postgresql, mysql
        
        if self.db_type == 'sqlite':
            # SQLite - файловая БД, не требует логина/пароля
            self.database_path = os.getenv('DATABASE_PATH', 'data/perfumes.db')
            self.db_host = None
            self.db_port = None
            self.db_name = None
            self.db_user = None
            self.db_password = None
            
        elif self.db_type in ['postgresql', 'mysql']:
            # PostgreSQL/MySQL - требуют логин/пароль
            self.db_host = os.getenv('DB_HOST', 'localhost')
            self.db_port = int(os.getenv('DB_PORT', '5432' if self.db_type == 'postgresql' else '3306'))
            self.db_name = os.getenv('DB_NAME', 'perfumes_db')
            self.db_user = os.getenv('DB_USER', '')
            self.db_password = os.getenv('DB_PASSWORD', '')
            
            # Проверяем обязательные параметры для серверных БД
            if not self.db_user:
                raise ValueError(f"DB_USER не установлен для {self.db_type}")
            if not self.db_password:
                raise ValueError(f"DB_PASSWORD не установлен для {self.db_type}")
                
            self.database_path = None
            
        else:
            raise ValueError(f"Неподдерживаемый тип БД: {self.db_type}")
        
        # API настройки
        self.api_cooldown_seconds = int(os.getenv('API_COOLDOWN_SECONDS', '30'))
        self.max_tokens_per_request = int(os.getenv('MAX_TOKENS_PER_REQUEST', '8000'))
        
        # Парсер настройки
        self.parse_interval_hours = int(os.getenv('PARSE_INTERVAL_HOURS', '6'))
        self.parser_max_workers = int(os.getenv('PARSER_MAX_WORKERS', '3'))
        
        # Режим без лимитов
        self.use_all_perfumes = True
        self.no_limits_mode = True
        
        # Настройки OpenRouter
        self.openrouter_model = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4-turbo-preview')
        self.openrouter_base_url = 'https://openrouter.ai/api/v1'
        
        # Парсер настройки
        self.aroma_euro_base_url = 'https://aroma-euro.ru'
        self.aroma_euro_catalog_url = 'https://aroma-euro.ru/perfume/'
        
        # Настройки кэширования
        self.cache_ttl_seconds = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
        
        # Логирование
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'perfume_bot.log')
        
        # Дополнительные настройки
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
    
    def get_database_url(self):
        """Возвращает строку подключения к БД"""
        if self.db_type == 'sqlite':
            return f"sqlite:///{self.database_path}"
        elif self.db_type == 'postgresql':
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.db_type == 'mysql':
            return f"mysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            raise ValueError(f"Неподдерживаемый тип БД: {self.db_type}")
    
    def __str__(self):
        """Строковое представление конфигурации"""
        db_info = f"🗄️ Database: {self.db_type}"
        if self.db_type == 'sqlite':
            db_info += f" ({self.database_path})"
        else:
            db_info += f" ({self.db_host}:{self.db_port}/{self.db_name})"
        
        return f"""
📋 Расширенная конфигурация Perfume Bot:
├── 🤖 Bot Token: {'✅ установлен' if self.bot_token else '❌ не установлен'}
├── 🧠 OpenRouter API: {'✅ установлен' if self.openrouter_api_key else '❌ не установлен'}
├── 👤 Admin ID: {self.admin_user_id}
├── {db_info}
├── ⏱️ API Cooldown: {self.api_cooldown_seconds}s
├── 🎯 Max Tokens: {self.max_tokens_per_request}
├── 🔄 Parse Interval: {self.parse_interval_hours}h
├── 🚀 No Limits Mode: {'✅ включен' if self.no_limits_mode else '❌ выключен'}
└── 📝 Log Level: {self.log_level}
        """.strip()

# Пример .env файла для разных БД
ENV_EXAMPLES = """
# Для SQLite (текущий проект)
DB_TYPE=sqlite
DATABASE_PATH=data/perfumes.db

# Для PostgreSQL
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=perfumes_db
DB_USER=perfume_user
DB_PASSWORD=your_secure_password

# Для MySQL
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=perfumes_db
DB_USER=perfume_user
DB_PASSWORD=your_secure_password
"""