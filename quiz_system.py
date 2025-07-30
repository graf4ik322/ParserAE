#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class QuizCategory(Enum):
    """Категории вопросов квиза"""
    BASIC_INFO = "basic_info"
    PREFERENCES = "preferences"
    LIFESTYLE = "lifestyle"
    OCCASIONS = "occasions"
    EXPERIENCE = "experience"

@dataclass
class QuizQuestion:
    """Структура вопроса квиза"""
    id: str
    category: QuizCategory
    text: str
    options: List[str]
    key: str
    weight: float = 1.0
    depends_on: Optional[str] = None

class PerfumeQuizSystem:
    """Система квиза для подбора парфюмов"""
    
    def __init__(self):
        self.questions = self._create_quiz_questions()
        self.question_flow = self._create_question_flow()
    
    def _create_quiz_questions(self) -> List[QuizQuestion]:
        """Создает все вопросы квиза"""
        return [
            # Базовая информация
            QuizQuestion(
                id="gender",
                category=QuizCategory.BASIC_INFO,
                text="👤 Для кого подбираем аромат?",
                options=[
                    "Для мужчины", 
                    "Для женщины", 
                    "Унисекс (универсальный)", 
                    "Не важно"
                ],
                key="target_gender",
                weight=2.0
            ),
            
            QuizQuestion(
                id="age_group",
                category=QuizCategory.BASIC_INFO,
                text="🎂 Возрастная группа?",
                options=[
                    "18-25 лет (молодежный)", 
                    "25-35 лет (активный)", 
                    "35-50 лет (зрелый)", 
                    "50+ лет (элегантный)"
                ],
                key="age_group",
                weight=1.5
            ),
            
            # Предпочтения по ароматам
            QuizQuestion(
                id="fragrance_family",
                category=QuizCategory.PREFERENCES,
                text="🌸 Какие ароматы вам нравятся?",
                options=[
                    "Цветочные (роза, жасмин, пион)",
                    "Цитрусовые (лимон, апельсин, грейпфрут)",
                    "Древесные (сандал, кедр, пачули)",
                    "Восточные (ваниль, амбра, мускус)",
                    "Свежие (морские, зеленые)",
                    "Фруктовые (ягоды, персик, яблоко)",
                    "Не знаю, помогите выбрать"
                ],
                key="fragrance_family",
                weight=2.5
            ),
            
            QuizQuestion(
                id="intensity",
                category=QuizCategory.PREFERENCES,
                text="💪 Интенсивность аромата?",
                options=[
                    "Легкий, едва заметный",
                    "Умеренный, приятный шлейф",
                    "Насыщенный, яркий",
                    "Очень интенсивный, стойкий"
                ],
                key="intensity",
                weight=2.0
            ),
            
            # Образ жизни
            QuizQuestion(
                id="lifestyle",
                category=QuizCategory.LIFESTYLE,
                text="🏃‍♂️ Ваш образ жизни?",
                options=[
                    "Активный, спортивный",
                    "Деловой, офисный",
                    "Творческий, свободный",
                    "Домашний, спокойный"
                ],
                key="lifestyle",
                weight=1.5
            ),
            
            QuizQuestion(
                id="season",
                category=QuizCategory.OCCASIONS,
                text="🌡️ Для какого сезона?",
                options=[
                    "Весна (свежие, цветочные)",
                    "Лето (легкие, цитрусовые)",
                    "Осень (теплые, пряные)",
                    "Зима (насыщенные, уютные)",
                    "Универсальный (круглый год)"
                ],
                key="season",
                weight=1.8
            ),
            
            QuizQuestion(
                id="time_of_day",
                category=QuizCategory.OCCASIONS,
                text="⏰ Время использования?",
                options=[
                    "Утро/День (бодрящие)",
                    "Вечер/Ночь (соблазнительные)",
                    "Особые случаи (праздничные)",
                    "Ежедневно (универсальные)"
                ],
                key="time_of_day",
                weight=1.7
            ),
            
            QuizQuestion(
                id="occasion",
                category=QuizCategory.OCCASIONS,
                text="🎭 Основные поводы для использования?",
                options=[
                    "Работа, офис",
                    "Свидания, романтика",
                    "Вечеринки, клубы",
                    "Повседневная жизнь",
                    "Особые события"
                ],
                key="occasion",
                weight=1.6
            ),
            
            # Опыт с парфюмерией
            QuizQuestion(
                id="experience",
                category=QuizCategory.EXPERIENCE,
                text="🎓 Ваш опыт с парфюмерией?",
                options=[
                    "Новичок, только начинаю",
                    "Иногда покупаю ароматы",
                    "Разбираюсь в парфюмерии",
                    "Эксперт, коллекционер"
                ],
                key="experience_level",
                weight=1.2
            ),
            
            QuizQuestion(
                id="budget",
                category=QuizCategory.EXPERIENCE,
                text="💰 Бюджет на аромат?",
                options=[
                    "Экономный (до 30₽)",
                    "Средний (30-45₽)",
                    "Выше среднего (45₽+)",
                    "Не важно, главное качество"
                ],
                key="budget",
                weight=1.3
            ),
            
            # Дополнительные предпочтения
            QuizQuestion(
                id="quality_preference",
                category=QuizCategory.PREFERENCES,
                text="⭐ Что важнее?",
                options=[
                    "Качество исполнения",
                    "Оригинальность аромата",
                    "Узнаваемость бренда",
                    "Соотношение цена/качество"
                ],
                key="quality_preference",
                weight=1.4
            ),
            
            QuizQuestion(
                id="factory_preference",
                category=QuizCategory.EXPERIENCE,
                text="🏭 Есть предпочтения по фабрикам?",
                options=[
                    "Givaudan (премиум качество)",
                    "LZ (широкий выбор)",
                    "Argeville (классика)",
                    "SELUZ (эксклюзив)",
                    "Не важно, любая"
                ],
                key="factory_preference",
                weight=1.1
            )
        ]
    
    def _create_question_flow(self) -> Dict[str, List[str]]:
        """Создает логику потока вопросов"""
        return {
            "start": ["gender", "age_group"],
            "basic_complete": ["fragrance_family", "intensity"],
            "preferences_complete": ["lifestyle", "season"],
            "lifestyle_complete": ["time_of_day", "occasion"],
            "occasions_complete": ["experience", "budget"],
            "experience_complete": ["quality_preference", "factory_preference"],
            "end": []
        }
    
    def get_next_question(self, current_answers: Dict[str, str], 
                         current_step: int) -> Optional[QuizQuestion]:
        """Получает следующий вопрос на основе текущих ответов"""
        if current_step >= len(self.questions):
            return None
        
        return self.questions[current_step]
    
    def get_total_questions(self) -> int:
        """Возвращает общее количество вопросов"""
        return len(self.questions)
    
    def analyze_answers(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Анализирует ответы и создает профиль предпочтений"""
        profile = {
            "target_audience": self._analyze_target_audience(answers),
            "fragrance_preferences": self._analyze_fragrance_preferences(answers),
            "usage_context": self._analyze_usage_context(answers),
            "quality_requirements": self._analyze_quality_requirements(answers),
            "weighted_preferences": self._calculate_weighted_preferences(answers)
        }
        
        return profile
    
    def _analyze_target_audience(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует целевую аудиторию"""
        return {
            "gender": answers.get("target_gender", "Не указано"),
            "age_group": answers.get("age_group", "Не указано"),
            "lifestyle": answers.get("lifestyle", "Не указано")
        }
    
    def _analyze_fragrance_preferences(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует предпочтения по ароматам"""
        return {
            "family": answers.get("fragrance_family", "Не указано"),
            "intensity": answers.get("intensity", "Не указано"),
            "quality_focus": answers.get("quality_preference", "Не указано")
        }
    
    def _analyze_usage_context(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует контекст использования"""
        return {
            "season": answers.get("season", "Не указано"),
            "time": answers.get("time_of_day", "Не указано"),
            "occasion": answers.get("occasion", "Не указано")
        }
    
    def _analyze_quality_requirements(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Анализирует требования к качеству"""
        return {
            "budget": answers.get("budget", "Не указано"),
            "experience": answers.get("experience_level", "Не указано"),
            "factory": answers.get("factory_preference", "Не указано")
        }
    
    def _calculate_weighted_preferences(self, answers: Dict[str, str]) -> Dict[str, float]:
        """Вычисляет взвешенные предпочтения"""
        weights = {}
        
        for question in self.questions:
            if question.key in answers:
                answer = answers[question.key]
                weights[f"{question.key}_{answer}"] = question.weight
        
        return weights
    
    def create_recommendation_prompt(self, profile: Dict[str, Any], 
                                   available_perfumes: List[str],
                                   factory_analysis: Dict[str, Any]) -> str:
        """Создает промпт для рекомендаций на основе профиля"""
        
        # Формируем описание профиля пользователя
        target = profile["target_audience"]
        preferences = profile["fragrance_preferences"]
        context = profile["usage_context"]
        quality = profile["quality_requirements"]
        
        profile_description = f"""
ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
• Целевая аудитория: {target['gender']}, {target['age_group']}, {target['lifestyle']}
• Предпочтения: {preferences['family']}, интенсивность {preferences['intensity']}
• Контекст использования: {context['season']}, {context['time']}, для {context['occasion']}
• Требования: бюджет {quality['budget']}, опыт {quality['experience']}, фабрика {quality['factory']}
• Приоритет: {preferences['quality_focus']}
"""
        
        # Ограничиваем список ароматов
        limited_perfumes = available_perfumes[:300]
        
        # Топ фабрик
        top_factories = []
        for factory, data in list(factory_analysis.items())[:8]:
            top_factories.append(f"- {factory}: {data['perfume_count']} ароматов, качество: {', '.join(data.get('quality_levels', ['стандарт'])[:2])}")
        
        prompt = f"""Ты - эксперт-парфюмер и персональный консультант. Подбери идеальные ароматы для клиента.

{profile_description}

ДОСТУПНЫЕ АРОМАТЫ (бренд - название + фабрика):
{chr(10).join(limited_perfumes)}

АНАЛИЗ ФАБРИК:
{chr(10).join(top_factories)}

ЗАДАЧА:
1. Выбери 5-7 ароматов, максимально соответствующих профилю клиента
2. Расположи по приоритету (самый подходящий первым)
3. Для каждого аромата объясни, почему он идеален для этого клиента
4. Укажи лучшие фабрики для каждого типа аромата
5. Дай персональные советы по использованию

КРИТЕРИИ ОТБОРА:
- Соответствие гендеру и возрасту
- Подходящая группа ароматов
- Правильная интенсивность
- Уместность для сезона и времени
- Соответствие бюджету и опыту

Ответ должен быть персонализированным, подробным и практичным."""

        return prompt

def create_quiz_system() -> PerfumeQuizSystem:
    """Фабричная функция для создания системы квиза"""
    return PerfumeQuizSystem()