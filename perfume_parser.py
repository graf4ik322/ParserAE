#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер каталога парфюмерных композиций с сайта aroma-euro.ru
Извлекает названия и бренды парфюмерии и сохраняет в JSON формате
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('perfume_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PerfumeParser:
    """Класс для парсинга каталога парфюмерии"""
    
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
    
    def extract_perfume_info(self, product_element) -> Optional[Dict[str, str]]:
        """Извлечение информации о парфюме из элемента товара"""
        try:
            perfume_info = {}
            
            # Поиск названия товара
            title_element = product_element.find('a', class_='product-title')
            if not title_element:
                title_element = product_element.find('a', {'class': re.compile(r'.*title.*')})
            if not title_element:
                title_element = product_element.find('h3')
            if not title_element:
                title_element = product_element.find('h4')
            
            if title_element:
                title_text = title_element.get_text(strip=True)
                perfume_info['full_title'] = title_text
                
                # Попытка разделить название и бренд
                brand, name = self.parse_title(title_text)
                perfume_info['brand'] = brand
                perfume_info['name'] = name
            else:
                logger.warning("Не найден элемент с названием товара")
                return None
            
            # Поиск ссылки на товар
            link_element = product_element.find('a')
            if link_element and link_element.get('href'):
                perfume_info['url'] = urljoin(self.base_url, link_element['href'])
            
            # Поиск цены (опционально)
            price_element = product_element.find(class_=re.compile(r'.*price.*'))
            if price_element:
                perfume_info['price'] = price_element.get_text(strip=True)
            
            return perfume_info
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о товаре: {e}")
            return None
    
    def parse_title(self, title: str) -> tuple:
        """Парсинг названия для разделения на бренд и название"""
        title = title.strip()
        
        # Общие паттерны для разделения бренда и названия
        patterns = [
            r'^([A-Za-z\s&\.\-]+?)\s*[-–—]\s*(.+)$',  # Бренд - Название
            r'^([A-Za-z\s&\.\-]+?)\s+(.+)$',          # Бренд Название
            r'^(.+?)\s*\(([^)]+)\).*$',               # Название (Бренд)
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title)
            if match:
                brand = match.group(1).strip()
                name = match.group(2).strip()
                
                # Проверяем, что бренд не слишком длинный
                if len(brand.split()) <= 3:
                    return brand, name
        
        # Если не удалось разделить, возвращаем пустой бренд и полное название
        return "", title
    
    def get_all_pages_urls(self) -> List[str]:
        """Получение ссылок на все страницы каталога"""
        urls = [self.catalog_url]
        
        soup = self.get_page_content(self.catalog_url)
        if not soup:
            return urls
        
        # Поиск пагинации
        pagination = soup.find('div', class_=re.compile(r'.*pagination.*'))
        if pagination:
            page_links = pagination.find_all('a', href=True)
            for link in page_links:
                href = link.get('href')
                if href and 'page-' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)
        
        # Альтернативный поиск ссылок на страницы
        page_links = soup.find_all('a', href=re.compile(r'.*page-\d+.*'))
        for link in page_links:
            href = link.get('href')
            if href:
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
        
        # Различные селекторы для поиска товаров
        product_selectors = [
            'div[class*="product"]',
            'div[class*="item"]',
            'div[class*="card"]',
            '.ty-grid-list__item',
            '.product-item',
            '.grid-item',
        ]
        
        products = []
        for selector in product_selectors:
            found_products = soup.select(selector)
            if found_products:
                products = found_products
                logger.info(f"Найдено товаров с селектором '{selector}': {len(products)}")
                break
        
        if not products:
            # Альтернативный поиск по структуре
            products = soup.find_all('div', {'class': re.compile(r'.*(product|item|card).*')})
            logger.info(f"Найдено товаров альтернативным способом: {len(products)}")
        
        for product in products:
            perfume_info = self.extract_perfume_info(product)
            if perfume_info:
                perfumes.append(perfume_info)
        
        logger.info(f"Извлечено парфюмов со страницы {url}: {len(perfumes)}")
        return perfumes
    
    def parse_all_catalog(self) -> List[Dict[str, str]]:
        """Парсинг всего каталога"""
        logger.info("Начинаю парсинг каталога парфюмерии")
        
        # Получаем все страницы каталога
        page_urls = self.get_all_pages_urls()
        
        all_perfumes = []
        
        for i, url in enumerate(page_urls, 1):
            logger.info(f"Обрабатываю страницу {i}/{len(page_urls)}: {url}")
            
            page_perfumes = self.parse_catalog_page(url)
            all_perfumes.extend(page_perfumes)
            
            # Задержка между запросами
            if i < len(page_urls):
                time.sleep(2)
        
        # Удаление дубликатов
        unique_perfumes = []
        seen_titles = set()
        
        for perfume in all_perfumes:
            title = perfume.get('full_title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_perfumes.append(perfume)
        
        logger.info(f"Всего найдено уникальных парфюмов: {len(unique_perfumes)}")
        self.perfumes = unique_perfumes
        return unique_perfumes
    
    def save_to_json(self, filename: str = 'perfumes_catalog.json') -> None:
        """Сохранение данных в JSON файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.perfumes, f, ensure_ascii=False, indent=2)
            
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
        
        for perfume in self.perfumes:
            brand = perfume.get('brand', '').strip()
            if brand:
                brands.add(brand)
                names_with_brands += 1
            else:
                names_without_brands += 1
        
        return {
            'total_perfumes': len(self.perfumes),
            'unique_brands': len(brands),
            'names_with_brands': names_with_brands,
            'names_without_brands': names_without_brands
        }


def main():
    """Основная функция"""
    parser = PerfumeParser()
    
    try:
        # Парсинг каталога
        perfumes = parser.parse_all_catalog()
        
        if perfumes:
            # Сохранение в JSON
            parser.save_to_json('perfumes_catalog.json')
            
            # Вывод статистики
            stats = parser.get_statistics()
            print("\n=== СТАТИСТИКА ПАРСИНГА ===")
            print(f"Всего парфюмов: {stats.get('total_perfumes', 0)}")
            print(f"Уникальных брендов: {stats.get('unique_brands', 0)}")
            print(f"С определенным брендом: {stats.get('names_with_brands', 0)}")
            print(f"Без бренда: {stats.get('names_without_brands', 0)}")
            
            # Показать первые несколько записей
            print("\n=== ПРИМЕРЫ ЗАПИСЕЙ ===")
            for i, perfume in enumerate(perfumes[:5], 1):
                print(f"{i}. {perfume}")
        else:
            logger.warning("Не удалось извлечь данные о парфюмах")
            
    except KeyboardInterrupt:
        logger.info("Парсинг прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    main()