#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')

from complete_parser_with_details import CompleteParfumeParser
import logging

# Настройка логирования для тестирования
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def test_article_extraction():
    """Тестирует извлечение артикулов из конкретных товаров"""
    
    parser = CompleteParfumeParser(max_workers=1)
    
    # Тестовые URLs
    test_urls = [
        "https://aroma-euro.ru/perfume/escentric-molecules-molecules-02-seluz-352/",
        "https://aroma-euro.ru/perfume/ex-nihilo-narcotique-fleur-luzi-t/",
        "https://aroma-euro.ru/perfume/tom-ford-lost-cherry-motiv-luzi-343713-t/"
    ]
    
    print("🧪 Тестирование извлечения артикулов...")
    print("=" * 60)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{i}. Тестируем: {url}")
        print("-" * 40)
        
        # Извлекаем детали товара
        details = parser.extract_product_details(url)
        
        print(f"📋 Результаты:")
        print(f"   Артикул: '{details.get('article', 'НЕ НАЙДЕН')}'")
        print(f"   Бренд: '{details.get('brand_detailed', '')}'")
        print(f"   Пол: '{details.get('gender', '')}'")
        print(f"   Фабрика: '{details.get('factory_detailed', '')}'")
        print(f"   Качество: '{details.get('quality', '')}'")
        print(f"   Группа: '{details.get('fragrance_group', '')}'")
        
        # Проверяем успешность
        if details.get('article'):
            print(f"✅ УСПЕШНО: Артикул найден!")
        else:
            print(f"❌ ОШИБКА: Артикул НЕ найден!")

if __name__ == "__main__":
    test_article_extraction()