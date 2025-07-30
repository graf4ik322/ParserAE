#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Perfume Consultant Bot - Единая система парфюмерного консультанта

Включает в себя:
- Парсинг и нормализацию данных о парфюмах
- Telegram бот с ИИ консультантом
- API интеграцию с OpenRouter
- Систему рекомендаций на основе квизов
"""

__version__ = "2.0.0"
__author__ = "Perfume Bot Team"
__description__ = "Intelligent Perfume Consultant Bot with Data Pipeline"

# Основные компоненты
from .core.application import PerfumeApplication
from .core.config import Config
from .core.logger import setup_logging

# Экспортируем основные классы
__all__ = [
    'PerfumeApplication',
    'Config', 
    'setup_logging'
]