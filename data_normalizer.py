#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Dict, List, Set
from collections import defaultdict

class PerfumeDataNormalizer:
    """Нормализация данных парфюмов для оптимизации LLM запросов"""
    
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.perfumes_data = self.load_data()
        
    def load_data(self) -> Dict:
        """Загружает данные из JSON файла"""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_names_only_list(self) -> List[str]:
        """Создает список только названий ароматов (уникальные)"""
        names = set()
        for perfume in self.perfumes_data['perfumes']:
            if perfume.get('name'):
                names.add(perfume['name'].strip())
        return sorted(list(names))
    
    def create_brand_name_list(self) -> List[str]:
        """Создает список бренд + название"""
        items = set()
        for perfume in self.perfumes_data['perfumes']:
            brand = perfume.get('brand', '').strip()
            name = perfume.get('name', '').strip()
            if brand and name:
                items.add(f"{brand} - {name}")
        return sorted(list(items))
    
    def create_name_factory_list(self) -> List[str]:
        """Создает список название + фабрика"""
        items = set()
        for perfume in self.perfumes_data['perfumes']:
            name = perfume.get('name', '').strip()
            factory = perfume.get('factory', '').strip()
            if name:
                if factory:
                    items.add(f"{name} ({factory})")
                else:
                    items.add(f"{name} (фабрика не указана)")
        return sorted(list(items))
    
    def create_brand_name_factory_list(self) -> List[str]:
        """Создает список бренд + название + фабрика"""
        items = set()
        for perfume in self.perfumes_data['perfumes']:
            brand = perfume.get('brand', '').strip()
            name = perfume.get('name', '').strip()
            factory = perfume.get('factory', '').strip()
            if brand and name:
                if factory:
                    items.add(f"{brand} - {name} ({factory})")
                else:
                    items.add(f"{brand} - {name} (фабрика не указана)")
        return sorted(list(items))
    
    def create_full_data_compact(self) -> List[Dict]:
        """Создает компактный список с полными данными для детального анализа"""
        compact_data = []
        for perfume in self.perfumes_data['perfumes']:
            details = perfume.get('details', {})
            item = {
                'brand': perfume.get('brand', ''),
                'name': perfume.get('name', ''),
                'factory': perfume.get('factory', ''),
                'price': perfume.get('price', ''),
                'gender': details.get('gender', ''),
                'fragrance_group': details.get('fragrance_group', ''),
                'quality': details.get('quality', '')
            }
            # Добавляем только если есть основные данные
            if item['brand'] and item['name']:
                compact_data.append(item)
        return compact_data
    
    def create_factory_analysis(self) -> Dict[str, Dict]:
        """Создает анализ фабрик для консультаций"""
        factory_data = defaultdict(lambda: {
            'perfumes': [],
            'brands': set(),
            'avg_price': 0,
            'quality_levels': set(),
            'fragrance_groups': set()
        })
        
        for perfume in self.perfumes_data['perfumes']:
            factory = perfume.get('factory', 'Неизвестная фабрика').strip()
            if not factory:
                factory = 'Неизвестная фабрика'
                
            details = perfume.get('details', {})
            
            factory_data[factory]['perfumes'].append({
                'brand': perfume.get('brand', ''),
                'name': perfume.get('name', ''),
                'price': perfume.get('price', '')
            })
            
            if perfume.get('brand'):
                factory_data[factory]['brands'].add(perfume['brand'])
            
            if details.get('quality'):
                factory_data[factory]['quality_levels'].add(details['quality'])
                
            if details.get('fragrance_group'):
                factory_data[factory]['fragrance_groups'].add(details['fragrance_group'])
        
        # Преобразуем sets в lists для JSON сериализации
        result = {}
        for factory, data in factory_data.items():
            result[factory] = {
                'perfume_count': len(data['perfumes']),
                'brands': sorted(list(data['brands'])),
                'quality_levels': sorted(list(data['quality_levels'])),
                'fragrance_groups': sorted(list(data['fragrance_groups'])),
                'sample_perfumes': data['perfumes'][:5]  # Первые 5 для примера
            }
        
        return result
    
    def create_quiz_reference_data(self) -> Dict:
        """Создает справочные данные для квиза"""
        return {
            'fragrance_groups': sorted(list(set(
                details.get('fragrance_group', '')
                for perfume in self.perfumes_data['perfumes']
                for details in [perfume.get('details', {})]
                if details.get('fragrance_group')
            ))),
            'genders': sorted(list(set(
                details.get('gender', '')
                for perfume in self.perfumes_data['perfumes']
                for details in [perfume.get('details', {})]
                if details.get('gender')
            ))),
            'qualities': sorted(list(set(
                details.get('quality', '')
                for perfume in self.perfumes_data['perfumes']
                for details in [perfume.get('details', {})]
                if details.get('quality')
            ))),
            'brands': sorted(list(set(
                perfume.get('brand', '')
                for perfume in self.perfumes_data['perfumes']
                if perfume.get('brand')
            ))),
            'factories': sorted(list(set(
                perfume.get('factory', '')
                for perfume in self.perfumes_data['perfumes']
                if perfume.get('factory')
            )))
        }
    
    def save_normalized_data(self, output_dir: str = '.'):
        """Сохраняет все нормализованные данные в отдельные файлы"""
        
        # 1. Только названия
        names_only = self.create_names_only_list()
        with open(f'{output_dir}/names_only.json', 'w', encoding='utf-8') as f:
            json.dump(names_only, f, ensure_ascii=False, indent=2)
        
        # 2. Бренд + название
        brand_name = self.create_brand_name_list()
        with open(f'{output_dir}/brand_name.json', 'w', encoding='utf-8') as f:
            json.dump(brand_name, f, ensure_ascii=False, indent=2)
        
        # 3. Название + фабрика
        name_factory = self.create_name_factory_list()
        with open(f'{output_dir}/name_factory.json', 'w', encoding='utf-8') as f:
            json.dump(name_factory, f, ensure_ascii=False, indent=2)
        
        # 4. Бренд + название + фабрика
        brand_name_factory = self.create_brand_name_factory_list()
        with open(f'{output_dir}/brand_name_factory.json', 'w', encoding='utf-8') as f:
            json.dump(brand_name_factory, f, ensure_ascii=False, indent=2)
        
        # 5. Компактные полные данные
        full_compact = self.create_full_data_compact()
        with open(f'{output_dir}/full_data_compact.json', 'w', encoding='utf-8') as f:
            json.dump(full_compact, f, ensure_ascii=False, indent=2)
        
        # 6. Анализ фабрик
        factory_analysis = self.create_factory_analysis()
        with open(f'{output_dir}/factory_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(factory_analysis, f, ensure_ascii=False, indent=2)
        
        # 7. Справочные данные для квиза
        quiz_data = self.create_quiz_reference_data()
        with open(f'{output_dir}/quiz_reference.json', 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, ensure_ascii=False, indent=2)
        
        # Статистика
        stats = {
            'total_perfumes': len(self.perfumes_data['perfumes']),
            'unique_names': len(names_only),
            'brand_name_combinations': len(brand_name),
            'name_factory_combinations': len(name_factory),
            'full_combinations': len(brand_name_factory),
            'compact_records': len(full_compact),
            'factories_analyzed': len(factory_analysis)
        }
        
        with open(f'{output_dir}/normalization_stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return stats

def main():
    """Основная функция для нормализации данных"""
    normalizer = PerfumeDataNormalizer('full_perfumes_catalog_complete.json')
    
    print("🔄 Начинаю нормализацию данных парфюмов...")
    
    stats = normalizer.save_normalized_data()
    
    print("✅ Нормализация завершена!")
    print(f"📊 Статистика:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    print(f"\n📁 Созданные файлы:")
    print(f"  - names_only.json - только названия ароматов")
    print(f"  - brand_name.json - бренд + название")
    print(f"  - name_factory.json - название + фабрика")
    print(f"  - brand_name_factory.json - бренд + название + фабрика")
    print(f"  - full_data_compact.json - компактные полные данные")
    print(f"  - factory_analysis.json - анализ фабрик")
    print(f"  - quiz_reference.json - справочные данные для квиза")
    print(f"  - normalization_stats.json - статистика нормализации")

if __name__ == "__main__":
    main()