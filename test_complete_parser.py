#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Импортируем класс из основного парсера
from complete_parser_with_details import CompleteParfumeParser
import json

def test_complete_parser():
    """Тестирует полноценный парсер на небольшом количестве товаров"""
    
    parser = CompleteParfumeParser(max_workers=2)  # 2 потока для тестирования
    
    print("🧪 ТЕСТИРОВАНИЕ полноценного парсера...")
    print("📍 Тестируем извлечение подробных характеристик")
    print("-" * 50)
    
    try:
        # Получаем только первую страницу каталога
        catalog_url = f"{parser.base_url}/perfume/"
        page_perfumes = parser.parse_catalog_page(catalog_url)
        
        # Берем только первые 5 товаров для тестирования
        test_perfumes = page_perfumes[:5]
        print(f"Тестируем на {len(test_perfumes)} товарах...")
        
        # Извлекаем подробные характеристики
        completed_perfumes = []
        for i, perfume in enumerate(test_perfumes, 1):
            print(f"\n🔍 Обрабатываю товар {i}/{len(test_perfumes)}: {perfume['full_title']}")
            
            # Извлекаем детали
            details = parser.extract_product_details(perfume['url'])
            perfume['details'] = details
            completed_perfumes.append(perfume)
            
            # Выводим результат
            print(f"   ✅ Артикул: {details.get('article', 'Не найден')}")
            print(f"   ✅ Качество: {details.get('quality', 'Не найдено')}")
            print(f"   ✅ Бренд: {details.get('brand_detailed', 'Не найден')}")
            print(f"   ✅ Пол: {details.get('gender', 'Не найден')}")
            print(f"   ✅ Группа аромата: {details.get('fragrance_group', 'Не найдена')}")
            print(f"   ✅ Фабрика: {details.get('factory_detailed', 'Не найдена')}")
        
        # Сохраняем результаты тестирования
        test_data = {
            'test_metadata': {
                'test_date': '2025-07-30',
                'test_count': len(completed_perfumes),
                'test_version': 'complete-test-1.0'
            },
            'test_perfumes': completed_perfumes
        }
        
        with open('test_complete_results.json', 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ ТЕСТ ЗАВЕРШЕН!")
        print(f"📁 Результаты сохранены в: test_complete_results.json")
        print(f"📊 Протестировано товаров: {len(completed_perfumes)}")
        
        # Анализируем результаты
        successful_extractions = sum(1 for p in completed_perfumes if p['details'].get('article'))
        print(f"📈 Успешных извлечений характеристик: {successful_extractions}/{len(completed_perfumes)}")
        
    except Exception as e:
        print(f"\n❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_parser()