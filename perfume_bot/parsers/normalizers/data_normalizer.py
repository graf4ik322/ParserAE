#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ...core.config import config
from ...core.logger import get_logger

logger = get_logger("perfume_bot.data")

@dataclass
class NormalizedPerfume:
    """Нормализованная структура парфюма"""
    name: str
    brand: str
    factory: str
    url: str
    article: Optional[str] = None
    price: Optional[float] = None
    volume: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    notes: List[str] = None
    availability: bool = True
    image_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []

class PerfumeDataNormalizer:
    """Нормализатор данных парфюмов для оптимизации LLM запросов"""
    
    def __init__(self):
        self.raw_data = None
        self.normalized_perfumes = []
        self.factory_stats = {}
        self.brand_stats = {}
        
    def load_raw_data(self, filepath: str) -> Dict[str, Any]:
        """Загружает сырые данные из JSON файла"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.raw_data = data
        logger.info(f"📋 Загружены сырые данные: {len(data.get('perfumes', []))} парфюмов")
        return data
    
    def normalize_all_data(self) -> Dict[str, Any]:
        """Нормализует все данные и создает различные представления"""
        if not self.raw_data:
            raise ValueError("Сначала загрузите сырые данные")
        
        logger.info("🔧 Начинаю нормализацию данных...")
        
        # Нормализуем парфюмы
        self.normalized_perfumes = self._normalize_perfumes()
        
        # Создаем статистику
        self.factory_stats = self._create_factory_stats()
        self.brand_stats = self._create_brand_stats()
        
        # Создаем различные списки для LLM
        normalized_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_perfumes": len(self.normalized_perfumes),
                "total_brands": len(self.brand_stats),
                "total_factories": len(self.factory_stats),
                "normalizer_version": "2.0.0"
            },
            "perfumes": [self._perfume_to_dict(p) for p in self.normalized_perfumes],
            "factory_analysis": self.factory_stats,
            "brand_analysis": self.brand_stats,
            
            # Различные списки для LLM оптимизации
            "names_only": self._create_names_only_list(),
            "brand_name": self._create_brand_name_list(),
            "name_factory": self._create_name_factory_list(),
            "brand_name_factory": self._create_brand_name_factory_list(),
            "full_data_compact": self._create_compact_data(),
            "quiz_reference": self._create_quiz_reference()
        }
        
        logger.info("✅ Нормализация завершена")
        return normalized_data
    
    def _normalize_perfumes(self) -> List[NormalizedPerfume]:
        """Нормализует список парфюмов"""
        normalized = []
        seen_combinations = set()
        
        for perfume_data in self.raw_data.get('perfumes', []):
            try:
                # Нормализуем данные
                normalized_perfume = self._normalize_single_perfume(perfume_data)
                
                if normalized_perfume:
                    # Проверяем уникальность (бренд + название)
                    combination = f"{normalized_perfume.brand}|{normalized_perfume.name}"
                    if combination not in seen_combinations:
                        normalized.append(normalized_perfume)
                        seen_combinations.add(combination)
                    else:
                        logger.debug(f"⚠️ Дублирующийся парфюм: {combination}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка нормализации парфюма: {e}")
                continue
        
        logger.info(f"✅ Нормализовано {len(normalized)} уникальных парфюмов")
        return normalized
    
    def _normalize_single_perfume(self, data: Dict[str, Any]) -> Optional[NormalizedPerfume]:
        """Нормализует данные одного парфюма"""
        # Обязательные поля
        name = self._clean_text(data.get('name', ''))
        brand = self._clean_text(data.get('brand', ''))
        url = data.get('url', '')
        
        if not name or not brand or not url:
            return None
        
        # Нормализуем фабрику
        factory = self._normalize_factory(data.get('factory', 'Unknown Factory'))
        
        # Нормализуем остальные поля
        article = self._clean_text(data.get('article'))
        price = self._normalize_price(data.get('price'))
        volume = self._normalize_volume(data.get('volume'))
        description = self._clean_description(data.get('description'))
        category = self._normalize_category(data.get('category'))
        gender = self._normalize_gender(data.get('gender'), name)
        notes = self._normalize_notes(data.get('notes', []))
        availability = bool(data.get('availability', True))
        image_url = data.get('image_url')
        rating = self._normalize_rating(data.get('rating'))
        reviews_count = self._normalize_reviews_count(data.get('reviews_count'))
        
        return NormalizedPerfume(
            name=name,
            brand=brand,
            factory=factory,
            url=url,
            article=article,
            price=price,
            volume=volume,
            description=description,
            category=category,
            gender=gender,
            notes=notes,
            availability=availability,
            image_url=image_url,
            rating=rating,
            reviews_count=reviews_count
        )
    
    def _clean_text(self, text: Any) -> str:
        """Очищает текст от лишних символов"""
        if not text:
            return ""
        
        text = str(text).strip()
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        # Убираем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        # Убираем специальные символы в начале и конце
        text = text.strip('.,;:!?-_+=[]{}()')
        
        return text
    
    def _normalize_factory(self, factory: str) -> str:
        """Нормализует название фабрики"""
        if not factory or factory.lower() in ['unknown', 'unknown factory', 'неизвестно']:
            return 'Unknown Factory'
        
        factory = self._clean_text(factory)
        
        # Словарь для нормализации названий фабрик
        factory_mapping = {
            'селуз': 'SELUZ',
            'seluz': 'SELUZ',
            'парфюм лидер': 'Парфюм Лидер',
            'perfume leader': 'Парфюм Лидер',
            'парфюмер': 'Парфюмер',
            'parfumer': 'Парфюмер',
            'рф': 'РФ',
            'rf': 'РФ',
            'россия': 'Россия',
            'russia': 'Россия'
        }
        
        factory_lower = factory.lower()
        for key, value in factory_mapping.items():
            if key in factory_lower:
                return value
        
        return factory.title()
    
    def _normalize_price(self, price: Any) -> Optional[float]:
        """Нормализует цену"""
        if price is None:
            return None
        
        try:
            if isinstance(price, str):
                # Извлекаем число из строки
                price_match = re.search(r'(\d+(?:\.\d+)?)', price.replace(',', '.'))
                if price_match:
                    price = float(price_match.group(1))
                else:
                    return None
            
            price = float(price)
            return price if price > 0 else None
            
        except (ValueError, TypeError):
            return None
    
    def _normalize_volume(self, volume: Any) -> Optional[str]:
        """Нормализует объем"""
        if not volume:
            return None
        
        volume_str = str(volume).lower()
        
        # Извлекаем число и единицу измерения
        volume_match = re.search(r'(\d+)\s*(ml|мл)', volume_str)
        if volume_match:
            number = volume_match.group(1)
            return f"{number} мл"
        
        return None
    
    def _clean_description(self, description: Any) -> Optional[str]:
        """Очищает описание"""
        if not description:
            return None
        
        description = self._clean_text(description)
        
        # Ограничиваем длину
        if len(description) > 300:
            description = description[:297] + "..."
        
        return description if len(description) > 10 else None
    
    def _normalize_category(self, category: Any) -> Optional[str]:
        """Нормализует категорию"""
        if not category:
            return None
        
        category = self._clean_text(category)
        
        # Словарь нормализации категорий
        category_mapping = {
            'парфюм': 'Парфюм',
            'perfume': 'Парфюм',
            'туалетная вода': 'Туалетная вода',
            'eau de toilette': 'Туалетная вода',
            'парфюмерная вода': 'Парфюмерная вода',
            'eau de parfum': 'Парфюмерная вода',
            'одеколон': 'Одеколон',
            'cologne': 'Одеколон'
        }
        
        category_lower = category.lower()
        for key, value in category_mapping.items():
            if key in category_lower:
                return value
        
        return category.title()
    
    def _normalize_gender(self, gender: Any, name: str) -> Optional[str]:
        """Нормализует пол парфюма"""
        if gender:
            gender_str = str(gender).lower()
            if 'male' in gender_str or 'мужск' in gender_str:
                return 'male'
            elif 'female' in gender_str or 'женск' in gender_str:
                return 'female'
            elif 'unisex' in gender_str or 'унисекс' in gender_str:
                return 'unisex'
        
        # Пытаемся определить по названию
        name_lower = name.lower()
        if any(word in name_lower for word in ['мужской', 'for men', 'homme', 'male']):
            return 'male'
        elif any(word in name_lower for word in ['женский', 'for women', 'femme', 'female']):
            return 'female'
        elif any(word in name_lower for word in ['унисекс', 'unisex']):
            return 'unisex'
        
        return None
    
    def _normalize_notes(self, notes: List[str]) -> List[str]:
        """Нормализует ноты парфюма"""
        if not notes:
            return []
        
        normalized_notes = []
        for note in notes:
            if note and isinstance(note, str):
                clean_note = self._clean_text(note)
                if clean_note and len(clean_note) > 2:
                    normalized_notes.append(clean_note.title())
        
        # Убираем дубликаты и ограничиваем количество
        return list(dict.fromkeys(normalized_notes))[:8]
    
    def _normalize_rating(self, rating: Any) -> Optional[float]:
        """Нормализует рейтинг"""
        if rating is None:
            return None
        
        try:
            rating = float(rating)
            return rating if 0 <= rating <= 5 else None
        except (ValueError, TypeError):
            return None
    
    def _normalize_reviews_count(self, count: Any) -> Optional[int]:
        """Нормализует количество отзывов"""
        if count is None:
            return None
        
        try:
            count = int(count)
            return count if count >= 0 else None
        except (ValueError, TypeError):
            return None
    
    def _perfume_to_dict(self, perfume: NormalizedPerfume) -> Dict[str, Any]:
        """Конвертирует парфюм в словарь"""
        return {
            'name': perfume.name,
            'brand': perfume.brand,
            'factory': perfume.factory,
            'url': perfume.url,
            'article': perfume.article,
            'price': perfume.price,
            'volume': perfume.volume,
            'description': perfume.description,
            'category': perfume.category,
            'gender': perfume.gender,
            'notes': perfume.notes,
            'availability': perfume.availability,
            'image_url': perfume.image_url,
            'rating': perfume.rating,
            'reviews_count': perfume.reviews_count
        }
    
    def _create_factory_stats(self) -> Dict[str, Any]:
        """Создает статистику по фабрикам"""
        factory_stats = defaultdict(lambda: {
            'perfume_count': 0,
            'brands': set(),
            'avg_price': 0,
            'price_range': {'min': float('inf'), 'max': 0},
            'quality_levels': set(),
            'perfumes': []
        })
        
        for perfume in self.normalized_perfumes:
            factory = perfume.factory
            stats = factory_stats[factory]
            
            stats['perfume_count'] += 1
            stats['brands'].add(perfume.brand)
            stats['perfumes'].append({
                'name': perfume.name,
                'brand': perfume.brand,
                'price': perfume.price,
                'url': perfume.url
            })
            
            # Статистика цен
            if perfume.price:
                if perfume.price < stats['price_range']['min']:
                    stats['price_range']['min'] = perfume.price
                if perfume.price > stats['price_range']['max']:
                    stats['price_range']['max'] = perfume.price
            
            # Определяем уровень качества по цене
            if perfume.price:
                if perfume.price < 1000:
                    stats['quality_levels'].add('эконом')
                elif perfume.price < 3000:
                    stats['quality_levels'].add('стандарт')
                elif perfume.price < 6000:
                    stats['quality_levels'].add('премиум')
                else:
                    stats['quality_levels'].add('люкс')
        
        # Конвертируем sets в lists для JSON
        result = {}
        for factory, stats in factory_stats.items():
            prices = [p['price'] for p in stats['perfumes'] if p['price']]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            result[factory] = {
                'perfume_count': stats['perfume_count'],
                'brands': sorted(list(stats['brands'])),
                'avg_price': round(avg_price, 2),
                'price_range': {
                    'min': stats['price_range']['min'] if stats['price_range']['min'] != float('inf') else 0,
                    'max': stats['price_range']['max']
                },
                'quality_levels': sorted(list(stats['quality_levels'])),
                'top_perfumes': sorted(stats['perfumes'], key=lambda x: x['price'] or 0, reverse=True)[:5]
            }
        
        return result
    
    def _create_brand_stats(self) -> Dict[str, Any]:
        """Создает статистику по брендам"""
        brand_stats = defaultdict(lambda: {
            'perfume_count': 0,
            'factories': set(),
            'avg_price': 0,
            'perfumes': []
        })
        
        for perfume in self.normalized_perfumes:
            brand = perfume.brand
            stats = brand_stats[brand]
            
            stats['perfume_count'] += 1
            stats['factories'].add(perfume.factory)
            stats['perfumes'].append({
                'name': perfume.name,
                'factory': perfume.factory,
                'price': perfume.price,
                'url': perfume.url
            })
        
        # Конвертируем в финальный формат
        result = {}
        for brand, stats in brand_stats.items():
            prices = [p['price'] for p in stats['perfumes'] if p['price']]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            result[brand] = {
                'perfume_count': stats['perfume_count'],
                'factories': sorted(list(stats['factories'])),
                'avg_price': round(avg_price, 2),
                'top_perfumes': sorted(stats['perfumes'], key=lambda x: x['price'] or 0, reverse=True)[:3]
            }
        
        return result
    
    # Методы для создания различных списков для LLM
    
    def _create_names_only_list(self) -> List[str]:
        """Создает список только названий ароматов (уникальные)"""
        names = set()
        for perfume in self.normalized_perfumes:
            names.add(perfume.name)
        return sorted(list(names))
    
    def _create_brand_name_list(self) -> List[str]:
        """Создает список бренд + название"""
        items = set()
        for perfume in self.normalized_perfumes:
            items.add(f"{perfume.brand} - {perfume.name}")
        return sorted(list(items))
    
    def _create_name_factory_list(self) -> List[str]:
        """Создает список название + фабрика"""
        items = set()
        for perfume in self.normalized_perfumes:
            items.add(f"{perfume.name} ({perfume.factory})")
        return sorted(list(items))
    
    def _create_brand_name_factory_list(self) -> List[str]:
        """Создает список бренд + название + фабрика"""
        items = set()
        for perfume in self.normalized_perfumes:
            if perfume.article:
                items.add(f"{perfume.brand} {perfume.name} ({perfume.factory}) [Артикул: {perfume.article}]")
            else:
                items.add(f"{perfume.brand} {perfume.name} ({perfume.factory})")
        return sorted(list(items))
    
    def _create_compact_data(self) -> List[Dict[str, Any]]:
        """Создает компактное представление данных"""
        compact = []
        for perfume in self.normalized_perfumes:
            compact.append({
                'name': perfume.name,
                'brand': perfume.brand,
                'factory': perfume.factory,
                'url': perfume.url,
                'article': perfume.article,
                'price': perfume.price,
                'volume': perfume.volume,
                'gender': perfume.gender,
                'availability': perfume.availability
            })
        return compact
    
    def _create_quiz_reference(self) -> Dict[str, Any]:
        """Создает справочник для квиза"""
        # Группируем по полу
        by_gender = defaultdict(list)
        by_price = defaultdict(list)
        by_factory = defaultdict(list)
        
        for perfume in self.normalized_perfumes:
            # По полу
            gender = perfume.gender or 'unisex'
            by_gender[gender].append(perfume.name)
            
            # По цене
            if perfume.price:
                if perfume.price < 1500:
                    by_price['budget'].append(perfume.name)
                elif perfume.price < 4000:
                    by_price['medium'].append(perfume.name)
                else:
                    by_price['premium'].append(perfume.name)
            
            # По фабрике
            by_factory[perfume.factory].append(perfume.name)
        
        return {
            'by_gender': dict(by_gender),
            'by_price': dict(by_price),
            'by_factory': dict(by_factory),
            'total_perfumes': len(self.normalized_perfumes)
        }
    
    def save_normalized_data(self, data: Dict[str, Any], filename: str = None) -> str:
        """Сохраняет нормализованные данные"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"perfumes_normalized_{timestamp}.json"
        
        filepath = config.get_data_file_path(filename, processed=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Нормализованные данные сохранены в {filepath}")
        return str(filepath)
    
    def save_separate_files(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Сохраняет отдельные файлы для каждого типа данных"""
        saved_files = {}
        
        # Сохраняем отдельные списки
        lists_to_save = [
            'names_only',
            'brand_name', 
            'name_factory',
            'brand_name_factory',
            'full_data_compact',
            'factory_analysis',
            'quiz_reference'
        ]
        
        for list_name in lists_to_save:
            if list_name in data:
                filename = f"{list_name}.json"
                filepath = config.get_data_file_path(filename, processed=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data[list_name], f, ensure_ascii=False, indent=2)
                
                saved_files[list_name] = str(filepath)
                logger.info(f"💾 Сохранен файл: {filename}")
        
        return saved_files