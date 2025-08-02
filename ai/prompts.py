#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any

class PromptTemplates:
    """Шаблоны промптов для ИИ с улучшенным форматированием - БЕЗ ОГРАНИЧЕНИЙ"""
    
    @staticmethod
    def create_perfume_question_prompt(user_question: str, perfumes_data: List[Dict[str, Any]]) -> str:
        """Создает промпт для вопроса о парфюмах со ВСЕМИ данными каталога БЕЗ ОГРАНИЧЕНИЙ"""
        
        # Формируем ПОЛНЫЙ список парфюмов (все парфюмы)
        perfumes_list = []
        factory_analysis = {}
        
        for perfume in perfumes_data:  # БЕЗ ОГРАНИЧЕНИЙ
            perfume_line = (
                f"{perfume['name']} | "
                f"{perfume['factory']} | "
                f"{perfume['article']}"
            )
            perfumes_list.append(perfume_line)
            
            # Анализ фабрик для контекста - ВСЕ фабрики
            factory = perfume['factory']
            if factory not in factory_analysis:
                factory_analysis[factory] = {'perfume_count': 0, 'quality_levels': set()}
            factory_analysis[factory]['perfume_count'] += 1
            if 'quality' in perfume:
                factory_analysis[factory]['quality_levels'].add(perfume['quality'])
        
        # ВЕСЬ список парфюмов - без ограничений
        all_perfumes = perfumes_list
        
        # Создаем ПОЛНУЮ сводку по ВСЕМ фабрикам
        factory_summary = []
        for factory, data in factory_analysis.items():  # ВСЕ фабрики
            quality_info = ', '.join(list(data['quality_levels'])) if data['quality_levels'] else 'стандарт'
            factory_summary.append(
                f"- {factory}: {data['perfume_count']} ароматов, качество: {quality_info}"
            )
        
        prompt = f"""Ты - эксперт-парфюмер и консультант по ароматам с 20-летним опытом.

ВОПРОС КЛИЕНТА: "{user_question}"

ВСЕ ДОСТУПНЫЕ АРОМАТЫ (название + фабрика + артикул):
{chr(10).join(all_perfumes)}

ПОЛНЫЙ АНАЛИЗ ВСЕХ ФАБРИК:
{chr(10).join(factory_summary)}

ИНСТРУКЦИИ:
1. Проанализируй запрос клиента и выбери 3-5 наиболее подходящих ароматов из ВСЕГО каталога
2. Для каждого аромата укажи:
   - Почему он подходит для данного запроса
   - Наилучшую Фабрику-производителя и её особенности
   - Практические советы по использованию
   - ОБЯЗАТЕЛЬНО добавь ссылку на карточку товара в формате: 🛒 [Заказать на aroma-euro.ru](URL)
3. Дай рекомендации по фабрикам - какая лучше передает характер нужного аромата
4. Добавь профессиональные советы и лайфхаки

ВАЖНО: 
- В названии аромата используй точное название из списка для корректного поиска ссылки!
- Обязательно указывай артикул в формате [Артикул: XXX], если он есть в списке товаров!

ФОРМАТ ОТВЕТА:
🎯 **Рекомендуемые ароматы:**

1. **[Название аромата]** ([Фабрика]) [Артикул: XXX]
   - Почему подходит: [объяснение]
   - Особенности фабрики: [анализ]
   - Советы по использованию: [практика]
   - 🛒 [Ссылка на товар]

🏭 **Анализ фабрик:**
[Сравнение и рекомендации по производителям]

💡 **Профессиональные советы:**
[Дополнительные рекомендации]

Ответ должен быть экспертным, практичным и полезным для клиента. Обязательно добавляй ссылки на товары для удобства заказа!"""
        
        return prompt
    
    @staticmethod
    def create_quiz_results_prompt(user_profile: Dict[str, Any], 
                                 suitable_perfumes: List[Dict[str, Any]],
                                 edwards_analysis: Dict[str, Any] = None) -> str:
        """Создает улучшенный промпт для результатов квиза с персонализацией - ВЕСЬ КАТАЛОГ"""
        
        # Анализируем профиль пользователя
        profile_summary = PromptTemplates._analyze_user_profile_detailed(user_profile)
        
        # Формируем ПОЛНЫЙ список ВСЕХ подходящих парфюмов - БЕЗ ОГРАНИЧЕНИЙ
        perfumes_list = []
        factory_analysis = {}
        
        for perfume in suitable_perfumes:  # ВСЕ парфюмы без ограничений
            perfume_line = (
                f"{perfume['name']} | "
                f"{perfume['factory']} | "
                f"{perfume['article']}"
            )
            perfumes_list.append(perfume_line)
            
            # Анализ ВСЕХ фабрик
            factory = perfume['factory']
            if factory not in factory_analysis:
                factory_analysis[factory] = {'perfume_count': 0, 'quality_levels': set()}
            factory_analysis[factory]['perfume_count'] += 1
            if 'quality' in perfume:
                factory_analysis[factory]['quality_levels'].add(perfume['quality'])
        
        # Создаем сводку по ВСЕМ фабрикам - без ограничений
        all_factories = []
        for factory, data in factory_analysis.items():  # ВСЕ фабрики
            quality_info = ', '.join(list(data['quality_levels'])) if data['quality_levels'] else 'стандарт'
            all_factories.append(
                f"- {factory}: {data['perfume_count']} ароматов, качество: {quality_info}"
            )
        
        perfumes_text = "\n".join(perfumes_list)
        
        prompt = f"""Ты - персональный парфюмерный консультант премиум-класса с экспертизой в психологии ароматов.

{profile_summary}

ВСЕ ДОСТУПНЫЕ АРОМАТЫ (бренд - название + фабрика + артикул):
{perfumes_text}

ПОЛНЫЙ АНАЛИЗ ВСЕХ ФАБРИК:
{chr(10).join(all_factories)}

ЗАДАЧА:
Создай персональную подборку из 5-7 ароматов, идеально подходящих этому клиенту из ВСЕГО доступного каталога.

КРИТЕРИИ ОТБОРА:
✅ Полное соответствие гендеру и возрасту
✅ Идеальная группа ароматов для предпочтений
✅ Правильная интенсивность
✅ Сезонная и временная уместность
✅ Соответствие образу жизни и поводам
✅ Попадание в бюджет
✅ Учет опыта пользователя
✅ Предпочтения по фабрикам

ВАЖНО: В названии аромата используй точное название из списка для корректного поиска ссылки!

ФОРМАТ ОТВЕТА:
🎯 **ВАШИ ПЕРСОНАЛЬНЫЕ РЕКОМЕНДАЦИИ**

**1. [НАЗВАНИЕ АРОМАТА]** ([Фабрика]) [Артикул: XXX]
💎 **Почему идеален:** [детальное объяснение соответствия профилю]
🏭 **О фабрике:** [анализ качества исполнения]
💡 **Как использовать:** [персональные советы]
⭐ **Соответствие профилю:** [процент или оценка]
🛒 **[Заказать на aroma-euro.ru](PLACEHOLDER_URL)**

[Повторить для каждого аромата]

🏆 **ФАБРИКИ-ЛИДЕРЫ ДЛЯ ВАШЕГО ПРОФИЛЯ:**
[Анализ лучших производителей под конкретные потребности]

💎 **ПЕРСОНАЛЬНЫЕ СОВЕТЫ:**
[Индивидуальные рекомендации по выбору, нанесению, комбинированию]

🎁 **БОНУСНЫЕ РЕКОМЕНДАЦИИ:**
[Дополнительные советы, альтернативы, сезонные варианты]

Рекомендации должны быть максимально персонализированными, практичными и обоснованными."""
        
        return prompt
    
    @staticmethod
    def create_fragrance_info_prompt(fragrance_query: str) -> str:
        """Создает промпт для получения информации об аромате"""
        
        prompt = f"""Ты - парфюмерный эксперт с энциклопедическими знаниями, автор книг о парфюмерии.

ЗАПРОС: "{fragrance_query}"

ЗАДАЧА:
1. Исправь возможные ошибки в написании названия аромата и бренда
2. Дай исчерпывающее описание аромата в стиле Fragrantica
3. Детально опиши пирамиду ароматов:
   - Верхние ноты (первое впечатление, 15-30 минут)
   - Средние ноты (сердце аромата, 2-4 часа)  
   - Базовые ноты (шлейф, 6+ часов)
4. Расскажи историю создания аромата
5. Опиши в художественном стиле ольфакторные впечатления
6. Укажи идеальные условия использования
7. Определи целевую аудиторию и возрастную группу
8. Дай практические советы по нанесению и комбинированию

ФОРМАТ ОТВЕТА:
🌟 **[Исправленное название аромата]**

📖 **Общее описание:**
[Подробное описание в стиле Fragrantica]

🏺 **Пирамида ароматов:**
• Верхние ноты: [список с описанием]
• Средние ноты: [список с описанием]
• Базовые ноты: [список с описанием]

📚 **История создания:**
[Рассказ о создании, парфюмере, концепции]

🎨 **Ольфакторное впечатление:**
[Художественное описание того, как пахнет аромат]

⏰ **Идеальное время и место:**
• Сезон: [рекомендации]
• Время суток: [рекомендации]
• Мероприятия: [список подходящих событий]

👥 **Целевая аудитория:**
[Пол, возраст, стиль жизни]

💡 **Советы по использованию:**
[Практические рекомендации]

Ответ должен быть подробным, эмоциональным и профессиональным."""

        return prompt

    @staticmethod
    def _analyze_user_profile_detailed(user_profile: Dict[str, Any]) -> str:
        """Создает детальное описание профиля пользователя"""
        
        # Извлекаем основные характеристики
        gender = "универсальный профиль"
        age_experience = "средний опыт"
        personality = "сбалансированная личность"
        
        # Обрабатываем различные форматы данных профиля
        if isinstance(user_profile, dict):
            # Новый формат с блоками
            for key, value in user_profile.items():
                if key == "gender" and isinstance(value, list) and value:
                    gender_map = {"female": "женский", "male": "мужской", "unisex": "унисекс"}
                    gender = gender_map.get(value[0], value[0])
                elif key == "age_experience" and isinstance(value, list) and value:
                    exp_map = {
                        "beginner": "новичок в парфюмерии", 
                        "intermediate": "средний опыт", 
                        "advanced": "продвинутый коллекционер"
                    }
                    age_experience = exp_map.get(value[0], value[0])
                elif key == "personality_type" and isinstance(value, list) and value:
                    pers_map = {
                        "romantic": "романтическая натура",
                        "intellectual": "интеллектуальный тип",
                        "extrovert": "экстравертная личность",
                        "introvert": "интровертная личность"
                    }
                    personality = pers_map.get(value[0], value[0])
        
        # Собираем полное описание профиля
        profile_description = f"""ПРОФИЛЬ КЛИЕНТА:
👤 **Гендерная принадлежность:** {gender}
🎓 **Опыт с парфюмерией:** {age_experience}
🧠 **Тип личности:** {personality}

📋 **Детальные предпочтения:**"""
        
        # Добавляем остальные характеристики
        for key, value in user_profile.items():
            if key not in ["gender", "age_experience", "personality_type"] and isinstance(value, list):
                key_formatted = key.replace("_", " ").title()
                values_formatted = ", ".join(value) if value else "не указано"
                profile_description += f"\n• {key_formatted}: {values_formatted}"
        
        return profile_description

    @staticmethod
    def _analyze_user_profile(user_profile: Dict[str, Any]) -> str:
        """Анализирует профиль пользователя и создает его описание (legacy метод)"""
        profile_lines = []
        
        for key, values in user_profile.items():
            if isinstance(values, list):
                formatted_key = key.replace('_', ' ').title()
                formatted_values = ', '.join(values)
                profile_lines.append(f"• {formatted_key}: {formatted_values}")
            else:
                formatted_key = key.replace('_', ' ').title()
                profile_lines.append(f"• {formatted_key}: {values}")
        
        return "\n".join(profile_lines)