#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class QuizCategory(Enum):
    """Категории вопросов квиза"""
    TARGET_SELECTION = "target_selection"
    SCENT_PREFERENCES = "scent_preferences"
    INTENSITY_LONGEVITY = "intensity_longevity"
    USAGE_CONTEXT = "usage_context"
    PERSONAL_STYLE = "personal_style"
    OCCASION_MOOD = "occasion_mood"

@dataclass
class QuizQuestion:
    """Структура вопроса квиза"""
    id: str
    category: QuizCategory
    text: str
    options: List[str]
    key: str
    depends_on: Optional[str] = None

class UniversalPerfumeQuizSystem:
    """Универсальная система квиза для точного подбора парфюмов"""
    
    def __init__(self):
        self.questions = self._create_universal_quiz_questions()
        self.target_based_questions = self._create_target_based_questions()
        self.total_questions = 8  # Оптимальное количество для точного определения
    
    def _create_universal_quiz_questions(self) -> List[QuizQuestion]:
        """Создает универсальные вопросы подходящие для любого пользователя"""
        return [
            # Вопрос 1: Определение целевой группы
            QuizQuestion(
                id="target_group",
                category=QuizCategory.TARGET_SELECTION,
                text="👤 Для кого подбираем аромат?",
                options=[
                    "Для себя (женские ароматы)", 
                    "Для себя (мужские ароматы)", 
                    "Для себя (унисекс ароматы)",
                    "В подарок (женщине)",
                    "В подарок (мужчине)",
                    "Универсальный подарок"
                ],
                key="target_group"
            ),
            
            # Вопрос 2: Ароматическая семья (универсальный)
            QuizQuestion(
                id="scent_family",
                category=QuizCategory.SCENT_PREFERENCES,
                text="🌺 Какие ароматы больше всего нравятся?",
                options=[
                    "Свежие и легкие (цитрус, морской бриз)",
                    "Цветочные и нежные (роза, жасмин, пион)",
                    "Древесные и теплые (сандал, кедр, ветивер)",
                    "Пряные и экзотические (корица, кардамон, перец)",
                    "Сладкие и уютные (ваниль, карамель, мед)",
                    "Свежие травяные (лаванда, мята, базилик)"
                ],
                key="scent_family"
            ),
            
            # Вопрос 3: Интенсивность и характер
            QuizQuestion(
                id="intensity_character",
                category=QuizCategory.INTENSITY_LONGEVITY,
                text="💨 Какой характер аромата предпочтительнее?",
                options=[
                    "Деликатный и ненавязчивый",
                    "Умеренный с приятным шлейфом",
                    "Яркий и запоминающийся",
                    "Интенсивный и долгоиграющий"
                ],
                key="intensity_character"
            ),
            
            # Вопрос 4: Основное использование
            QuizQuestion(
                id="primary_usage",
                category=QuizCategory.USAGE_CONTEXT,
                text="🎯 В каких ситуациях чаще всего будет использоваться?",
                options=[
                    "Ежедневно (работа, учеба, повседневные дела)",
                    "Особые случаи (свидания, торжества, встречи)",
                    "Вечерние выходы (театр, рестораны, мероприятия)",
                    "Дома для себя (релакс, уют, личное время)",
                    "Активный отдых (спорт, прогулки, путешествия)"
                ],
                key="primary_usage"
            ),
            
            # Вопрос 5: Сезонность
            QuizQuestion(
                id="seasonal_preference",
                category=QuizCategory.USAGE_CONTEXT,
                text="🌡️ Когда планируется использовать аромат?",
                options=[
                    "Круглый год (универсальный)",
                    "Весна-лето (легкие, освежающие)",
                    "Осень-зима (теплые, уютные)",
                    "По настроению (разные ароматы для разных дней)"
                ],
                key="seasonal_preference"
            ),
            
            # Вопрос 6: Стиль и имидж
            QuizQuestion(
                id="style_image",
                category=QuizCategory.PERSONAL_STYLE,
                text="✨ Какой образ хочется создать с помощью аромата?",
                options=[
                    "Элегантный и утонченный",
                    "Современный и стильный",
                    "Загадочный и чувственный",
                    "Энергичный и жизнерадостный",
                    "Спокойный и гармоничный",
                    "Уникальный и креативный"
                ],
                key="style_image"
            ),
            
            # Вопрос 7: Настроение и эмоции
            QuizQuestion(
                id="mood_emotion",
                category=QuizCategory.OCCASION_MOOD,
                text="🎭 Какие эмоции должен вызывать аромат?",
                options=[
                    "Уверенность и силу",
                    "Спокойствие и умиротворение",
                    "Радость и позитив",
                    "Романтичность и нежность",
                    "Энергию и бодрость",
                    "Загадочность и притягательность"
                ],
                key="mood_emotion"
            ),
            
            # Вопрос 8: Приоритеты при выборе
            QuizQuestion(
                id="selection_priority",
                category=QuizCategory.PERSONAL_STYLE,
                text="⭐ Что важнее всего при выборе аромата?",
                options=[
                    "Уникальность и оригинальность",
                    "Стойкость и долговечность",
                    "Натуральность ингредиентов",
                    "Универсальность и практичность",
                    "Соответствие модным трендам",
                    "Соотношение цена/качество"
                ],
                key="selection_priority"
            )
        ]
    
    def _create_target_based_questions(self) -> Dict[str, List[QuizQuestion]]:
        """Создает дополнительные вопросы в зависимости от целевой группы"""
        return {
            "Для себя (женские ароматы)": [
                QuizQuestion(
                    id="feminine_occasion",
                    category=QuizCategory.OCCASION_MOOD,
                    text="💃 В каких случаях планируется использование?",
                    options=[
                        "Повседневная работа и деловые встречи",
                        "Романтические свидания",
                        "Светские мероприятия и вечеринки",
                        "Домашний уют и личное время"
                    ],
                    key="feminine_occasion"
                )
            ],
            
            "Для себя (мужские ароматы)": [
                QuizQuestion(
                    id="masculine_occasion",
                    category=QuizCategory.OCCASION_MOOD,
                    text="🤵 В каких ситуациях планируется использование?",
                    options=[
                        "Офис и деловая среда",
                        "Спорт и активный отдых",
                        "Вечерние выходы и мероприятия",
                        "Повседневная жизнь"
                    ],
                    key="masculine_occasion"
                )
            ],
            
            "Для себя (унисекс ароматы)": [
                QuizQuestion(
                    id="unisex_preference",
                    category=QuizCategory.SCENT_PREFERENCES,
                    text="🎯 Какой стиль ароматов предпочтительнее?",
                    options=[
                        "Минималистичные и чистые",
                        "Сложные и многогранные",
                        "Природные и натуральные",
                        "Современные и авангардные"
                    ],
                    key="unisex_preference"
                )
            ],
            
            "В подарок (женщине)": [
                QuizQuestion(
                    id="gift_woman_relationship",
                    category=QuizCategory.USAGE_CONTEXT,
                    text="💕 Кому предназначен подарок?",
                    options=[
                        "Партнерше/жене",
                        "Маме/сестре/родственнице",
                        "Подруге/коллеге",
                        "Знакомой (формальный подарок)"
                    ],
                    key="gift_woman_relationship"
                )
            ],
            
            "В подарок (мужчине)": [
                QuizQuestion(
                    id="gift_man_relationship",
                    category=QuizCategory.USAGE_CONTEXT,
                    text="🎁 Кому предназначен подарок?",
                    options=[
                        "Партнеру/мужу",
                        "Папе/брату/родственнику",
                        "Другу/коллеге",
                        "Знакомому (формальный подарок)"
                    ],
                    key="gift_man_relationship"
                )
            ],
            
            "Универсальный подарок": [
                QuizQuestion(
                    id="universal_gift_type",
                    category=QuizCategory.USAGE_CONTEXT,
                    text="🎪 Какой тип подарка предпочтительнее?",
                    options=[
                        "Нейтральный и безопасный выбор",
                        "Качественный и престижный",
                        "Оригинальный и запоминающийся",
                        "Практичный и универсальный"
                    ],
                    key="universal_gift_type"
                )
            ]
        }
    
    def get_next_question(self, current_answers: Dict[str, str], 
                         current_step: int) -> Optional[QuizQuestion]:
        """Получает следующий вопрос на основе текущих ответов"""
        
        # Основные вопросы (0-7)
        if current_step < len(self.questions):
            return self.questions[current_step]
        
        # Дополнительный вопрос на основе целевой группы (шаг 8)
        if current_step == 8 and "target_group" in current_answers:
            target = current_answers["target_group"]
            if target in self.target_based_questions:
                additional_questions = self.target_based_questions[target]
                if additional_questions:
                    return additional_questions[0]
        
        return None
    
    def get_total_questions(self) -> int:
        """Возвращает общее количество вопросов"""
        return 9  # 8 основных + 1 дополнительный
    
    def analyze_answers(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Анализирует ответы и создает детальный профиль предпочтений"""
        profile = {
            "target_analysis": self._analyze_target_group(answers),
            "scent_profile": self._analyze_scent_preferences(answers),
            "usage_profile": self._analyze_usage_context(answers),
            "personality_profile": self._analyze_personality_traits(answers),
            "recommendation_focus": self._determine_recommendation_focus(answers),
            "raw_answers": answers
        }
        
        return profile
    
    def _analyze_target_group(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует целевую группу"""
        target = answers.get("target_group", "")
        
        # Определяем основные параметры
        if "женские" in target:
            gender_focus = "женские"
        elif "мужские" in target:
            gender_focus = "мужские"
        elif "унисекс" in target:
            gender_focus = "унисекс"
        else:
            gender_focus = "универсальные"
        
        is_gift = "подарок" in target.lower()
        
        return {
            "target": target,
            "gender_focus": gender_focus,
            "is_gift": "да" if is_gift else "нет",
            "purchase_type": "подарок" if is_gift else "для себя"
        }
    
    def _analyze_scent_preferences(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует предпочтения по ароматам"""
        family = answers.get("scent_family", "")
        intensity = answers.get("intensity_character", "")
        
        # Классифицируем ароматическую семью
        if "свежие и легкие" in family.lower():
            family_type = "fresh"
        elif "цветочные" in family.lower():
            family_type = "floral"
        elif "древесные" in family.lower():
            family_type = "woody"
        elif "пряные" in family.lower():
            family_type = "spicy"
        elif "сладкие" in family.lower():
            family_type = "gourmand"
        elif "травяные" in family.lower():
            family_type = "aromatic"
        else:
            family_type = "mixed"
        
        # Определяем уровень интенсивности
        if "деликатный" in intensity.lower():
            intensity_level = "light"
        elif "умеренный" in intensity.lower():
            intensity_level = "moderate"
        elif "яркий" in intensity.lower():
            intensity_level = "strong"
        elif "интенсивный" in intensity.lower():
            intensity_level = "intense"
        else:
            intensity_level = "moderate"
        
        return {
            "family": family,
            "family_type": family_type,
            "intensity": intensity,
            "intensity_level": intensity_level
        }
    
    def _analyze_usage_context(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует контекст использования"""
        usage = answers.get("primary_usage", "")
        seasonal = answers.get("seasonal_preference", "")
        
        # Определяем контекст
        if "ежедневно" in usage.lower():
            context = "daily"
        elif "особые случаи" in usage.lower():
            context = "special"
        elif "вечерние" in usage.lower():
            context = "evening"
        elif "дома" in usage.lower():
            context = "home"
        elif "активный" in usage.lower():
            context = "sport"
        else:
            context = "versatile"
        
        # Определяем сезонность
        if "круглый год" in seasonal.lower():
            season = "all_year"
        elif "весна-лето" in seasonal.lower():
            season = "warm"
        elif "осень-зима" in seasonal.lower():
            season = "cold"
        else:
            season = "flexible"
        
        return {
            "primary_usage": usage,
            "usage_context": context,
            "seasonal": seasonal,
            "season_type": season
        }
    
    def _analyze_personality_traits(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует личностные характеристики"""
        style = answers.get("style_image", "")
        mood = answers.get("mood_emotion", "")
        priority = answers.get("selection_priority", "")
        
        return {
            "style_image": style,
            "desired_mood": mood,
            "selection_priority": priority
        }
    
    def _determine_recommendation_focus(self, answers: Dict[str, str]) -> str:
        """Определяет фокус для рекомендаций"""
        target = answers.get("target_group", "")
        family = answers.get("scent_family", "")
        usage = answers.get("primary_usage", "")
        
        # Создаем фокусированный профиль для ИИ
        focus_keywords = []
        
        # Добавляем гендерный фокус
        if "женские" in target:
            focus_keywords.append("feminine")
        elif "мужские" in target:
            focus_keywords.append("masculine")
        elif "унисекс" in target:
            focus_keywords.append("unisex")
        
        # Добавляем ароматический профиль
        if "свежие" in family.lower():
            focus_keywords.append("fresh")
        elif "цветочные" in family.lower():
            focus_keywords.append("floral")
        elif "древесные" in family.lower():
            focus_keywords.append("woody")
        elif "сладкие" in family.lower():
            focus_keywords.append("sweet")
        
        # Добавляем контекст использования
        if "ежедневно" in usage.lower():
            focus_keywords.append("daily_wear")
        elif "особые" in usage.lower():
            focus_keywords.append("special_occasions")
        elif "вечерние" in usage.lower():
            focus_keywords.append("evening_wear")
        
        return " + ".join(focus_keywords)
    
    def create_recommendation_prompt(self, profile: Dict[str, Any], 
                                   available_perfumes: List[str],
                                   factory_analysis: Dict[str, Any]) -> str:
        """Создает улучшенный промпт для рекомендаций на основе универсального профиля"""
        
        target = profile.get("target_analysis", {})
        scent = profile.get("scent_profile", {})
        usage = profile.get("usage_profile", {})
        personality = profile.get("personality_profile", {})
        focus = profile.get("recommendation_focus", "")
        
        prompt = f"""
Вы - эксперт-парфюмер. Подберите 3-4 идеальных аромата на основе детального профиля:

ПРОФИЛЬ КЛИЕНТА:
🎯 Целевая группа: {target.get('target', 'не указано')} ({target.get('gender_focus', 'универсальные')})
🌺 Ароматические предпочтения: {scent.get('family', 'не указано')} (тип: {scent.get('family_type', 'смешанный')})
💨 Интенсивность: {scent.get('intensity', 'не указано')} (уровень: {scent.get('intensity_level', 'умеренный')})
🎯 Использование: {usage.get('primary_usage', 'не указано')} (контекст: {usage.get('usage_context', 'универсальный')})
🌡️ Сезонность: {usage.get('seasonal', 'не указано')} (тип: {usage.get('season_type', 'гибкий')})
✨ Желаемый образ: {personality.get('style_image', 'не указано')}
🎭 Настроение: {personality.get('desired_mood', 'не указано')}
⭐ Приоритет: {personality.get('selection_priority', 'не указано')}

ФОКУС РЕКОМЕНДАЦИИ: {focus}

ТРЕБОВАНИЯ К ОТВЕТУ:
1. Максимум 4 эмодзи в сообщении
2. Краткие блоки текста (не более 5 строк)
3. Обязательно указывайте артикул в формате [Артикул: XXX]
4. Обоснование выбора для каждого аромата (2-3 строки)

ФОРМАТ ОТВЕТА:
🎯 **Персональные рекомендации**

1. [Бренд] [Название] ([Фабрика]) [Артикул: XXX]
Обоснование выбора
🛒 [Ссылка на товар]

———————————

2. [Бренд] [Название] ([Фабрика]) [Артикул: XXX]
Обоснование выбора
🛒 [Ссылка на товар]

Доступные ароматы: {str(available_perfumes)[:1000]}...

Анализ фабрик: {str(factory_analysis)[:200]}...
"""
        
        return prompt

def create_quiz_system() -> UniversalPerfumeQuizSystem:
    """Создает экземпляр улучшенной универсальной системы квиза"""
    return UniversalPerfumeQuizSystem()