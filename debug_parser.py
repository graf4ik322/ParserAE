#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладочная версия парсера для диагностики
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_parser():
    """Отладка парсера"""
    
    url = "https://aroma-euro.ru/perfume/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    print(f"Загружаю страницу: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        print(f"Статус: {response.status_code}")
        print(f"Размер ответа: {len(response.text)} символов")
        
        # Сохраним HTML для анализа
        with open('debug_page_full.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("HTML сохранен в debug_page_full.html")
        
        # Проверим наличие product-title в тексте
        product_title_count = response.text.count('product-title')
        print(f"Вхождений 'product-title' в HTML: {product_title_count}")
        
        # Найдем все вхождения product-title
        pattern = r'class="product-title"[^>]*>([^<]+)<'
        matches = re.findall(pattern, response.text)
        print(f"Найдено названий товаров через regex: {len(matches)}")
        
        if matches:
            print("\nПервые 5 найденных товаров:")
            for i, title in enumerate(matches[:5], 1):
                print(f"{i}. {title}")
        
        # Теперь попробуем BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем разными способами
        product_links_class = soup.find_all('a', class_='product-title')
        print(f"\nBeautifulSoup .find_all('a', class_='product-title'): {len(product_links_class)}")
        
        product_links_attr = soup.find_all('a', {'class': 'product-title'})
        print(f"BeautifulSoup .find_all('a', {{'class': 'product-title'}}): {len(product_links_attr)}")
        
        # Ищем все ссылки с product-title в атрибутах
        all_links = soup.find_all('a')
        product_title_links = [link for link in all_links if 'product-title' in str(link.get('class', []))]
        print(f"Ссылки с 'product-title' в классах: {len(product_title_links)}")
        
        # Ищем по содержимому class атрибута
        product_links_contains = soup.find_all('a', class_=re.compile(r'.*product-title.*'))
        print(f"BeautifulSoup с regex для класса: {len(product_links_contains)}")
        
        # Попробуем найти любые ссылки на /perfume/
        perfume_links = soup.find_all('a', href=re.compile(r'.*/perfume/[^/]+/?$'))
        print(f"Все ссылки на товары парфюмерии: {len(perfume_links)}")
        
        if perfume_links:
            print("\nПервые 5 ссылок на парфюмерию:")
            for i, link in enumerate(perfume_links[:5], 1):
                title = link.get_text(strip=True)
                href = link.get('href', '')
                classes = link.get('class', [])
                print(f"{i}. {title}")
                print(f"   URL: {href}")
                print(f"   Классы: {classes}")
        
        # Проверим, есть ли JavaScript, который может загружать контент
        scripts = soup.find_all('script')
        js_with_product = [script for script in scripts if script.string and 'product' in script.string.lower()]
        print(f"\nСкриптов с упоминанием 'product': {len(js_with_product)}")
        
        return matches
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return []

if __name__ == "__main__":
    debug_parser()