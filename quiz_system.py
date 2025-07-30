#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class QuizCategory(Enum):
    """Категории вопросов квиза"""
    BASIC_PROFILE = "basic_profile"
    PSYCHOLOGICAL_TYPE = "psychological_type"
    SCENT_PREFERENCES = "scent_preferences"
    USAGE_CONTEXT = "usage_context"
    PERSONAL_STYLE = "personal_style"

@dataclass
class QuizQuestion:
    """Структура вопроса квиза"""
    id: str
    category: QuizCategory
    text: str
    options: List[str]
    key: str
    depends_on: Optional[str] = None

class PerfumeQuizSystem:
    """Улучшенная система квиза для максимально точного подбора парфюмов"""
    
    def __init__(self):
        self.questions = self._create_enhanced_quiz_questions()
        self.adaptive_questions = self._create_adaptive_questions()
        self.question_flow = self._create_question_flow()
    
    def _create_enhanced_quiz_questions(self) -> List[QuizQuestion]:
        """Создает научно обоснованные вопросы для точного профилирования"""
        return [
            # Базовый профиль
            QuizQuestion(
                id="target_person",
                category=QuizCategory.BASIC_PROFILE,
                text="👤 Для кого подбираем аромат?",
                options=[
                    "Для себя (женщина)", 
                    "Для себя (мужчина)", 
                    "Для партнера/партнерши",
                    "Универсальный подарок"
                ],
                key="target_person"
            ),
            
            QuizQuestion(
                id="age_personality",
                category=QuizCategory.BASIC_PROFILE,
                text="🎭 Как бы вы описали свой характер?",
                options=[
                    "Энергичный и современный", 
                    "Элегантный и утонченный", 
                    "Загадочный и чувственный",
                    "Спокойный и гармоничный"
                ],
                key="personality_type"
            ),
            
            # Психологический тип (на основе исследования Mintel)
            QuizQuestion(
                id="fragrance_motivation",
                category=QuizCategory.PSYCHOLOGICAL_TYPE,
                text="🧠 Что для вас главное в аромате?",
                options=[
                    "Расслабление и эмоциональное благополучие",
                    "Безопасность и натуральность",
                    "Уникальность и приключения",
                    "Уверенность и привлекательность"
                ],
                key="consumer_type"
            ),
            
            QuizQuestion(
                id="scent_discovery",
                category=QuizCategory.PSYCHOLOGICAL_TYPE,
                text="🌟 Как вы относитесь к новым ароматам?",
                options=[
                    "Обожаю экспериментировать с новинками",
                    "Предпочитаю проверенную классику",
                    "Выбираю по настроению",
                    "Доверяю рекомендациям экспертов"
                ],
                key="innovation_attitude"
            ),
            
            # Предпочтения по ароматам (улучшенная версия)
            QuizQuestion(
                id="scent_family_detailed",
                category=QuizCategory.SCENT_PREFERENCES,
                text="🌺 Какие ароматы вызывают у вас приятные ассоциации?",
                options=[
                    "Цветочная свежесть",
                    "Теплые уютные ноты",
                    "Цитрусовая энергия",
                    "Благородное дерево",
                    "Экзотические пряности",
                    "Морская свежесть"
                ],
                key="scent_family"
            ),
            
            QuizQuestion(
                id="scent_intensity",
                category=QuizCategory.SCENT_PREFERENCES,
                text="💨 Какой должна быть интенсивность аромата?",
                options=[
                    "Деликатная - только для меня",
                    "Умеренная - приятный шлейф",
                    "Заметная - чтобы запомнились",
                    "Интенсивная - яркое заявление"
                ],
                key="intensity_preference"
            ),
            
            QuizQuestion(
                id="longevity_importance",
                category=QuizCategory.SCENT_PREFERENCES,
                text="⏰ Насколько важна стойкость аромата?",
                options=[
                    "Критично важна (8+ часов)",
                    "Важна (4-6 часов)",
                    "Умеренно важна (2-4 часа)",
                    "Не принципиально"
                ],
                key="longevity_need"
            ),
            
            # Контекст использования (оптимизированный)
            QuizQuestion(
                id="primary_usage",
                category=QuizCategory.USAGE_CONTEXT,
                text="🎯 В каких ситуациях будете использовать аромат чаще всего?",
                options=[
                    "Ежедневно на работе",
                    "Особые случаи",
                    "Свидания",
                    "Дома для себя",
                    "Спорт и отдых"
                ],
                key="usage_context"
            ),
            
            QuizQuestion(
                id="seasonal_preference",
                category=QuizCategory.USAGE_CONTEXT,
                text="🌡️ Когда планируете использовать аромат?",
                options=[
                    "Круглый год",
                    "Весна-лето",
                    "Осень-зима",
                    "По настроению"
                ],
                key="seasonal_usage"
            ),
            
            # Личный стиль
            QuizQuestion(
                id="style_association",
                category=QuizCategory.PERSONAL_STYLE,
                text="👗 Ваш стиль в одежде ближе к:",
                options=[
                    "Классический и элегантный",
                    "Современный и минималистичный",
                    "Яркий и творческий",
                    "Удобный и практичный",
                    "Романтичный и женственный"
                ],
                key="style_preference"
            ),
            
            QuizQuestion(
                id="social_impact",
                category=QuizCategory.PERSONAL_STYLE,
                text="👥 Как аромат должен влиять на окружающих?",
                options=[
                    "Создавать атмосферу уюта и доверия",
                    "Подчеркивать мою индивидуальность",
                    "Привлекать внимание и интерес",
                    "Оставаться незаметным для других"
                ],
                key="social_impact"
            ),
            
            QuizQuestion(
                id="quality_priority",
                category=QuizCategory.PERSONAL_STYLE,
                text="⭐ Что для вас приоритетнее?",
                options=[
                    "Уникальность и редкость аромата",
                    "Качество исполнения и стойкость",
                    "Натуральность ингредиентов",
                    "Соотношение цена/качество"
                ],
                key="quality_focus"
            )
        ]
    
    def _create_question_flow(self) -> Dict[str, List[str]]:
        """Создает логику потока вопросов"""
        return {
            "start": ["target_person", "age_personality"],
            "profile_complete": ["fragrance_motivation", "scent_discovery"],
            "psychology_complete": ["scent_family_detailed", "scent_intensity"],
            "scent_preferences_complete": ["longevity_importance", "primary_usage"],
            "usage_complete": ["seasonal_preference", "style_association"],
            "style_complete": ["social_impact", "quality_priority"],
            "end": []
        }
    
    def _create_adaptive_questions(self) -> Dict[str, List[QuizQuestion]]:
        """Создает адаптивные вопросы в зависимости от целевой аудитории"""
        return {
            "Для себя (женщина)": [
                QuizQuestion(
                    id="female_occasion",
                    category=QuizCategory.USAGE_CONTEXT,
                    text="✨ В каких случаях планируете использовать аромат?",
                    options=[
                        "Ежедневно на работу",
                        "Романтические свидания",
                        "Вечерние мероприятия",
                        "Для себя дома"
                    ],
                    key="female_occasion"
                ),
                QuizQuestion(
                    id="female_style",
                    category=QuizCategory.PERSONAL_STYLE,
                    text="👗 Ваш стиль в образах:",
                    options=[
                        "Классика и элегантность",
                        "Романтичность",
                        "Современный минимализм",
                        "Яркость и креативность"
                    ],
                    key="female_style"
                )
            ],
            "Для себя (мужчина)": [
                QuizQuestion(
                    id="male_occasion",
                    category=QuizCategory.USAGE_CONTEXT,
                    text="🎯 Где будете использовать аромат?",
                    options=[
                        "Офис и деловые встречи",
                        "Спорт и активный отдых", 
                        "Вечерние выходы",
                        "Повседневно"
                    ],
                    key="male_occasion"
                ),
                QuizQuestion(
                    id="male_character",
                    category=QuizCategory.PERSONAL_STYLE,
                    text="💪 Как бы вас описали друзья?",
                    options=[
                        "Уверенный лидер",
                        "Надежный друг",
                        "Творческая личность",
                        "Спокойный и мудрый"
                    ],
                    key="male_character"
                )
            ],
            "Для партнера/партнерши": [
                QuizQuestion(
                    id="partner_type",
                    category=QuizCategory.BASIC_PROFILE,
                    text="💕 Ваш партнер:",
                    options=[
                        "Женщина, любит элегантность",
                        "Женщина, предпочитает естественность",
                        "Мужчина, деловой стиль",
                        "Мужчина, спортивный тип"
                    ],
                    key="partner_type"
                ),
                QuizQuestion(
                    id="relationship_stage",
                    category=QuizCategory.PSYCHOLOGICAL_TYPE,
                    text="💖 Какой этап отношений?",
                    options=[
                        "Начало отношений",
                        "Устоявшиеся отношения",
                        "Особый повод/годовщина",
                        "Просто приятный сюрприз"
                    ],
                    key="relationship_stage"
                )
            ],
            "Универсальный подарок": [
                QuizQuestion(
                    id="gift_recipient",
                    category=QuizCategory.BASIC_PROFILE,
                    text="🎁 Для кого подарок?",
                    options=[
                        "Коллега/деловой партнер",
                        "Друг/подруга",
                        "Родственник",
                        "Неизвестно/универсально"
                    ],
                    key="gift_recipient"
                ),
                QuizQuestion(
                    id="gift_budget",
                    category=QuizCategory.PSYCHOLOGICAL_TYPE,
                    text="💰 Каким видите подарок?",
                    options=[
                        "Скромный знак внимания",
                        "Качественный подарок",
                        "Роскошный сюрприз",
                        "Практичный выбор"
                    ],
                    key="gift_budget"
                )
            ]
        }
    
    def get_next_question(self, current_answers: Dict[str, str], 
                         current_step: int) -> Optional[QuizQuestion]:
        """Получает следующий вопрос на основе текущих ответов"""
        # Если это первый вопрос, возвращаем базовый
        if current_step == 0:
            return self.questions[0]
        
        # Если выбрали целевую аудиторию, добавляем адаптивные вопросы
        if current_step == 1 and "target_person" in current_answers:
            target = current_answers["target_person"]
            if target in self.adaptive_questions:
                adaptive_questions = self.adaptive_questions[target]
                if len(adaptive_questions) > 0:
                    return adaptive_questions[0]
        
        if current_step == 2 and "target_person" in current_answers:
            target = current_answers["target_person"]
            if target in self.adaptive_questions:
                adaptive_questions = self.adaptive_questions[target]
                if len(adaptive_questions) > 1:
                    return adaptive_questions[1]
        
        # Для остальных вопросов используем базовую логику, но сдвигаем индекс
        base_index = current_step - 2  # Учитываем 2 адаптивных вопроса
        if base_index >= 0 and base_index + 1 < len(self.questions):
            return self.questions[base_index + 1]
        
        return None
    
    def get_total_questions(self) -> int:
        """Возвращает общее количество вопросов"""
        return len(self.questions) + 2  # Базовые вопросы + 2 адаптивных
    
    def analyze_answers(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Анализирует ответы и создает детальный профиль предпочтений"""
        profile = {
            "basic_profile": self._analyze_basic_profile(answers),
            "psychological_type": self._analyze_psychological_type(answers),
            "scent_preferences": self._analyze_scent_preferences(answers),
            "usage_context": self._analyze_usage_context(answers),
            "personal_style": self._analyze_personal_style(answers),
            "weighted_preferences": self._calculate_weighted_preferences(answers),
            "consumer_archetype": self._determine_consumer_archetype(answers)
        }
        
        return profile
    
    def _analyze_basic_profile(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует базовый профиль"""
        return {
            "target": answers.get("target_person", "Не указано"),
            "personality": answers.get("personality_type", "Не указано")
        }
    
    def _analyze_psychological_type(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует психологический тип потребителя"""
        return {
            "motivation": answers.get("consumer_type", "Не указано"),
            "innovation_attitude": answers.get("innovation_attitude", "Не указано")
        }
    
    def _analyze_scent_preferences(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует предпочтения по ароматам"""
        return {
            "family": answers.get("scent_family", "Не указано"),
            "intensity": answers.get("intensity_preference", "Не указано"),
            "longevity": answers.get("longevity_need", "Не указано")
        }
    
    def _analyze_usage_context(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует контекст использования"""
        return {
            "primary_usage": answers.get("usage_context", "Не указано"),
            "seasonal": answers.get("seasonal_usage", "Не указано")
        }
    
    def _analyze_personal_style(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует личный стиль"""
        return {
            "style": answers.get("style_preference", "Не указано"),
            "social_impact": answers.get("social_impact", "Не указано"),
            "quality_focus": answers.get("quality_focus", "Не указано")
        }
    
    def _determine_consumer_archetype(self, answers: Dict[str, str]) -> str:
        """Определяет архетип потребителя на основе исследований"""
        motivation = answers.get("consumer_type", "")
        
        if "расслабление" in motivation.lower():
            return "Self-care Enthusiast"
        elif "безопасность" in motivation.lower():
            return "Safety Seeker"
        elif "уникальность" in motivation.lower():
            return "Escapist Consumer"
        else:
            return "Confidence Builder"
    
    def _calculate_weighted_preferences(self, answers: Dict[str, str]) -> Dict[str, float]:
        """Упрощенная система предпочтений без весов"""
        # Веса больше не используются, так как рекомендации полностью делает ИИ
        return {}
    
    def create_recommendation_prompt(self, profile: Dict[str, Any], 
                                   available_perfumes: List[str],
                                   factory_analysis: Dict[str, Any]) -> str:
        """Создает улучшенный промпт для рекомендаций на основе детального профиля"""
        
        basic = profile.get("basic_profile", {})
        psychology = profile.get("psychological_type", {})
        scent_prefs = profile.get("scent_preferences", {})
        usage = profile.get("usage_context", {})
        style = profile.get("personal_style", {})
        archetype = profile.get("consumer_archetype", "")
        
        prompt = f"""
Вы - эксперт-парфюмер с 20-летним опытом. Подберите 3-4 идеальных аромата на основе детального профиля клиента:

ПРОФИЛЬ КЛИЕНТА:
🎭 Личность: {basic.get('personality', 'не указано')}
🧠 Тип потребителя: {archetype}
🌺 Ароматические предпочтения: {scent_prefs.get('family', 'не указано')}
💨 Интенсивность: {scent_prefs.get('intensity', 'не указано')}
⏰ Стойкость: {scent_prefs.get('longevity', 'не указано')}
🎯 Основное использование: {usage.get('primary_usage', 'не указано')}
👗 Стиль: {style.get('style', 'не указано')}
👥 Социальное влияние: {style.get('social_impact', 'не указано')}

ТРЕБОВАНИЯ К ОТВЕТУ:
1. Максимум 4 эмодзи в сообщении
2. Блоки текста не более 6 строк
3. Разделители между рекомендациями
4. Прямые ссылки на товары
5. Обоснование выбора для каждого аромата

         ФОРМАТ ОТВЕТА:
         🎯 **Персональные рекомендации**
         
         1. [Бренд] - [Название аромата] ([Фабрика]) [Артикул: XXX]
         Описание и обоснование выбора (2-3 строки)
         🛒 [Ссылка на товар]
         
         ——————————
         
         2. [Бренд] - [Название аромата] ([Фабрика]) [Артикул: XXX]
         Описание и обоснование выбора (2-3 строки)
         🛒 [Ссылка на товар]
         
         ВАЖНО: Обязательно указывайте артикул в квадратных скобках, если он есть в списке товаров!

Доступные ароматы: {str(available_perfumes)[:1000]}...

Анализ фабрик: {str(factory_analysis)[:200]}...
"""
        
        return prompt

def create_quiz_system() -> PerfumeQuizSystem:
    """Создает экземпляр улучшенной системы квиза"""
    return PerfumeQuizSystem()