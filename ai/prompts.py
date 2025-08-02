#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any

class PromptTemplates:
    """Шаблоны промптов для ИИ"""
    
    @staticmethod
    def create_perfume_question_prompt(user_question: str, perfumes_data: List[Dict[str, Any]]) -> str:
        """Создает промпт для вопроса о парфюмах со ВСЕМИ данными каталога"""
        
        # Формируем оптимизированный список парфюмов (только ключевые поля)
        perfumes_list = []
        for perfume in perfumes_data:
            perfume_line = (
                f"{perfume['name']} | "
                f"{perfume['factory']} | "
                f"{perfume['article']}"
            )
            perfumes_list.append(perfume_line)
        
        perfumes_text = "\n".join(perfumes_list)
        
        prompt = f"""Ты - эксперт-парфюмер с многолетним опытом. Ответь на вопрос клиента, используя ВЕСЬ доступный каталог.

ВОПРОС: "{user_question}"

ВСЕ ДОСТУПНЫЕ АРОМАТЫ (Название | Фабрика | Артикул):
{perfumes_text}

ИНСТРУКЦИИ:
1. Выбери 3-5 наиболее подходящих ароматов из ВСЕГО каталога
2. Для каждого аромата обязательно укажи артикул в формате [Артикул: XXX]
3. Объясни, почему каждый аромат подходит для данного запроса
4. Дай практические советы по использованию каждого аромата
5. Учитывай все характеристики: бренд, пол, ароматическую группу, цену
6. Если есть ценовые предпочтения, учитывай их при выборе
7. Если указан пол, приоритизируй ароматы для этого пола

ФОРМАТ ОТВЕТА:
🎯 **Рекомендуемые ароматы:**

1. **[Название]** ([Фабрика]) [Артикул: XXX]
   - Бренд: [бренд]
   - Пол: [пол]
   - Ароматическая группа: [группа]
   - Цена: [цена]
   - Почему подходит: [объяснение]
   - Советы по использованию: [практические рекомендации]

2. **[Название]** ([Фабрика]) [Артикул: XXX]
   - Бренд: [бренд]
   - Пол: [пол]
   - Ароматическая группа: [группа]
   - Цена: [цена]
   - Почему подходит: [объяснение]
   - Советы по использованию: [практические рекомендации]

💡 **Дополнительные рекомендации:**
[Общие советы, лайфхаки по парфюмерии и рекомендации по выбору]

ВАЖНО: Обязательно указывай артикул в формате [Артикул: XXX] для каждого аромата!"""
        
        return prompt
    
    @staticmethod
    def create_quiz_results_prompt(user_profile: Dict[str, Any], suitable_perfumes: List[Dict[str, Any]]) -> str:
        """Создает промпт для результатов квиза со ВСЕМИ подходящими парфюмами"""
        
        # Анализируем профиль пользователя
        profile_summary = PromptTemplates._analyze_user_profile(user_profile)
        
        # Формируем оптимизированный список подходящих парфюмов (только ключевые поля)
        perfumes_list = []
        for perfume in suitable_perfumes:
            perfume_line = (
                f"{perfume['name']} | "
                f"{perfume['factory']} | "
                f"{perfume['article']}"
            )
            perfumes_list.append(perfume_line)
        
        perfumes_text = "\n".join(perfumes_list)
        
        prompt = f"""Ты - эксперт-парфюмер. Создай персонализированные рекомендации на основе профиля пользователя.

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
{profile_summary}

ВСЕ ПОДХОДЯЩИЕ АРОМАТЫ (Название | Фабрика | Артикул):
{perfumes_text}

ИНСТРУКЦИИ:
1. Выбери 5-7 наиболее подходящих ароматов из ВСЕГО каталога
2. Объясни, почему каждый аромат подходит именно этому профилю
3. Учитывай все характеристики: бренд, пол, ароматическую группу, цену, качество
4. Дай персонализированные рекомендации по использованию
5. Обязательно указывай артикулы в формате [Артикул: XXX]
6. Ранжируй ароматы по степени соответствия профилю

ФОРМАТ ОТВЕТА:
🎯 **Персональные рекомендации для вас:**

1. **[Название]** ([Фабрика]) [Артикул: XXX]
   - Бренд: [бренд]
   - Пол: [пол]
   - Ароматическая группа: [группа]
   - Качество: [качество]
   - Цена: [цена]
   - Почему подходит вашему профилю: [детальное объяснение]
   - Рекомендации по использованию: [персональные советы]

💡 **Общие рекомендации для вашего профиля:**
[Советы по выбору и использованию парфюмов, подходящих именно этому пользователю]

ВАЖНО: Обязательно указывай артикул в формате [Артикул: XXX] для каждого аромата!"""
        
        return prompt
    
    @staticmethod
    def create_fragrance_info_prompt(query: str, matching_perfumes: List[Dict[str, Any]]) -> str:
        """Создает промпт для информации об аромате"""
        
        # Формируем список найденных ароматов
        perfumes_list = []
        for perfume in matching_perfumes:
            perfume_line = (
                f"{perfume['name']} | "
                f"{perfume['factory']} | "
                f"{perfume['article']} | "
                f"{perfume['price_formatted']} | "
                f"{perfume['brand']} | "
                f"{perfume['gender']} | "
                f"{perfume['fragrance_group']} | "
                f"{perfume['quality_level']}"
            )
            perfumes_list.append(perfume_line)
        
        perfumes_text = "\n".join(perfumes_list)
        
        prompt = f"""Ты - эксперт-парфюмер. Предоставь подробную информацию об ароматах по запросу пользователя.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: "{query}"

НАЙДЕННЫЕ АРОМАТЫ (Название | Фабрика | Артикул | Цена | Бренд | Пол | Ароматическая группа | Качество):
{perfumes_text}

ИНСТРУКЦИИ:
1. Предоставь подробную информацию о каждом найденном аромате
2. Расскажи о характеристиках, особенностях и применении
3. Укажи артикулы в формате [Артикул: XXX]
4. Если найдено много ароматов, сгруппируй их по брендам или характеристикам
5. Дай рекомендации по выбору между найденными вариантами

ФОРМАТ ОТВЕТА:
🔍 **Информация об ароматах:**

**[Название]** ([Фабрика]) [Артикул: XXX]
- Бренд: [бренд]
- Пол: [пол]
- Ароматическая группа: [группа]
- Качество: [качество]  
- Цена: [цена]
- Описание: [подробная информация об аромате]
- Рекомендации: [советы по использованию]

💡 **Советы по выбору:**
[Рекомендации, если найдено несколько вариантов]

ВАЖНО: Обязательно указывай артикул в формате [Артикул: XXX] для каждого аромата!"""
        
        return prompt
    
    @staticmethod
    def _analyze_user_profile(profile: Dict[str, Any]) -> str:
        """Анализирует профиль пользователя и создает краткое описание"""
        summary_parts = []
        
        # Пол
        if 'gender' in profile:
            summary_parts.append(f"Пол: {profile['gender']}")
        
        # Возраст
        if 'age_group' in profile:
            summary_parts.append(f"Возрастная группа: {profile['age_group']}")
        
        # Предпочтения по ароматам
        if 'preferred_fragrance_groups' in profile:
            groups = profile['preferred_fragrance_groups']
            if isinstance(groups, list):
                summary_parts.append(f"Предпочитаемые группы ароматов: {', '.join(groups)}")
            else:
                summary_parts.append(f"Предпочитаемые группы ароматов: {groups}")
        
        # Бюджет
        if 'budget' in profile:
            summary_parts.append(f"Бюджет: {profile['budget']}")
        
        # Повод использования
        if 'occasion' in profile:
            summary_parts.append(f"Основные поводы использования: {profile['occasion']}")
        
        # Интенсивность
        if 'intensity_preference' in profile:
            summary_parts.append(f"Предпочитаемая интенсивность: {profile['intensity_preference']}")
        
        # Время года
        if 'season_preference' in profile:
            summary_parts.append(f"Любимое время года для ароматов: {profile['season_preference']}")
        
        # Опыт с парфюмерией
        if 'experience_level' in profile:
            summary_parts.append(f"Опыт с парфюмерией: {profile['experience_level']}")
        
        if not summary_parts:
            return "Профиль пользователя не заполнен"
        
        return "\n".join([f"• {part}" for part in summary_parts])
    
    @staticmethod
    def optimize_large_prompt(perfumes_data: List[Dict[str, Any]], max_perfumes: int = 5000) -> str:
        """Оптимизирует промпт для больших объемов данных"""
        if len(perfumes_data) <= max_perfumes:
            return PromptTemplates._format_all_perfumes_detailed(perfumes_data)
        
        # Группируем по брендам
        grouped_perfumes = PromptTemplates._group_perfumes_by_brand(perfumes_data)
        
        # Создаем краткую сводку
        summary = PromptTemplates._create_brand_summary(grouped_perfumes)
        
        # Добавляем полный список в сжатом формате
        full_list = PromptTemplates._format_all_perfumes_compact(perfumes_data)
        
        return f"{summary}\n\nПОЛНЫЙ СПИСОК АРОМАТОВ:\n{full_list}"
    
    @staticmethod
    def _group_perfumes_by_brand(perfumes_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Группирует парфюмы по брендам"""
        groups = {}
        for perfume in perfumes_data:
            brand = perfume['brand']
            if brand not in groups:
                groups[brand] = []
            groups[brand].append(perfume)
        return groups
    
    @staticmethod
    def _create_brand_summary(grouped_perfumes: Dict[str, List[Dict[str, Any]]]) -> str:
        """Создает краткую сводку по брендам"""
        summary = "КРАТКАЯ СВОДКА ПО БРЕНДАМ:\n"
        
        for brand, perfumes in grouped_perfumes.items():
            summary += f"\n{brand}: {len(perfumes)} ароматов"
            # Добавляем несколько примеров
            for i, perfume in enumerate(perfumes[:3]):
                summary += f"\n  - {perfume['name']} ({perfume['factory']}) [Артикул: {perfume['article']}]"
        
        return summary
    
    @staticmethod
    def _format_all_perfumes_detailed(perfumes_data: List[Dict[str, Any]]) -> str:
        """Форматирует все парфюмы с подробной информацией"""
        perfumes_list = []
        for perfume in perfumes_data:
            perfume_line = (
                f"{perfume['name']} | "
                f"{perfume['factory']} | "
                f"{perfume['article']} | "
                f"{perfume['price_formatted']} | "
                f"{perfume['brand']} | "
                f"{perfume['gender']} | "
                f"{perfume['fragrance_group']}"
            )
            perfumes_list.append(perfume_line)
        return "\n".join(perfumes_list)
    
    @staticmethod
    def _format_all_perfumes_compact(perfumes_data: List[Dict[str, Any]]) -> str:
        """Форматирует все парфюмы в сжатом формате"""
        perfumes_list = []
        for perfume in perfumes_data:
            perfume_line = f"{perfume['name']} ({perfume['brand']}) [{perfume['article']}] - {perfume['price_formatted']}"
            perfumes_list.append(perfume_line)
        return "\n".join(perfumes_list)