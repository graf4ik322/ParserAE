#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная версия парсера каталога парфюмерных композиций с сайта aroma-euro.ru
Извлекает названия и бренды парфюмерии и сохраняет в JSON формате
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin, parse_qs, urlparse
import re
from typing import List, Dict, Optional
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aroma_euro_final.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AromaEuroFinalParser:
    """Финальная версия парсера для сайта aroma-euro.ru"""
    
    def __init__(self, base_url: str = "https://aroma-euro.ru"):
        self.base_url = base_url
        self.catalog_url = f"{base_url}/perfume/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': base_url,
        })
        self.perfumes = []
        
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Получение содержимого страницы"""
        try:
            logger.info(f"Загружаю страницу: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Ошибка при загрузке страницы {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке {url}: {e}")
            return None
    
    def parse_title(self, title: str) -> tuple:
        """Парсинг названия для разделения на бренд и название"""
        title = title.strip()
        
        # Удаляем лишние части
        title = re.sub(r'\s*\(мотив\)\s*', '', title)
        title = re.sub(r',\s*[A-Z]+\s*$', '', title)  # Убираем код в конце
        
        # Паттерны для разделения
        patterns = [
            # Tom Ford Black Orchid
            r'^([A-Za-z][A-Za-z\s&\.\-\']+?)\s+([A-Za-z].+)$',
            # Brand - Name
            r'^([A-Za-z][A-Za-z\s&\.\-\']+?)\s*[-–—]\s*(.+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                potential_brand = match.group(1).strip()
                potential_name = match.group(2).strip()
                
                # Проверяем, что это разумное разделение
                if (len(potential_brand.split()) <= 3 and 
                    len(potential_brand) <= 50 and
                    len(potential_name) > 0):
                    return potential_brand, potential_name
        
        # Известные бренды
        known_brands = [
            'Tom Ford', 'Chanel', 'Dior', 'Gucci', 'Prada', 'Versace', 'Armani', 
            'Calvin Klein', 'Hugo Boss', 'Dolce Gabbana', 'Yves Saint Laurent',
            'Creed', 'Maison Margiela', 'Byredo', 'Le Labo', 'Diptyque', 'Hermès',
            'Bottega Veneta', 'Burberry', 'Givenchy', 'Lancome', 'Estee Lauder',
            'Escentric Molecules', 'Montale', 'Mancera', 'Amouage', 'Nasomatto',
            'Serge Lutens', 'Francis Kurkdjian', 'Frederic Malle', 'Penhaligons',
            'Miller Harris', 'Acqua di Parma', 'Annick Goutal', 'L\'Artisan Parfumeur'
        ]
        
        title_lower = title.lower()
        for brand in known_brands:
            if title_lower.startswith(brand.lower()):
                remaining = title[len(brand):].strip()
                if remaining:
                    return brand, remaining
        
        # Если не удалось разделить
        return "", title
    
    def extract_perfume_info(self, product_element) -> Optional[Dict[str, str]]:
        """Извлечение информации о парфюме из элемента товара"""
        try:
            perfume_info = {}
            
            # Поиск названия товара
            title_element = product_element.select_one('.product-title')
            
            if not title_element:
                # Альтернативные селекторы
                title_selectors = [
                    'a[href*="/perfume/"][href$="/"]',
                    'a[href*="/perfume/"]',
                    '.ty-grid-list__item-name a',
                    '.ut2-gl__name a',
                    'h3 a',
                    'h4 a'
                ]
                
                for selector in title_selectors:
                    title_element = product_element.select_one(selector)
                    if title_element:
                        break
            
            if title_element:
                title_text = title_element.get_text(strip=True)
                
                # Фильтруем нерелевантные заголовки
                if any(skip in title_text.lower() for skip in [
                    'парфюмерные масла', 'весь каталог', 'моно ароматы', 
                    'флаконы', 'аксессуары', 'хиты продаж', 'бренды', 'новинки'
                ]):
                    return None
                
                if title_text and len(title_text) > 5:
                    perfume_info['full_title'] = title_text
                    
                    # Разделение на бренд и название
                    brand, name = self.parse_title(title_text)
                    perfume_info['brand'] = brand
                    perfume_info['name'] = name
                    
                    # URL товара
                    if title_element.get('href'):
                        href = title_element['href']
                        # Проверяем, что это ссылка на конкретный товар
                        if '/perfume/' in href and not href.endswith('/perfume/'):
                            perfume_info['url'] = urljoin(self.base_url, href)
                        else:
                            return None
                else:
                    return None
            else:
                return None
            
            # Поиск цены
            price_selectors = [
                '.ty-price-num',
                '.price',
                '.ty-price',
                '[class*="price"]'
            ]
            
            for selector in price_selectors:
                price_element = product_element.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    if price_text and any(char.isdigit() for char in price_text):
                        perfume_info['price'] = price_text
                    break
            
            # Поиск изображения
            img_element = product_element.find('img')
            if img_element and img_element.get('src'):
                src = img_element['src']
                if 'product' in src.lower() or 'perfume' in src.lower():
                    perfume_info['image'] = urljoin(self.base_url, src)
            
            return perfume_info
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о товаре: {e}")
            return None
    
    def get_all_pages_urls(self) -> List[str]:
        """Получение ссылок на все страницы каталога"""
        urls = [self.catalog_url]
        
        soup = self.get_page_content(self.catalog_url)
        if not soup:
            return urls
        
        # Поиск пагинации
        pagination_links = soup.find_all('a', href=re.compile(r'.*page-\d+.*'))
        
        for link in pagination_links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                if full_url not in urls:
                    urls.append(full_url)
        
        # Также ищем числовые ссылки пагинации
        page_numbers = soup.find_all('a', string=re.compile(r'^\d+$'))
        for link in page_numbers:
            href = link.get('href')
            if href and 'page' in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in urls:
                    urls.append(full_url)
        
        logger.info(f"Найдено страниц для парсинга: {len(urls)}")
        return sorted(urls)
    
    def parse_catalog_page(self, url: str) -> List[Dict[str, str]]:
        """Парсинг одной страницы каталога"""
        soup = self.get_page_content(url)
        if not soup:
            return []
        
        perfumes = []
        
        # Ищем все элементы с классом product-title
        product_titles = soup.find_all(class_='product-title')
        logger.info(f"Найдено элементов .product-title: {len(product_titles)}")
        
        # Для каждого заголовка ищем родительский контейнер
        processed_urls = set()
        
        for title_element in product_titles:
            # Находим родительский контейнер товара
            product_container = title_element.find_parent(['div', 'li', 'article'])
            if product_container:
                perfume_info = self.extract_perfume_info(product_container)
                if perfume_info and perfume_info.get('url'):
                    # Избегаем дубликатов по URL
                    if perfume_info['url'] not in processed_urls:
                        processed_urls.add(perfume_info['url'])
                        perfumes.append(perfume_info)
        
        logger.info(f"Извлечено уникальных парфюмов со страницы {url}: {len(perfumes)}")
        return perfumes
    
    def parse_all_catalog(self, max_pages: int = None) -> List[Dict[str, str]]:
        """Парсинг всего каталога"""
        logger.info("Начинаю парсинг каталога парфюмерии aroma-euro.ru")
        
        # Получаем все страницы каталога
        page_urls = self.get_all_pages_urls()
        
        if max_pages:
            page_urls = page_urls[:max_pages]
            logger.info(f"Ограничиваю парсинг до {max_pages} страниц")
        
        all_perfumes = []
        
        for i, url in enumerate(page_urls, 1):
            logger.info(f"Обрабатываю страницу {i}/{len(page_urls)}: {url}")
            
            page_perfumes = self.parse_catalog_page(url)
            all_perfumes.extend(page_perfumes)
            
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
        
        logger.info(f"Всего найдено уникальных парфюмов: {len(unique_perfumes)}")
        self.perfumes = unique_perfumes
        return unique_perfumes
    
    def save_to_json(self, filename: str = 'aroma_euro_catalog.json') -> None:
        """Сохранение данных в JSON файл"""
        try:
            # Подготавливаем данные для сохранения
            save_data = {
                'metadata': {
                    'source': 'aroma-euro.ru',
                    'catalog_url': self.catalog_url,
                    'parsing_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_count': len(self.perfumes),
                    'parser_version': '3.0'
                },
                'perfumes': self.perfumes
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Данные сохранены в файл: {filename}")
            logger.info(f"Количество записей: {len(self.perfumes)}")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в JSON: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Получение статистики по парсингу"""
        if not self.perfumes:
            return {}
        
        brands = set()
        names_with_brands = 0
        names_without_brands = 0
        with_urls = 0
        with_prices = 0
        with_images = 0
        
        for perfume in self.perfumes:
            brand = perfume.get('brand', '').strip()
            if brand:
                brands.add(brand)
                names_with_brands += 1
            else:
                names_without_brands += 1
            
            if perfume.get('url'):
                with_urls += 1
            if perfume.get('price'):
                with_prices += 1
            if perfume.get('image'):
                with_images += 1
        
        return {
            'total_perfumes': len(self.perfumes),
            'unique_brands': len(brands),
            'names_with_brands': names_with_brands,
            'names_without_brands': names_without_brands,
            'with_urls': with_urls,
            'with_prices': with_prices,
            'with_images': with_images
        }


