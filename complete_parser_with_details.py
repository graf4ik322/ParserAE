#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
import concurrent.futures
from threading import Lock

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteParfumeParser:
    def __init__(self, max_workers=3):
        self.base_url = "https://aroma-euro.ru"
        self.session = requests.Session()
        # Убираем Accept-Encoding для избежания проблем с сжатием
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        self.perfumes = []
        self.max_workers = max_workers
        self.lock = Lock()
        
        # Известные фабрики
        self.known_factories = [
            'Bin Tammam', 'EPS', 'Givaudan', 'Givaudan Premium', 'Givaudan SuperLux',
            'Hamidi', 'Iberchem', 'LZ AG', 'Lz', 'LZ', 'MG Gulcicek', 'Reiha', 
            'Argeville', 'SELUZ', 'Seluz', 'LUZI', 'Luzi'
        ]
        
        # Известные бренды для лучшего парсинга
        self.known_brands = [
            'Tom Ford', 'Chanel', 'Dior', 'Christian Dior', 'Creed', 'Amouage',
            'Maison Francis Kurkdjian', 'Byredo', 'Le Labo', 'Escentric Molecules',
            'Tiziana Terenzi', 'Ex Nihilo', 'Nasomatto', 'Orto Parisi',
            'Giorgio Armani', 'Versace', 'Gucci', 'Prada', 'Yves Saint Laurent',
            'Givenchy', 'Hermès', 'Bulgari', 'Dolce&Gabbana', 'Paco Rabanne',
            'Lacoste', 'Hugo Boss', 'Calvin Klein', 'Antonio Banderas',
            'Lanvin', 'Attar Collection', 'Marc-Antoine Barrois', 'Ajmal',
            'Victoria\'s Secret', 'Thomas Kosmala'
        ]

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Получает содержимое страницы с правильной обработкой кодировки"""
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Получаем сырой контент
            content = response.content
            
            # Декодируем с учетом кодировки
            if response.encoding:
                text = content.decode(response.encoding)
            else:
                text = content.decode('utf-8', errors='ignore')
            
            return BeautifulSoup(text, 'html.parser')
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке {url}: {e}")
            return None

    def extract_factory_info(self, title: str) -> Tuple[str, str, str]:
        """
        Извлекает информацию о фабрике из названия товара
        Возвращает: (оригинальное_название, фабрика, артикул)
        """
        factory = ""
        article = ""
        clean_title = title
        
        # Паттерны для поиска фабрик и артикулов
        patterns = [
            # Givaudan Premium/SuperLux
            r',\s*(Givaudan Premium|Givaudan SuperLux)\s*$',
            # SELUZ
            r',\s*(SELUZ|Seluz)\s*$',
            # Argeville
            r',\s*(Argeville)\s*$',
            # Lz с артикулом
            r',\s*(Lz)\s+(\d+[\d\-T]*)\s*$',
            r',\s*(Lz)\s+(\d+[\d\-/\s]*)\s*$',
            # Просто Lz
            r',\s*(Lz)\s*$',
            # Другие фабрики
            r',\s*(Bin Tammam|EPS|Hamidi|Iberchem|LZ AG|MG Gulcicek|Reiha|LUZI|Luzi)\s*([^,]*?)\s*$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                factory = match.group(1)
                if len(match.groups()) > 1 and match.group(2):
                    article = match.group(2).strip()
                # Удаляем найденную фабрику из названия
                clean_title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
                break
        
        return clean_title, factory, article

    def parse_title_and_brand(self, title: str) -> Tuple[str, str, str, str]:
        """
        Парсит название, извлекая бренд, название аромата, фабрику и артикул
        Возвращает: (бренд, название_аромата, фабрика, артикул)
        """
        # Сначала извлекаем информацию о фабрике
        clean_title, factory, article = self.extract_factory_info(title)
        
        # Убираем "(мотив)" и подобные пометки
        clean_title = re.sub(r'\s*\(мотив[^)]*\)\s*', ' ', clean_title).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title)  # Убираем лишние пробелы
        
        brand = ""
        perfume_name = clean_title
        
        # Ищем известные бренды в начале названия
        for known_brand in sorted(self.known_brands, key=len, reverse=True):
            pattern = rf'^{re.escape(known_brand)}\s+'
            if re.match(pattern, clean_title, re.IGNORECASE):
                brand = known_brand
                perfume_name = re.sub(pattern, '', clean_title, flags=re.IGNORECASE).strip()
                break
        
        # Если бренд не найден, пробуем другие паттерны
        if not brand:
            # Паттерн: "Бренд - Название"
            dash_match = re.match(r'^([^-]+?)\s*-\s*(.+)$', clean_title)
            if dash_match:
                potential_brand = dash_match.group(1).strip()
                if len(potential_brand.split()) <= 3:  # Бренд обычно не более 3 слов
                    brand = potential_brand
                    perfume_name = dash_match.group(2).strip()
            
            # Паттерн: первые 1-2 слова как бренд
            if not brand:
                words = clean_title.split()
                if len(words) >= 2:
                    # Пробуем первые 2 слова
                    potential_brand = ' '.join(words[:2])
                    if any(char.isupper() for char in potential_brand):
                        brand = potential_brand
                        perfume_name = ' '.join(words[2:]) if len(words) > 2 else words[-1]
                    else:
                        # Пробуем первое слово
                        brand = words[0]
                        perfume_name = ' '.join(words[1:])
        
        return brand, perfume_name, factory, article

    def extract_product_details(self, product_url: str) -> Dict[str, str]:
        """
        Извлекает подробные характеристики товара со страницы товара
        """
        details = {
            'article': '',
            'quality': '',
            'brand_detailed': '',
            'gender': '',
            'fragrance_group': '',
            'factory_detailed': ''
        }
        
        soup = self.get_page_content(product_url)
        if not soup:
            return details
        
        # Ищем блок с характеристиками
        features_block = soup.find('div', class_='ty-features-list')
        if not features_block:
            logger.warning(f"Не найден блок характеристик для {product_url}")
            return details
        
        # Извлекаем характеристики - ищем все элементы с классом ty-control-group
        feature_elements = features_block.find_all(['span', 'a'], class_='ty-control-group')
        
        for element in feature_elements:
            # Ищем label и value
            label_elem = element.find('span', class_='ty-product-feature__label')
            if not label_elem:
                continue
                
            label = label_elem.get_text(strip=True).lower()
            
            # Ищем все span элементы в этом элементе
            all_spans = element.find_all('span')
            value = ""
            
            # Значение находится во втором span (не в том, что с классом ty-product-feature__label)
            for span in all_spans:
                if 'ty-product-feature__label' not in span.get('class', []):
                    # Это span со значением
                    em_tag = span.find('em')
                    if em_tag:
                        value = em_tag.get_text(strip=True)
                    else:
                        value = span.get_text(strip=True)
                    break
            
            # Сопоставляем характеристики
            if 'артикул' in label:
                details['article'] = value
            elif 'качество' in label:
                details['quality'] = value
            elif 'бренд' in label:
                details['brand_detailed'] = value
            elif 'пол' in label:
                details['gender'] = value
            elif 'группа аромата' in label:
                details['fragrance_group'] = value
            elif 'фабрика' in label:
                details['factory_detailed'] = value
        
        return details

    def create_unique_key(self, brand: str, name: str, factory: str, article: str) -> str:
        """
        Создает уникальный ключ для товара с учетом фабрики
        """
        # Нормализуем данные
        brand_norm = brand.lower().strip()
        name_norm = name.lower().strip()
        factory_norm = factory.lower().strip()
        
        # Ключ включает бренд, название и фабрику
        return f"{brand_norm}|{name_norm}|{factory_norm}"

    def parse_catalog_page(self, url: str) -> List[Dict[str, str]]:
        """Парсит одну страницу каталога"""
        soup = self.get_page_content(url)
        if not soup:
            return []
        
        perfumes = []
        product_links = soup.find_all('a', class_='product-title')
        logger.info(f"Найдено товаров на странице {url}: {len(product_links)}")
        
        for link in product_links:
            try:
                # Извлекаем название
                title = link.get_text(strip=True)
                if not title:
                    continue
                
                # Парсим название
                brand, perfume_name, factory, article = self.parse_title_and_brand(title)
                
                # URL товара
                product_url = link.get('href')
                if product_url:
                    if product_url.startswith('/'):
                        product_url = urljoin(self.base_url, product_url)
                
                # Ищем цену
                price = ""
                price_element = None
                
                # Ищем цену в родительских элементах
                current = link
                for _ in range(5):  # Максимум 5 уровней вверх
                    current = current.parent
                    if not current:
                        break
                    
                    price_element = current.find(class_=re.compile(r'price'))
                    if price_element:
                        price = price_element.get_text(strip=True)
                        break
                
                perfume_info = {
                    'full_title': title,
                    'brand': brand,
                    'name': perfume_name,
                    'factory': factory,
                    'article': article,
                    'url': product_url,
                    'price': price,
                    'unique_key': self.create_unique_key(brand, perfume_name, factory, article),
                    # Подробные характеристики будут добавлены позже
                    'details': {}
                }
                
                perfumes.append(perfume_info)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке товара: {e}")
                continue
        
        return perfumes

    def process_product_details(self, perfume: Dict[str, str]) -> Dict[str, str]:
        """
        Обрабатывает один товар - извлекает подробные характеристики
        """
        try:
            if perfume.get('url'):
                details = self.extract_product_details(perfume['url'])
                perfume['details'] = details
                
                # Логируем прогресс
                with self.lock:
                    logger.info(f"Обработан товар: {perfume['full_title']}")
                
            return perfume
        except Exception as e:
            logger.error(f"Ошибка при обработке деталей товара {perfume.get('full_title', 'Unknown')}: {e}")
            return perfume

    def get_all_pages_urls(self) -> List[str]:
        """Получает URLs всех страниц каталога"""
        catalog_url = f"{self.base_url}/perfume/"
        soup = self.get_page_content(catalog_url)
        if not soup:
            return [catalog_url]
        
        urls = [catalog_url]
        
        # Ищем пагинацию
        pagination_selectors = [
            'nav.pagination a',
            '.pagination a',
            'a[href*="/perfume/page/"]',
            'a[href*="page="]'
        ]
        
        for selector in pagination_selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href and '/perfume/' in href:
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        if href not in urls:
                            urls.append(href)
                break
        
        logger.info(f"Найдено страниц каталога: {len(urls)}")
        return sorted(urls)

    def parse_all_catalog(self) -> List[Dict[str, str]]:
        """Парсит весь каталог"""
        all_urls = self.get_all_pages_urls()
        all_perfumes = []
        unique_keys = set()
        
        # Этап 1: Сбор базовой информации со всех страниц каталога
        logger.info("🔍 Этап 1: Сбор базовой информации со страниц каталога...")
        for i, url in enumerate(all_urls, 1):
            logger.info(f"Обрабатываю страницу каталога {i}/{len(all_urls)}: {url}")
            
            page_perfumes = self.parse_catalog_page(url)
            
            # Добавляем только уникальные товары (с учетом фабрики)
            for perfume in page_perfumes:
                unique_key = perfume['unique_key']
                if unique_key not in unique_keys:
                    unique_keys.add(unique_key)
                    all_perfumes.append(perfume)
                else:
                    logger.debug(f"Пропущен дубликат: {perfume['full_title']}")
            
            # Задержка между запросами
            if i < len(all_urls):
                time.sleep(1)
        
        logger.info(f"Найдено уникальных товаров: {len(all_perfumes)}")
        
        # Этап 2: Извлечение подробных характеристик с использованием многопоточности
        logger.info("🔍 Этап 2: Извлечение подробных характеристик товаров...")
        
        # Ограничиваем количество товаров для тестирования (можно убрать для полного парсинга)
        # test_perfumes = all_perfumes[:10]  # Только первые 10 для тестирования
        test_perfumes = all_perfumes  # Все товары
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Отправляем задачи на выполнение
            future_to_perfume = {
                executor.submit(self.process_product_details, perfume): perfume 
                for perfume in test_perfumes
            }
            
            # Собираем результаты
            completed_perfumes = []
            for i, future in enumerate(concurrent.futures.as_completed(future_to_perfume), 1):
                try:
                    perfume = future.result()
                    completed_perfumes.append(perfume)
                    
                    if i % 10 == 0:  # Логируем каждые 10 товаров
                        logger.info(f"Обработано товаров: {i}/{len(test_perfumes)}")
                        
                except Exception as e:
                    logger.error(f"Ошибка при обработке товара: {e}")
                
                # Небольшая задержка между запросами
                time.sleep(0.5)
        
        logger.info(f"Всего обработано товаров с подробными характеристиками: {len(completed_perfumes)}")
        return completed_perfumes

    def analyze_data(self, perfumes: List[Dict[str, str]]) -> Dict:
        """Анализирует собранные данные"""
        factory_stats = {}
        brand_stats = {}
        quality_stats = {}
        gender_stats = {}
        fragrance_group_stats = {}
        
        for perfume in perfumes:
            # Статистика по фабрикам
            factory = perfume.get('details', {}).get('factory_detailed') or perfume.get('factory', 'Не указана')
            factory_stats[factory] = factory_stats.get(factory, 0) + 1
            
            # Статистика по брендам
            brand = perfume.get('details', {}).get('brand_detailed') or perfume.get('brand', 'Неизвестный')
            brand_stats[brand] = brand_stats.get(brand, 0) + 1
            
            # Статистика по качеству
            quality = perfume.get('details', {}).get('quality', 'Не указано')
            quality_stats[quality] = quality_stats.get(quality, 0) + 1
            
            # Статистика по полу
            gender = perfume.get('details', {}).get('gender', 'Не указан')
            gender_stats[gender] = gender_stats.get(gender, 0) + 1
            
            # Статистика по группам ароматов
            fragrance_group = perfume.get('details', {}).get('fragrance_group', 'Не указана')
            if fragrance_group and fragrance_group != 'Не указана':
                # Разделяем группы ароматов по запятым
                groups = [g.strip() for g in fragrance_group.split(',')]
                for group in groups:
                    fragrance_group_stats[group] = fragrance_group_stats.get(group, 0) + 1
        
        return {
            'factory_stats': dict(sorted(factory_stats.items(), key=lambda x: x[1], reverse=True)),
            'brand_stats': dict(sorted(brand_stats.items(), key=lambda x: x[1], reverse=True)),
            'quality_stats': dict(sorted(quality_stats.items(), key=lambda x: x[1], reverse=True)),
            'gender_stats': dict(sorted(gender_stats.items(), key=lambda x: x[1], reverse=True)),
            'fragrance_group_stats': dict(sorted(fragrance_group_stats.items(), key=lambda x: x[1], reverse=True)),
            'total_products': len(perfumes),
            'products_with_details': sum(1 for p in perfumes if p.get('details', {}).get('article'))
        }

    def save_to_json(self, filename: str = 'complete_perfumes_catalog.json') -> None:
        """Сохраняет результаты в JSON файл"""
        if not self.perfumes:
            logger.warning("Нет данных для сохранения")
            return
        
        # Анализируем данные
        analysis = self.analyze_data(self.perfumes)
        
        data = {
            'metadata': {
                'source': 'aroma-euro.ru',
                'catalog_url': f'{self.base_url}/perfume/',
                'parsing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': len(self.perfumes),
                'parser_version': 'complete-details-1.0',
                'analysis': analysis
            },
            'perfumes': self.perfumes
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Данные сохранены в файл: {filename}")
            
            # Выводим статистику
            self.print_statistics(analysis)
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла: {e}")

    def print_statistics(self, analysis: Dict) -> None:
        """Выводит подробную статистику"""
        print(f"\n📊 ПОДРОБНАЯ СТАТИСТИКА ПАРСИНГА:")
        print(f"Всего товаров: {analysis['total_products']}")
        print(f"Товаров с подробными характеристиками: {analysis['products_with_details']}")
        
        print(f"\n🏭 ТОП ФАБРИК:")
        for factory, count in list(analysis['factory_stats'].items())[:10]:
            print(f"  {factory}: {count} товаров")
        
        print(f"\n🏷️ ТОП БРЕНДОВ:")
        for brand, count in list(analysis['brand_stats'].items())[:10]:
            print(f"  {brand}: {count} товаров")
        
        print(f"\n⭐ КАЧЕСТВО ТОВАРОВ:")
        for quality, count in analysis['quality_stats'].items():
            print(f"  {quality}: {count} товаров")
        
        print(f"\n👤 РАСПРЕДЕЛЕНИЕ ПО ПОЛУ:")
        for gender, count in analysis['gender_stats'].items():
            print(f"  {gender}: {count} товаров")
        
        print(f"\n🌸 ТОП ГРУПП АРОМАТОВ:")
        for group, count in list(analysis['fragrance_group_stats'].items())[:10]:
            print(f"  {group}: {count} товаров")

def main():
    parser = CompleteParfumeParser(max_workers=3)  # 3 потока для извлечения деталей
    
    print("🚀 Запуск полноценного парсера с подробными характеристиками...")
    print("📍 Сайт: https://aroma-euro.ru/perfume/")
    print("🎯 Цель: полная информация о товарах с детальными характеристиками")
    print("-" * 70)
    
    try:
        # Парсим каталог
        parser.perfumes = parser.parse_all_catalog()
        
        # Сохраняем результаты
        parser.save_to_json()
        
        print("\n✅ Парсинг успешно завершен!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Парсинг прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()