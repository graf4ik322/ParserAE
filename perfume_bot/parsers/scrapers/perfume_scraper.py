#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from ...core.config import config
from ...core.logger import get_logger

logger = get_logger("perfume_bot.parser")

@dataclass
class PerfumeData:
    """Структура данных парфюма"""
    name: str
    brand: str
    factory: str
    url: str
    price: Optional[float] = None
    volume: Optional[str] = None
    description: Optional[str] = None
    article: Optional[str] = None
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

class PerfumeScraper:
    """Интегрированный парсер парфюмов"""
    
    def __init__(self):
        self.session = None
        self.parsed_urls = set()
        self.perfumes = []
        
        # Настройки парсера из конфигурации
        self.max_concurrent = config.parser.max_concurrent_requests
        self.request_delay = config.parser.request_delay
        self.timeout = config.parser.timeout
        self.retry_attempts = config.parser.retry_attempts
        self.user_agent = config.parser.user_agent
        
        # Семафор для ограничения concurrent запросов
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def _fetch_with_retry(self, url: str) -> Optional[str]:
        """Получает HTML страницы с повторными попытками"""
        for attempt in range(self.retry_attempts):
            try:
                async with self.semaphore:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            logger.debug(f"✅ Загружена страница: {url}")
                            return content
                        else:
                            logger.warning(f"⚠️ HTTP {response.status} для {url}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Таймаут для {url} (попытка {attempt + 1})")
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки {url}: {e}")
            
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.request_delay * (attempt + 1))
        
        logger.error(f"❌ Не удалось загрузить {url} после {self.retry_attempts} попыток")
        return None
    
    async def get_sitemap_urls(self, sitemap_url: str) -> List[str]:
        """Извлекает URL из sitemap"""
        logger.info(f"📋 Получение URL из sitemap: {sitemap_url}")
        
        content = await self._fetch_with_retry(sitemap_url)
        if not content:
            return []
        
        urls = []
        
        # Парсим XML sitemap
        try:
            # Простой парсинг XML через регулярные выражения
            url_pattern = r'<loc>(.*?)</loc>'
            found_urls = re.findall(url_pattern, content)
            
            # Фильтруем URL парфюмов
            perfume_urls = [
                url for url in found_urls 
                if self._is_perfume_url(url)
            ]
            
            urls.extend(perfume_urls)
            logger.info(f"✅ Найдено {len(urls)} URL парфюмов в sitemap")
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга sitemap: {e}")
        
        return urls
    
    def _is_perfume_url(self, url: str) -> bool:
        """Проверяет, является ли URL страницей парфюма"""
        # Паттерны для определения страниц парфюмов
        perfume_patterns = [
            r'/parfum/',
            r'/perfume/',
            r'/fragrance/',
            r'/product/',
            r'\.html$'
        ]
        
        # Исключаем служебные страницы
        exclude_patterns = [
            r'/category/',
            r'/brand/',
            r'/search/',
            r'/cart/',
            r'/checkout/',
            r'/account/',
            r'/blog/',
            r'/news/'
        ]
        
        url_lower = url.lower()
        
        # Проверяем исключения
        for pattern in exclude_patterns:
            if re.search(pattern, url_lower):
                return False
        
        # Проверяем соответствие паттернам парфюмов
        for pattern in perfume_patterns:
            if re.search(pattern, url_lower):
                return True
        
        return False
    
    async def parse_perfume_page(self, url: str) -> Optional[PerfumeData]:
        """Парсит страницу парфюма"""
        if url in self.parsed_urls:
            return None
        
        content = await self._fetch_with_retry(url)
        if not content:
            return None
        
        self.parsed_urls.add(url)
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            perfume_data = await self._extract_perfume_data(soup, url)
            
            if perfume_data and perfume_data.name and perfume_data.brand:
                logger.debug(f"✅ Парфюм распознан: {perfume_data.brand} - {perfume_data.name}")
                return perfume_data
            else:
                logger.debug(f"⚠️ Неполные данные для {url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга {url}: {e}")
            return None
    
    async def _extract_perfume_data(self, soup: BeautifulSoup, url: str) -> Optional[PerfumeData]:
        """Извлекает данные парфюма из HTML"""
        try:
            # Извлекаем название
            name = self._extract_name(soup)
            if not name:
                return None
            
            # Извлекаем бренд
            brand = self._extract_brand(soup, name)
            
            # Извлекаем фабрику
            factory = self._extract_factory(soup)
            
            # Извлекаем остальные данные
            price = self._extract_price(soup)
            volume = self._extract_volume(soup)
            description = self._extract_description(soup)
            article = self._extract_article(soup)
            category = self._extract_category(soup)
            gender = self._extract_gender(soup, name)
            notes = self._extract_notes(soup)
            availability = self._extract_availability(soup)
            image_url = self._extract_image_url(soup, url)
            rating = self._extract_rating(soup)
            reviews_count = self._extract_reviews_count(soup)
            
            return PerfumeData(
                name=name,
                brand=brand,
                factory=factory,
                url=url,
                price=price,
                volume=volume,
                description=description,
                article=article,
                category=category,
                gender=gender,
                notes=notes,
                availability=availability,
                image_url=image_url,
                rating=rating,
                reviews_count=reviews_count
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения данных: {e}")
            return None
    
    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Извлекает название парфюма"""
        selectors = [
            'h1.product-title',
            'h1.title',
            'h1',
            '.product-name',
            '.perfume-name',
            '[data-name]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name and len(name) > 3:
                    return self._clean_name(name)
        
        return None
    
    def _extract_brand(self, soup: BeautifulSoup, name: str) -> str:
        """Извлекает бренд парфюма"""
        # Попытка извлечь из специальных элементов
        selectors = [
            '.brand-name',
            '.manufacturer',
            '.product-brand',
            '[data-brand]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                brand = element.get_text(strip=True)
                if brand:
                    return brand
        
        # Попытка извлечь из названия
        return self._extract_brand_from_name(name)
    
    def _extract_brand_from_name(self, name: str) -> str:
        """Извлекает бренд из названия"""
        # Список известных брендов
        known_brands = [
            'Tom Ford', 'Chanel', 'Dior', 'Gucci', 'Versace', 'Armani',
            'Calvin Klein', 'Hugo Boss', 'Dolce & Gabbana', 'Prada',
            'Yves Saint Laurent', 'Givenchy', 'Burberry', 'Hermès',
            'Creed', 'Maison Margiela', 'Byredo', 'Le Labo', 'Amouage'
        ]
        
        name_lower = name.lower()
        for brand in known_brands:
            if brand.lower() in name_lower:
                return brand
        
        # Если бренд не найден, берем первое слово
        words = name.split()
        return words[0] if words else "Unknown"
    
    def _extract_factory(self, soup: BeautifulSoup) -> str:
        """Извлекает фабрику производителя"""
        selectors = [
            '.factory',
            '.manufacturer-factory',
            '.producer'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                factory = element.get_text(strip=True)
                if factory:
                    return factory
        
        return "Unknown Factory"
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Извлекает цену"""
        selectors = [
            '.price',
            '.product-price',
            '.cost',
            '[data-price]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Извлекаем числа из текста
                price_match = re.search(r'(\d+(?:\.\d+)?)', price_text.replace(',', '.'))
                if price_match:
                    try:
                        return float(price_match.group(1))
                    except ValueError:
                        continue
        
        return None
    
    def _extract_volume(self, soup: BeautifulSoup) -> Optional[str]:
        """Извлекает объем"""
        selectors = [
            '.volume',
            '.size',
            '.ml'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                volume = element.get_text(strip=True)
                if 'ml' in volume.lower() or 'мл' in volume.lower():
                    return volume
        
        # Поиск в названии или описании
        text = soup.get_text()
        volume_match = re.search(r'(\d+\s*(?:ml|мл))', text, re.IGNORECASE)
        if volume_match:
            return volume_match.group(1)
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Извлекает описание"""
        selectors = [
            '.description',
            '.product-description',
            '.about',
            '.details'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                description = element.get_text(strip=True)
                if description and len(description) > 20:
                    return description[:500]  # Ограничиваем длину
        
        return None
    
    def _extract_article(self, soup: BeautifulSoup) -> Optional[str]:
        """Извлекает артикул"""
        selectors = [
            '.article',
            '.sku',
            '.product-code',
            '[data-sku]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                article = element.get_text(strip=True)
                if article:
                    return article
        
        return None
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Извлекает категорию"""
        selectors = [
            '.category',
            '.breadcrumb',
            '.product-category'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                category = element.get_text(strip=True)
                if category:
                    return category
        
        return None
    
    def _extract_gender(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """Определяет пол парфюма"""
        text = (soup.get_text() + " " + name).lower()
        
        if any(word in text for word in ['мужской', 'for men', 'homme', 'male']):
            return 'male'
        elif any(word in text for word in ['женский', 'for women', 'femme', 'female']):
            return 'female'
        elif any(word in text for word in ['унисекс', 'unisex', 'for all']):
            return 'unisex'
        
        return None
    
    def _extract_notes(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает ноты парфюма"""
        notes = []
        
        selectors = [
            '.notes',
            '.fragrance-notes',
            '.composition'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                notes_text = element.get_text()
                # Простое извлечение нот через запятые
                note_list = [note.strip() for note in notes_text.split(',')]
                notes.extend(note_list)
        
        return notes[:10]  # Ограничиваем количество нот
    
    def _extract_availability(self, soup: BeautifulSoup) -> bool:
        """Проверяет наличие товара"""
        unavailable_indicators = [
            'out of stock',
            'нет в наличии',
            'недоступен',
            'sold out'
        ]
        
        text = soup.get_text().lower()
        return not any(indicator in text for indicator in unavailable_indicators)
    
    def _extract_image_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Извлекает URL изображения"""
        selectors = [
            '.product-image img',
            '.perfume-image img',
            '.main-image img',
            'img.product'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src') or element.get('data-src')
                if src:
                    return urljoin(base_url, src)
        
        return None
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Извлекает рейтинг"""
        selectors = [
            '.rating',
            '.stars',
            '[data-rating]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text(strip=True)
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                        if 0 <= rating <= 5:
                            return rating
                    except ValueError:
                        continue
        
        return None
    
    def _extract_reviews_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Извлекает количество отзывов"""
        selectors = [
            '.reviews-count',
            '.review-count',
            '[data-reviews]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                count_text = element.get_text(strip=True)
                count_match = re.search(r'(\d+)', count_text)
                if count_match:
                    try:
                        return int(count_match.group(1))
                    except ValueError:
                        continue
        
        return None
    
    def _clean_name(self, name: str) -> str:
        """Очищает название от лишних символов"""
        # Убираем лишние пробелы и символы
        name = re.sub(r'\s+', ' ', name.strip())
        # Убираем HTML теги если остались
        name = re.sub(r'<[^>]+>', '', name)
        return name
    
    async def scrape_all_perfumes(self, sitemap_url: str = None) -> List[PerfumeData]:
        """Парсит все парфюмы с сайта"""
        if not sitemap_url:
            sitemap_url = config.data.perfume_catalog_url
        
        logger.info(f"🚀 Начинаю парсинг парфюмов с {sitemap_url}")
        
        # Получаем URL из sitemap
        urls = await self.get_sitemap_urls(sitemap_url)
        if not urls:
            logger.error("❌ Не удалось получить URL из sitemap")
            return []
        
        logger.info(f"📋 Найдено {len(urls)} URL для парсинга")
        
        # Парсим страницы параллельно
        tasks = []
        for url in urls[:100]:  # Ограничиваем для тестирования
            task = asyncio.create_task(self.parse_perfume_page(url))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        perfumes = []
        for result in results:
            if isinstance(result, PerfumeData):
                perfumes.append(result)
            elif isinstance(result, Exception):
                logger.error(f"❌ Ошибка при парсинге: {result}")
        
        logger.info(f"✅ Успешно распарсено {len(perfumes)} парфюмов")
        self.perfumes = perfumes
        return perfumes
    
    def save_to_json(self, filename: str = None) -> str:
        """Сохраняет данные в JSON файл"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"perfumes_raw_{timestamp}.json"
        
        filepath = config.get_data_file_path(filename, processed=False)
        
        # Конвертируем в словари для JSON
        data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_count": len(self.perfumes),
                "parser_version": "2.0.0"
            },
            "perfumes": [asdict(perfume) for perfume in self.perfumes]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Данные сохранены в {filepath}")
        return str(filepath)