def main():
    """Основная функция"""
    parser = AromaEuroFinalParser()
    
    # Опция для тестирования на ограниченном количестве страниц
    max_pages = None
    if len(sys.argv) > 1:
        try:
            max_pages = int(sys.argv[1])
            print(f"Парсинг ограничен до {max_pages} страниц")
        except ValueError:
            print("Неверный аргумент для количества страниц")
    
    try:
        # Парсинг каталога
        perfumes = parser.parse_all_catalog(max_pages=max_pages)
        
        if perfumes:
            # Сохранение в JSON
            parser.save_to_json('aroma_euro_catalog.json')
            
            # Вывод статистики
            stats = parser.get_statistics()
            print("\n" + "="*60)
            print("СТАТИСТИКА ПАРСИНГА AROMA-EURO.RU")
            print("="*60)
            print(f"Всего парфюмов: {stats.get('total_perfumes', 0)}")
            print(f"Уникальных брендов: {stats.get('unique_brands', 0)}")
            print(f"С определенным брендом: {stats.get('names_with_brands', 0)}")
            print(f"Без бренда: {stats.get('names_without_brands', 0)}")
            print(f"С URL: {stats.get('with_urls', 0)}")
            print(f"С ценами: {stats.get('with_prices', 0)}")
            print(f"С изображениями: {stats.get('with_images', 0)}")
            
            # Показать первые несколько записей
            print("\n" + "="*60)
            print("ПРИМЕРЫ ЗАПИСЕЙ")
            print("="*60)
            for i, perfume in enumerate(perfumes[:10], 1):
                print(f"\n{i}. {perfume.get('full_title', 'Без названия')}")
                if perfume.get('brand'):
                    print(f"   Бренд: {perfume['brand']}")
                if perfume.get('name'):
                    print(f"   Название: {perfume['name']}")
                if perfume.get('price'):
                    print(f"   Цена: {perfume['price']}")
                if perfume.get('url'):
                    print(f"   URL: {perfume['url'][:80]}...")
            
            # Топ брендов
            brand_counts = {}
            for perfume in perfumes:
                brand = perfume.get('brand', '').strip()
                if brand:
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            if brand_counts:
                print("\n" + "="*60)
                print("ТОП-15 БРЕНДОВ")
                print("="*60)
                sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
                for i, (brand, count) in enumerate(sorted_brands[:15], 1):
                    print(f"{i:2d}. {brand}: {count} товаров")
        else:
            logger.warning("Не удалось извлечь данные о парфюмах")
            print("\nПарсинг не дал результатов. Проверьте логи для диагностики.")
            
    except KeyboardInterrupt:
        logger.info("Парсинг прерван пользователем")
        print("\nПарсинг прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"\nКритическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main()