#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправленная версия парсера с правильной обработкой сжатого контента
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin
import re
from typing import List, Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FixedParser:
    """Исправленный парсер для aroma-euro.ru"""
    
    def __init__(self):
        self.base_url = "https://aroma-euro.ru"
        self.session = requests.Session()
        # Убираем Accept-Encoding для избежания проблем со сжатием
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        self.perfumes = []
    
    def parse_title(self, title: str) -> tuple:
        """Парсинг названия для разделения на бренд и название"""
        title = title.strip()
        
        # Удаляем лишние части
        title = re.sub(r'\s*\(мотив\)\s*', '', title)
        title = re.sub(r',\s*[A-Z][a-z]\s*\d+[-\w]*\s*$', '', title)  # Убираем код в конце
        
        # Известные бренды
        known_brands = [
            'Tom Ford', 'Chanel', 'Dior', 'Gucci', 'Prada', 'Versace', 'Armani', 
            'Calvin Klein', 'Hugo Boss', 'Dolce Gabbana', 'Yves Saint Laurent',
            'Creed', 'Maison Margiela', 'Byredo', 'Le Labo', 'Diptyque', 'Hermès',
            'Bottega Veneta', 'Burberry', 'Givenchy', 'Lancome', 'Estee Lauder',
            'Escentric Molecules', 'Montale', 'Mancera', 'Amouage', 'Nasomatto',
            'Serge Lutens', 'Francis Kurkdjian', 'Frederic Malle', 'Penhaligons',
            'Miller Harris', 'Acqua di Parma', 'Annick Goutal', 'L\'Artisan Parfumeur',
            'Ex Nihilo', 'Tiziana Terenzi', 'Dolce&Gabbana', 'Tiziana terenzi'
        ]
        
        # Поиск известных брендов
        title_lower = title.lower()
        for brand in known_brands:
            brand_lower = brand.lower()
            if title_lower.startswith(brand_lower):
                remaining = title[len(brand):].strip()
                if remaining:
                    return brand, remaining
        
        # Паттерны для разделения
        patterns = [
            # Brand Name
            r'^([A-Za-z][A-Za-z\s&\.\-\']+?)\s+([A-Za-z].+)$',
            # Brand - Name
            r'^([A-Za-z][A-Za-z\s&\.\-\']+?)\s*[-–—]\s*(.+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                potential_brand = match.group(1).strip()
                potential_name = match.group(2).strip()
                
                # Проверяем разумность разделения
                if (len(potential_brand.split()) <= 3 and 
                    len(potential_brand) <= 50 and
                    len(potential_name) > 2):
                    return potential_brand, potential_name
        
        # Если не удалось разделить
        return "", title
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Получение содержимого страницы с правильной обработкой сжатия"""
        try:
            logger.info(f"Загружаю страницу: {url}")
            
            # Делаем запрос без автоматического декодирования
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Получаем содержимое
            content = response.content
            
            # Декодируем в зависимости от кодировки
            if response.encoding:
                text = content.decode(response.encoding)
            else:
                text = content.decode('utf-8', errors='ignore')
            
            logger.info(f"Размер страницы: {len(text)} символов")
            
            # Проверяем наличие product-title в тексте
            product_title_count = text.count('product-title')
            logger.info(f"Найдено 'product-title' в HTML: {product_title_count}")
            
            return BeautifulSoup(text, 'html.parser')
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке {url}: {e}")
            return None
    
    def parse_page(self, url: str) -> List[Dict[str, str]]:
        """Парсинг одной страницы"""
        soup = self.get_page_content(url)
        if not soup:
            return []
        
        perfumes = []
        
        # Ищем все ссылки с классом product-title
        product_links = soup.find_all('a', class_='product-title')
        logger.info(f"Найдено ссылок .product-title: {len(product_links)}")
        
        for link in product_links:
            try:
                title = link.get_text(strip=True)
                href = link.get('href')
                
                if title and href and '/perfume/' in href:
                    # Разбираем название
                    brand, name = self.parse_title(title)
                    
                    perfume_data = {
                        'full_title': title,
                        'brand': brand,
                        'name': name,
                        'url': urljoin(self.base_url, href)
                    }
                    
                    # Ищем цену в родительском элементе
                    parent = link.find_parent()
                    while parent and parent.name != 'body':
                        price_element = parent.find(class_=re.compile(r'.*price.*'))
                        if price_element:
                            price_text = price_element.get_text(strip=True)
                            if price_text and any(char.isdigit() for char in price_text):
                                perfume_data['price'] = price_text
                            break
                        parent = parent.find_parent()
                    
                    perfumes.append(perfume_data)
                    
            except Exception as e:
                logger.error(f"Ошибка при обработке ссылки: {e}")
                continue
        
        return perfumes
    
    def get_all_pages(self) -> List[str]:
        """Получение всех страниц каталога"""
        urls = ["https://aroma-euro.ru/perfume/"]
        
        soup = self.get_page_content(urls[0])
        if not soup:
            return urls
        
        # Ищем пагинацию
        pagination_links = soup.find_all('a', href=re.compile(r'.*page-\d+.*'))
        
        for link in pagination_links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                if full_url not in urls:
                    urls.append(full_url)
        
        logger.info(f"Найдено страниц: {len(urls)}")
        return sorted(urls)
    
    def parse_catalog(self, max_pages: int = None) -> List[Dict[str, str]]:
        """Парсинг всего каталога"""
        logger.info("Начинаю парсинг каталога")
        
        page_urls = self.get_all_pages()
        
        if max_pages:
            page_urls = page_urls[:max_pages]
        
        all_perfumes = []
        
        for i, url in enumerate(page_urls, 1):
            logger.info(f"Страница {i}/{len(page_urls)}: {url}")
            
            page_perfumes = self.parse_page(url)
            all_perfumes.extend(page_perfumes)
            
            logger.info(f"Найдено товаров на странице: {len(page_perfumes)}")
            
            # Задержка между запросами
            if i < len(page_urls):
                time.sleep(2)
        
        # Удаление дубликатов по URL
        unique_perfumes = []
        seen_urls = set()
        
        for perfume in all_perfumes:
            url = perfume.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_perfumes.append(perfume)
        
        logger.info(f"Всего уникальных товаров: {len(unique_perfumes)}")
        self.perfumes = unique_perfumes
        return unique_perfumes
    
    def save_to_json(self, filename: str = 'aroma_euro_perfumes_final.json'):
        """Сохранение в JSON"""
        try:
            data = {
                'metadata': {
                    'source': 'aroma-euro.ru',
                    'catalog_url': 'https://aroma-euro.ru/perfume/',
                    'parsing_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_count': len(self.perfumes),
                    'parser_version': 'fixed-1.0'
                },
                'perfumes': self.perfumes
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Данные сохранены в {filename}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
    
    def print_statistics(self):
        """Вывод статистики"""
        if not self.perfumes:
            print("Нет данных для статистики")
            return
        
        brands = set()
        with_brands = 0
        with_prices = 0
        
        for perfume in self.perfumes:
            if perfume.get('brand'):
                brands.add(perfume['brand'])
                with_brands += 1
            if perfume.get('price'):
                with_prices += 1
        
        print("\n" + "="*60)
        print("ФИНАЛЬНАЯ СТАТИСТИКА ПАРСИНГА AROMA-EURO.RU")
        print("="*60)
        print(f"Всего парфюмов: {len(self.perfumes)}")
        print(f"Уникальных брендов: {len(brands)}")
        print(f"С определенным брендом: {with_brands}")
        print(f"Без бренда: {len(self.perfumes) - with_brands}")
        print(f"С ценами: {with_prices}")
        
        # Примеры
        print("\n" + "="*60)
        print("ПРИМЕРЫ ЗАПИСЕЙ")
        print("="*60)
        for i, perfume in enumerate(self.perfumes[:15], 1):
            print(f"\n{i}. {perfume['full_title']}")
            if perfume.get('brand'):
                print(f"   Бренд: {perfume['brand']}")
            if perfume.get('name'):
                print(f"   Название: {perfume['name']}")
            if perfume.get('price'):
                print(f"   Цена: {perfume['price']}")
            print(f"   URL: {perfume.get('url', '')[:80]}...")
        
        # Топ брендов
        if brands:
            brand_counts = {}
            for perfume in self.perfumes:
                brand = perfume.get('brand')
                if brand:
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            print("\n" + "="*60)
            print("ТОП-15 БРЕНДОВ")
            print("="*60)
            sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
            for i, (brand, count) in enumerate(sorted_brands[:15], 1):
                print(f"{i:2d}. {brand}: {count} товаров")


def main():
    """Основная функция"""
    import sys
    
    parser = FixedParser()
    
    # Опция ограничения страниц для тестирования
    max_pages = None
    if len(sys.argv) > 1:
        try:
            max_pages = int(sys.argv[1])
            print(f"Ограничение: {max_pages} страниц")
        except ValueError:
            print("Неверный аргумент")
    
    try:
        # Парсинг
        perfumes = parser.parse_catalog(max_pages=max_pages)
        
        if perfumes:
            # Сохранение
            parser.save_to_json()
            
            # Статистика
            parser.print_statistics()
            
            print(f"\n{'='*60}")
            print("ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
            print(f"Результат сохранен в файл: aroma_euro_perfumes_final.json")
            print(f"{'='*60}")
        else:
            print("Парсинг не дал результатов")
            
    except KeyboardInterrupt:
        print("\nПарсинг прерван пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main()