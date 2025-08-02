#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
from typing import Dict, Any, Optional
from hashlib import md5

logger = logging.getLogger(__name__)

class DataProcessor:
    """Процессор для нормализации и обработки данных парфюмов"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        
        # Известные фабрики (из оригинального парсера)
        self.known_factories = [
            'Bin Tammam', 'EPS', 'Givaudan', 'Givaudan Premium', 'Givaudan SuperLux',
            'Hamidi', 'Iberchem', 'LZ AG', 'Lz', 'LZ', 'MG Gulcicek', 'Reiha', 
            'Argeville', 'SELUZ', 'Seluz', 'LUZI', 'Luzi'
        ]
        
        logger.info("🔧 DataProcessor инициализирован")
    
    def normalize_perfume_data(self, raw_perfume: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализует данные парфюма согласно схеме БД"""
        try:
            # Извлекаем основные данные
            brand = self._clean_text(raw_perfume.get('brand', ''))
            name = self._clean_text(raw_perfume.get('name', ''))
            full_title = self._clean_text(raw_perfume.get('full_title', ''))
            
            # Извлекаем детали из парфюма сначала
            details = raw_perfume.get('details', {})
            if isinstance(details, str):
                details = {}
            
            # ПРИОРИТЕТ 1: Артикул из детальной страницы (КОД)
            article = details.get('article', '').strip()
            
            # ПРИОРИТЕТ 2: Если артикул не найден в деталях, пытаемся извлечь из названия/URL
            if not article:
                article = self._extract_article(full_title, raw_perfume.get('url', ''))
                logger.debug(f"Артикул извлечен из названия/URL: '{article}'")
            else:
                logger.debug(f"Артикул найден в деталях: '{article}'")
            
            # Обрабатываем фабрику
            factory = self._normalize_factory(raw_perfume.get('factory', ''))
            factory_detailed = self._extract_factory_details(raw_perfume)
            
            # Обрабатываем цену
            price_str = str(raw_perfume.get('price', ''))
            price = self._extract_numeric_price(price_str)
            
            # Создаем уникальный ключ для дедупликации
            unique_key = self._create_unique_key(brand, name, factory)
            
            gender = self._normalize_gender(details.get('gender', ''))
            fragrance_group = self._normalize_fragrance_group(details.get('fragrance_group', ''))
            quality_level = self._normalize_quality_level(details.get('quality', ''))
            
            # URL
            url = raw_perfume.get('url', '')
            if url and not url.startswith('http'):
                url = f"https://aroma-euro.ru{url}"
            
            normalized = {
                'article': article,
                'unique_key': unique_key,
                'brand': brand,
                'name': name,
                'full_title': full_title,
                'factory': factory,
                'factory_detailed': factory_detailed,
                'price': price,
                'price_formatted': price_str,
                'currency': 'RUB',
                'gender': gender,
                'fragrance_group': fragrance_group,
                'quality_level': quality_level,
                'url': url
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Ошибка при нормализации данных парфюма: {e}")
            logger.error(f"Raw data: {raw_perfume}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Очищает текст от лишних символов"""
        if not text:
            return ''
        
        # Убираем лишние пробелы и переводы строк
        text = re.sub(r'\s+', ' ', str(text))
        text = text.strip()
        
        # Убираем специальные символы, которые могут вызвать проблемы
        text = text.replace('\x00', '')
        
        return text
    
    def _extract_article(self, full_title: str, url: str) -> str:
        """Извлекает артикул из названия или URL"""
        # Пытаемся найти артикул в названии (обычно в скобках или в конце)
        article_patterns = [
            r'\b([A-Z]{2,}\d{3,})\b',  # Буквы + цифры (например, TF001)
            r'\b(\d{4,})\b',           # Просто цифры (например, 1234)
            r'\[([A-Z0-9\-]+)\]',      # В квадратных скобках
            r'\(([A-Z0-9\-]+)\)',      # В круглых скобках
        ]
        
        for pattern in article_patterns:
            match = re.search(pattern, full_title)
            if match:
                return match.group(1)
        
        # Если не найден в названии, пытаемся извлечь из URL
        if url:
            url_match = re.search(r'/([A-Z0-9\-]+)/?$', url.upper())
            if url_match:
                return url_match.group(1)
        
        # Если ничего не найдено, генерируем артикул на основе хэша
        hash_source = f"{full_title}_{url}"
        article = 'GEN' + md5(hash_source.encode()).hexdigest()[:6].upper()
        
        return article
    
    def _normalize_factory(self, factory: str) -> str:
        """Нормализует название фабрики"""
        if not factory:
            return ''
        
        factory_clean = self._clean_text(factory)
        
        # Проверяем соответствие известным фабрикам
        for known_factory in self.known_factories:
            if known_factory.lower() in factory_clean.lower():
                return known_factory
        
        return factory_clean
    
    def _extract_factory_details(self, raw_perfume: Dict[str, Any]) -> str:
        """Извлекает подробную информацию о фабрике"""
        details = raw_perfume.get('details', {})
        if isinstance(details, dict):
            factory_detailed = details.get('factory_detailed', '')
            if factory_detailed:
                return self._clean_text(factory_detailed)
        
        return ''
    
    def _extract_numeric_price(self, price_str: str) -> float:
        """Извлекает числовую цену из строки"""
        if not price_str:
            return 0.0
        
        # Убираем все кроме цифр, точек и запятых
        price_clean = re.sub(r'[^\d.,]', '', str(price_str))
        
        # Заменяем запятые на точки
        price_clean = price_clean.replace(',', '.')
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return 0.0
    
    def _create_unique_key(self, brand: str, name: str, factory: str) -> str:
        """Создает уникальный ключ для дедупликации"""
        # Нормализуем компоненты ключа
        brand_norm = re.sub(r'[^\w\s]', '', brand.lower().strip())
        name_norm = re.sub(r'[^\w\s]', '', name.lower().strip())
        factory_norm = re.sub(r'[^\w\s]', '', factory.lower().strip())
        
        # Создаем ключ
        key_source = f"{brand_norm}_{name_norm}_{factory_norm}"
        key_hash = md5(key_source.encode()).hexdigest()
        
        return f"{brand[:3].upper()}_{key_hash[:8]}"
    
    def _normalize_gender(self, gender: str) -> str:
        """Нормализует пол парфюма"""
        if not gender:
            return ''
        
        gender_lower = gender.lower()
        
        if 'мужск' in gender_lower or 'men' in gender_lower:
            return 'Мужской'
        elif 'женск' in gender_lower or 'women' in gender_lower:
            return 'Женский'
        elif 'унисекс' in gender_lower or 'unisex' in gender_lower:
            return 'Унисекс'
        
        return self._clean_text(gender)
    
    def _normalize_fragrance_group(self, fragrance_group: str) -> str:
        """Нормализует группу ароматов"""
        if not fragrance_group:
            return ''
        
        # Список стандартных групп ароматов
        standard_groups = {
            'цветочн': 'Цветочные',
            'цитрус': 'Цитрусовые', 
            'древесн': 'Древесные',
            'свеж': 'Свежие',
            'восточн': 'Восточные',
            'гурман': 'Гурманские',
            'фужер': 'Фужерные',
            'шипр': 'Шипровые',
            'амбр': 'Амбровые',
            'мускус': 'Мускусные'
        }
        
        fragrance_lower = fragrance_group.lower()
        
        for key, standard_name in standard_groups.items():
            if key in fragrance_lower:
                return standard_name
        
        return self._clean_text(fragrance_group)
    
    def _normalize_quality_level(self, quality: str) -> str:
        """Нормализует уровень качества"""
        if not quality:
            return ''
        
        quality_lower = quality.lower()
        
        # Стандартные уровни качества
        if 'премиум' in quality_lower or 'premium' in quality_lower:
            return 'Премиум'
        elif 'люкс' in quality_lower or 'lux' in quality_lower:
            return 'Люкс'
        elif 'стандарт' in quality_lower or 'standard' in quality_lower:
            return 'Стандарт'
        elif 'эконом' in quality_lower or 'econom' in quality_lower:
            return 'Эконом'
        
        return self._clean_text(quality)
    
    def validate_perfume_data(self, perfume_data: Dict[str, Any]) -> bool:
        """Валидирует данные парфюма перед сохранением"""
        required_fields = ['article', 'unique_key', 'brand', 'name', 'url']
        
        for field in required_fields:
            if not perfume_data.get(field):
                logger.warning(f"Отсутствует обязательное поле: {field}")
                return False
        
        # Проверяем длину полей
        if len(perfume_data['article']) > 50:
            logger.warning(f"Артикул слишком длинный: {perfume_data['article']}")
            return False
        
        if len(perfume_data['brand']) > 100:
            logger.warning(f"Бренд слишком длинный: {perfume_data['brand']}")
            return False
        
        return True