#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

@dataclass
class BotConfig:
    """Конфигурация Telegram бота"""
    token: str
    admin_user_id: int
    max_message_length: int = 4096
    quiz_timeout: int = 300
    cache_size: int = 100

@dataclass
class APIConfig:
    """Конфигурация OpenRouter API"""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    model: str = "deepseek/deepseek-chat-v3-0324:free"
    max_tokens: int = 1500
    temperature: float = 0.7
    max_retries: int = 3
    retry_delay: int = 1
    cooldown_seconds: int = 30

@dataclass
class DataConfig:
    """Конфигурация данных"""
    base_dir: Path
    raw_dir: Path
    processed_dir: Path
    cache_dir: Path
    
    # Файлы данных
    perfume_catalog_url: str = "https://aroma-euro.ru/sitemap.xml"
    update_interval_hours: int = 24
    cache_expiry_days: int = 7

@dataclass
class ParserConfig:
    """Конфигурация парсера"""
    max_concurrent_requests: int = 10
    request_delay: float = 1.0
    timeout: int = 30
    retry_attempts: int = 3
    user_agent: str = "Mozilla/5.0 (compatible; PerfumeBot/2.0)"

@dataclass
class LoggingConfig:
    """Конфигурация логирования"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_dir: Path = Path("logs")

class Config:
    """Главный класс конфигурации"""
    
    def __init__(self):
        # Определяем базовые пути
        self.project_root = Path(__file__).parent.parent.parent
        self.data_base_dir = self.project_root / "perfume_bot" / "data"
        
        # Создаем необходимые директории
        self._create_directories()
        
        # Инициализируем конфигурации
        self.bot = self._init_bot_config()
        self.api = self._init_api_config()
        self.data = self._init_data_config()
        self.parser = self._init_parser_config()
        self.logging = self._init_logging_config()
        
        # Валидация
        self._validate_config()
    
    def _create_directories(self):
        """Создает необходимые директории"""
        directories = [
            self.data_base_dir / "raw",
            self.data_base_dir / "processed", 
            self.data_base_dir / "cache",
            self.project_root / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _init_bot_config(self) -> BotConfig:
        """Инициализирует конфигурацию бота"""
        return BotConfig(
            token=os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE'),
            admin_user_id=int(os.getenv('ADMIN_USER_ID', '0')),
            max_message_length=int(os.getenv('MAX_MESSAGE_LENGTH', '4096')),
            quiz_timeout=int(os.getenv('QUIZ_TIMEOUT', '300')),
            cache_size=int(os.getenv('CACHE_SIZE', '100'))
        )
    
    def _init_api_config(self) -> APIConfig:
        """Инициализирует конфигурацию API"""
        return APIConfig(
            api_key=os.getenv('OPENROUTER_API_KEY', 'YOUR_OPENROUTER_API_KEY_HERE'),
            model=os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3-0324:free'),
            max_tokens=int(os.getenv('OPENROUTER_MAX_TOKENS', '1500')),
            temperature=float(os.getenv('OPENROUTER_TEMPERATURE', '0.7')),
            max_retries=int(os.getenv('API_MAX_RETRIES', '3')),
            retry_delay=int(os.getenv('API_RETRY_DELAY', '1')),
            cooldown_seconds=int(os.getenv('API_COOLDOWN_SECONDS', '30'))
        )
    
    def _init_data_config(self) -> DataConfig:
        """Инициализирует конфигурацию данных"""
        return DataConfig(
            base_dir=self.data_base_dir,
            raw_dir=self.data_base_dir / "raw",
            processed_dir=self.data_base_dir / "processed",
            cache_dir=self.data_base_dir / "cache",
            perfume_catalog_url=os.getenv('PERFUME_CATALOG_URL', 'https://aroma-euro.ru/sitemap.xml'),
            update_interval_hours=int(os.getenv('UPDATE_INTERVAL_HOURS', '24')),
            cache_expiry_days=int(os.getenv('CACHE_EXPIRY_DAYS', '7'))
        )
    
    def _init_parser_config(self) -> ParserConfig:
        """Инициализирует конфигурацию парсера"""
        return ParserConfig(
            max_concurrent_requests=int(os.getenv('PARSER_MAX_CONCURRENT', '10')),
            request_delay=float(os.getenv('PARSER_REQUEST_DELAY', '1.0')),
            timeout=int(os.getenv('PARSER_TIMEOUT', '30')),
            retry_attempts=int(os.getenv('PARSER_RETRY_ATTEMPTS', '3')),
            user_agent=os.getenv('PARSER_USER_AGENT', 'Mozilla/5.0 (compatible; PerfumeBot/2.0)')
        )
    
    def _init_logging_config(self) -> LoggingConfig:
        """Инициализирует конфигурацию логирования"""
        return LoggingConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            log_dir=self.project_root / "logs"
        )
    
    def _validate_config(self):
        """Валидирует конфигурацию"""
        errors = []
        
        if self.bot.token == 'YOUR_BOT_TOKEN_HERE':
            errors.append("BOT_TOKEN не настроен")
        
        if self.api.api_key == 'YOUR_OPENROUTER_API_KEY_HERE':
            errors.append("OPENROUTER_API_KEY не настроен")
        
        if self.bot.admin_user_id == 0:
            errors.append("ADMIN_USER_ID не настроен")
        
        if errors:
            raise ValueError(f"Ошибки конфигурации: {', '.join(errors)}")
    
    @property
    def is_production(self) -> bool:
        """Проверяет, запущен ли в продакшене"""
        return os.getenv('ENVIRONMENT', 'development') == 'production'
    
    def get_data_file_path(self, filename: str, processed: bool = True) -> Path:
        """Возвращает путь к файлу данных"""
        base_dir = self.data.processed_dir if processed else self.data.raw_dir
        return base_dir / filename
    
    def get_cache_file_path(self, filename: str) -> Path:
        """Возвращает путь к файлу кэша"""
        return self.data.cache_dir / filename

# Глобальный экземпляр конфигурации
config = Config()