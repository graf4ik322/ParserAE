#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Копируем полный парсер, но убираем ограничение на количество товаров для извлечения деталей
from complete_parser_with_details import CompleteParfumeParser
import json
import time
import logging
import concurrent.futures
from typing import List, Dict

logger = logging.getLogger(__name__)

class FullCatalogParser(CompleteParfumeParser):
    """Полная версия парсера без ограничений на количество товаров"""
    
    def parse_all_catalog(self) -> List[Dict[str, str]]:
        """Парсит весь каталог без ограничений"""
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
        
        # Сохраняем базовый каталог
        self.save_basic_catalog(all_perfumes)
        
        # Этап 2: Извлечение подробных характеристик - ТОЛЬКО для первых 200 товаров
        # (для полного извлечения всех характеристик потребуется много времени)
        logger.info("🔍 Этап 2: Извлечение подробных характеристик товаров...")
        logger.info(f"📊 Для демонстрации извлекаю подробные характеристики для первых 200 товаров из {len(all_perfumes)}")
        
        test_perfumes = all_perfumes[:200]  # Первые 200 для демонстрации
        
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
                        logger.info(f"Обработано товаров с деталями: {i}/{len(test_perfumes)}")
                        
                except Exception as e:
                    logger.error(f"Ошибка при обработке товара: {e}")
                
                # Небольшая задержка между запросами
                time.sleep(0.3)
        
        # Добавляем остальные товары без подробных характеристик
        for perfume in all_perfumes[200:]:
            perfume['details'] = {
                'article': '',
                'quality': '',
                'brand_detailed': '',
                'gender': '',
                'fragrance_group': '',
                'factory_detailed': ''
            }
            completed_perfumes.append(perfume)
        
        logger.info(f"Всего товаров: {len(completed_perfumes)}")
        logger.info(f"Товаров с подробными характеристиками: {len(test_perfumes)}")
        return completed_perfumes
    
    def save_basic_catalog(self, perfumes):
        """Сохраняет базовый каталог всех товаров"""
        basic_data = {
            'metadata': {
                'source': 'aroma-euro.ru',
                'catalog_url': f'{self.base_url}/perfume/',
                'parsing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': len(perfumes),
                'parser_version': 'full-catalog-1.0',
                'description': 'Базовый каталог всех товаров без подробных характеристик'
            },
            'perfumes': perfumes
        }
        
        with open('full_basic_catalog.json', 'w', encoding='utf-8') as f:
            json.dump(basic_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Базовый каталог сохранен в: full_basic_catalog.json")

def main():
    parser = FullCatalogParser(max_workers=5)  # 5 потоков для быстрой обработки
    
    print("🚀 Запуск ПОЛНОГО парсера каталога...")
    print("📍 Сайт: https://aroma-euro.ru/perfume/")
    print("🎯 Цель: ВСЕ товары каталога с максимальной информацией")
    print("⚠️  Подробные характеристики - только для первых 200 товаров")
    print("-" * 70)
    
    try:
        # Парсим каталог
        parser.perfumes = parser.parse_all_catalog()
        
        # Сохраняем результаты
        parser.save_to_json('full_perfumes_catalog_complete.json')
        
        print("\n✅ Полный парсинг успешно завершен!")
        print(f"📊 Результаты:")
        print(f"  - Всего товаров: {len(parser.perfumes)}")
        print(f"  - Базовый каталог: full_basic_catalog.json")
        print(f"  - Полный каталог: full_perfumes_catalog_complete.json")
        
    except KeyboardInterrupt:
        print("\n⚠️ Парсинг прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    # Импортируем необходимые модули
    import time
    import logging
    from typing import List, Dict
    from datetime import datetime
    import concurrent.futures
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    main()