#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовая версия парсера для проверки работоспособности
Парсит только первую страницу каталога
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin

def test_parser():
    """Тестирование парсера на первой странице"""
    
    url = "https://aroma-euro.ru/perfume/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
    }
    
    print(f"Загружаю страницу: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"Статус: {response.status_code}")
        print(f"Размер страницы: {len(response.text)} символов")
        
        # Попробуем найти различные селекторы
        selectors_to_try = [
            '.ty-grid-list__item',
            '.ut2-gl__item', 
            '.ty-column4',
            '.product-item',
            'div[class*="grid"]',
            'div[class*="product"]',
            'div[class*="item"]'
        ]
        
        products = []
        for selector in selectors_to_try:
            found = soup.select(selector)
            print(f"Селектор '{selector}': найдено {len(found)} элементов")
            if found:
                products = found
                break
        
        # Альтернативный поиск по ссылкам
        if not products:
            print("Пробую поиск по ссылкам...")
            product_links = soup.find_all('a', href=re.compile(r'.*/perfume/[^/]+/?$'))
            print(f"Найдено ссылок на товары: {len(product_links)}")
            
            if product_links:
                parents = set()
                for link in product_links[:10]:  # Берем первые 10 для теста
                    parent = link.find_parent(['div', 'li', 'article'])
                    if parent:
                        parents.add(parent)
                products = list(parents)
                print(f"Родительских элементов: {len(products)}")
        
        # Анализ найденных товаров
        perfumes = []
        for i, product in enumerate(products[:10]):  # Анализируем первые 10
            print(f"\n--- ТОВАР {i+1} ---")
            
            # Поиск названия
            title_selectors = [
                '.ty-grid-list__item-name a',
                '.product-title',
                '.ty-product-title',
                'a[class*="product-title"]',
                '.ut2-gl__name a',
                'h3 a',
                'h4 a',
                'a[href*="/perfume/"]'
            ]
            
            title_element = None
            for selector in title_selectors:
                title_element = product.select_one(selector)
                if title_element:
                    print(f"Найден заголовок селектором '{selector}'")
                    break
            
            if not title_element:
                title_element = product.find('a', href=re.compile(r'.*/perfume/.*'))
                if title_element:
                    print("Найден заголовок по ссылке")
            
            if title_element:
                title_text = title_element.get_text(strip=True)
                print(f"Название: {title_text}")
                
                # URL
                url_link = title_element.get('href')
                if url_link:
                    full_url = urljoin("https://aroma-euro.ru", url_link)
                    print(f"URL: {full_url}")
                
                # Попытка разделения на бренд и название
                if ' - ' in title_text:
                    parts = title_text.split(' - ', 1)
                    brand = parts[0].strip()
                    name = parts[1].strip()
                    print(f"Бренд: {brand}")
                    print(f"Парфюм: {name}")
                else:
                    print("Не удалось разделить на бренд и название")
                
                # Поиск цены
                price_selectors = ['.ty-price-num', '.price', '.ty-price', '[class*="price"]']
                for selector in price_selectors:
                    price_element = product.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text(strip=True)
                        if price_text and any(char.isdigit() for char in price_text):
                            print(f"Цена: {price_text}")
                            break
                
                perfume_data = {
                    'full_title': title_text,
                    'url': full_url if url_link else None
                }
                perfumes.append(perfume_data)
            else:
                print("Заголовок не найден")
        
        print(f"\n=== ИТОГО ===")
        print(f"Найдено товаров: {len(perfumes)}")
        
        # Сохранение тестовых данных
        if perfumes:
            with open('test_results.json', 'w', encoding='utf-8') as f:
                json.dump(perfumes, f, ensure_ascii=False, indent=2)
            print("Тестовые данные сохранены в test_results.json")
        
        return perfumes
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return []

if __name__ == "__main__":
    test_parser()