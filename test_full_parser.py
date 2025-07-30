#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Импортируем класс из основного парсера
from complete_parser_with_details import CompleteParfumeParser
import json

def test_pagination_detection():
    """Тестирует автоматическое определение количества страниц"""
    
    parser = CompleteParfumeParser(max_workers=2)
    
    print("🧪 ТЕСТИРОВАНИЕ автоматического определения страниц...")
    print("📍 Проверяем логику пагинации")
    print("-" * 60)
    
    try:
        # Тестируем только определение страниц
        all_urls = parser.get_all_pages_urls()
        
        print(f"✅ Найдено страниц: {len(all_urls)}")
        print(f"📄 Первые 5 страниц:")
        for i, url in enumerate(all_urls[:5], 1):
            print(f"  {i}. {url}")
        
        if len(all_urls) > 5:
            print(f"  ...")
            print(f"  {len(all_urls)}. {all_urls[-1]}")
        
        # Тестируем парсинг только первых 3 страниц для проверки
        print(f"\n🔍 Тестирую парсинг первых 3 страниц...")
        
        test_urls = all_urls[:3]
        all_perfumes = []
        unique_keys = set()
        
        for i, url in enumerate(test_urls, 1):
            print(f"Обрабатываю страницу {i}/{len(test_urls)}: {url}")
            
            page_perfumes = parser.parse_catalog_page(url)
            print(f"  Найдено товаров: {len(page_perfumes)}")
            
            # Добавляем только уникальные товары
            for perfume in page_perfumes:
                unique_key = perfume['unique_key']
                if unique_key not in unique_keys:
                    unique_keys.add(unique_key)
                    all_perfumes.append(perfume)
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print(f"Всего страниц обнаружено: {len(all_urls)}")
        print(f"Протестировано страниц: {len(test_urls)}")
        print(f"Уникальных товаров на тестовых страницах: {len(all_perfumes)}")
        print(f"Ожидаемое общее количество товаров: ~{len(all_urls) * 40}")
        
        # Анализируем фабрики на тестовых данных
        factories = {}
        brands = {}
        
        for perfume in all_perfumes:
            # Из названия
            factory_from_title = perfume.get('factory', 'Не указана')
            if factory_from_title:
                factories[factory_from_title] = factories.get(factory_from_title, 0) + 1
            
            brand = perfume.get('brand', 'Неизвестный')
            if brand:
                brands[brand] = brands.get(brand, 0) + 1
        
        print(f"\n🏭 ФАБРИКИ (из тестовых данных):")
        for factory, count in sorted(factories.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {factory}: {count} товаров")
        
        print(f"\n🏷️ БРЕНДЫ (из тестовых данных):")
        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {brand}: {count} товаров")
        
        print(f"\n✅ ТЕСТ ЗАВЕРШЕН!")
        print(f"Парсер готов для полного запуска на {len(all_urls)} страницах")
        
        return len(all_urls)
        
    except Exception as e:
        print(f"\n❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    total_pages = test_pagination_detection()
    
    if total_pages > 0:
        print(f"\n🚀 Для запуска полного парсинга выполните:")
        print(f"python3 complete_parser_with_details.py")
        print(f"Будет обработано {total_pages} страниц с ~{total_pages * 40} товарами")