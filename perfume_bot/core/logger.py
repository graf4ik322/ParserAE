#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from .config import config

class PerfumeLogger:
    """Система логирования для парфюмерного бота"""
    
    def __init__(self, name: str = "perfume_bot"):
        self.name = name
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Настраивает логгер с ротацией файлов"""
        self.logger = logging.getLogger(self.name)
        
        # Если логгер уже настроен, не настраиваем повторно
        if self.logger.handlers:
            return
        
        # Устанавливаем уровень логирования
        level = getattr(logging, config.logging.level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Создаем форматтер
        formatter = logging.Formatter(
            config.logging.format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Файловый обработчик с ротацией
        try:
            log_file = config.logging.log_dir / f"{self.name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=config.logging.max_file_size,
                backupCount=config.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            self.logger.warning(f"Не удалось создать файл логов: {e}")
        
        # Отдельный файл для ошибок
        try:
            error_log_file = config.logging.log_dir / f"{self.name}_errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=config.logging.max_file_size,
                backupCount=config.logging.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            self.logger.addHandler(error_handler)
        except (PermissionError, OSError):
            pass  # Игнорируем ошибки создания файла ошибок
    
    def debug(self, message: str, *args, **kwargs):
        """Логирует debug сообщение"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Логирует info сообщение"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Логирует warning сообщение"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Логирует error сообщение"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Логирует critical сообщение"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Логирует исключение с трейсбеком"""
        self.logger.exception(message, *args, **kwargs)

# Глобальные логгеры для разных компонентов
_loggers = {}

def get_logger(name: str = "perfume_bot") -> PerfumeLogger:
    """Получает логгер по имени"""
    if name not in _loggers:
        _loggers[name] = PerfumeLogger(name)
    return _loggers[name]

def setup_logging(level: Optional[str] = None):
    """Настраивает логирование для всего приложения"""
    if level:
        # Обновляем уровень в конфигурации
        config.logging.level = level.upper()
    
    # Создаем основные логгеры
    get_logger("perfume_bot")  # Основной логгер
    get_logger("perfume_bot.parser")  # Логгер парсера
    get_logger("perfume_bot.bot")  # Логгер бота
    get_logger("perfume_bot.api")  # Логгер API
    get_logger("perfume_bot.data")  # Логгер данных

# Удобные алиасы для основных логгеров
main_logger = get_logger("perfume_bot")
parser_logger = get_logger("perfume_bot.parser")
bot_logger = get_logger("perfume_bot.bot")
api_logger = get_logger("perfume_bot.api")
data_logger = get_logger("perfume_bot.data")