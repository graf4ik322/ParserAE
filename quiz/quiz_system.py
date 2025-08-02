#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, List, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class QuizSystem:
    """Научно обоснованная система квизов на основе Edwards Fragrance Wheel"""
    
    def __init__(self, db_manager, ai_processor=None):
        self.db = db_manager
        self.ai_processor = ai_processor
        self.quiz_questions = self._initialize_quiz_questions()
        logger.info("📝 QuizSystem v3.0 (Edwards Fragrance Wheel) инициализирована")
    
    def _initialize_quiz_questions(self) -> List[Dict[str, Any]]:
        """Инициализирует 15 научно обоснованных вопросов квиза"""
        return [
            # БЛОК 1: ДЕМОГРАФИЧЕСКИЙ (2 вопроса)
            {
                "id": "gender",
                "block": "demographic",
                "question": "👤 **Для кого предназначен аромат?**",
                "type": "single_choice",
                "options": [
                    {
                        "text": "👩 Для меня (женщина)",
                        "value": "female",
                        "keywords": ["женский", "feminine", "floral", "delicate"]
                    },
                    {
                        "text": "👨 Для меня (мужчина)",
                        "value": "male",
                        "keywords": ["мужской", "masculine", "woody", "strong"]
                    },
                    {
                        "text": "🌈 Унисекс",
                        "value": "unisex",
                        "keywords": ["унисекс", "unisex", "neutral", "balanced"]
                    }
                ]
            },
            {
                "id": "age_experience",
                "block": "demographic",
                "question": "🎓 **Ваш опыт с парфюмерией?**",
                "type": "single_choice",
                "options": [
                    {
                        "text": "🌱 Новичок (первые ароматы)",
                        "value": "beginner",
                        "keywords": ["легкий", "простой", "классический", "популярный", "безопасный"]
                    },
                    {
                        "text": "🌿 Имею базовый опыт",
                        "value": "intermediate",
                        "keywords": ["современный", "трендовый", "качественный", "сбалансированный"]
                    },
                    {
                        "text": "🌳 Продвинутый (коллекционер)",
                        "value": "advanced",
                        "keywords": ["нишевый", "эксклюзивный", "сложный", "уникальный", "артистический"]
                    }
                ]
            },

            # БЛОК 2: ПСИХОЛОГИЧЕСКИЙ (3 вопроса)
            {
                "id": "personality_type",
                "block": "psychological",
                "question": "🧠 **Какой тип личности вам ближе?**",
                "type": "single_choice",
                "options": [
                    {
                        "text": "💕 Романтик",
                        "value": "romantic",
                        "keywords": ["романтичный", "чувственный", "нежный", "floral", "rose", "jasmine"]
                    },
                    {
                        "text": "🎓 Интеллектуал",
                        "value": "intellectual",
                        "keywords": ["сложный", "утонченный", "изысканный", "green", "herbaceous"]
                    },
                    {
                        "text": "🎉 Экстраверт",
                        "value": "extrovert",
                        "keywords": ["яркий", "заметный", "bold", "oriental", "spicy"]
                    },
                    {
                        "text": "🤫 Интроверт",
                        "value": "introvert",
                        "keywords": ["спокойный", "деликатный", "subtle", "woody", "musky"]
                    },
                    {
                        "text": "🔬 Логик-аналитик",
                        "value": "analytical",
                        "keywords": ["структурированный", "чистый", "minimalistic", "aquatic", "ozonic"]
                    }
                ]
            },
            {
                "id": "lifestyle",
                "block": "psychological", 
                "question": "🏃 **Опишите ваш образ жизни:**",
                "type": "single_choice",
                "options": [
                    {
                        "text": "⚡ Активный и динамичный",
                        "value": "active",
                        "keywords": ["энергичный", "спортивный", "fresh", "citrus", "energizing"]
                    },
                    {
                        "text": "🧘 Спокойный и размеренный",
                        "value": "calm",
                        "keywords": ["расслабляющий", "мягкий", "comforting", "vanilla", "amber"]
                    },
                    {
                        "text": "🎨 Творческий и артистичный",
                        "value": "creative",
                        "keywords": ["креативный", "необычный", "artistic", "incense", "patchouli"]
                    },
                    {
                        "text": "💼 Деловой и профессиональный",
                        "value": "professional",
                        "keywords": ["строгий", "элегантный", "sophisticated", "cedar", "sandalwood"]
                    }
                ]
            },
            {
                "id": "usage_time",
                "block": "psychological",
                "question": "⏰ **В какое время дня планируете использовать аромат?**",
                "type": "multiple_choice",
                "options": [
                    {
                        "text": "🌅 Утром и днем",
                        "value": "day",
                        "keywords": ["дневной", "light", "fresh", "citrus", "green"]
                    },
                    {
                        "text": "🌃 Вечером",
                        "value": "evening",
                        "keywords": ["вечерний", "intense", "oriental", "woody", "amber"]
                    },
                    {
                        "text": "✨ На особые случаи",
                        "value": "special",
                        "keywords": ["праздничный", "luxurious", "sophisticated", "oud", "rare"]
                    },
                    {
                        "text": "🔄 Универсально",
                        "value": "universal",
                        "keywords": ["универсальный", "versatile", "balanced", "moderate"]
                    }
                ]
            },

            # БЛОК 3: LIFESTYLE (4 вопроса)
            {
                "id": "occasions",
                "block": "lifestyle",
                "question": "🎭 **Для каких случаев нужен аромат?**",
                "type": "multiple_choice",
                "options": [
                    {
                        "text": "🏢 Повседневная работа/учеба",
                        "value": "work",
                        "keywords": ["офисный", "деликатный", "professional", "clean", "subtle"]
                    },
                    {
                        "text": "💕 Романтические встречи",
                        "value": "romantic",
                        "keywords": ["соблазнительный", "чувственный", "seductive", "rose", "ylang-ylang"]
                    },
                    {
                        "text": "🎉 Вечеринки и мероприятия",
                        "value": "party",
                        "keywords": ["яркий", "запоминающийся", "party", "gourmand", "sweet"]
                    },
                    {
                        "text": "🏃 Спорт и активность",
                        "value": "sport",
                        "keywords": ["свежий", "легкий", "sport", "aquatic", "marine"]
                    },
                    {
                        "text": "🛋️ Отдых и релакс",
                        "value": "relaxation",
                        "keywords": ["успокаивающий", "комфортный", "relaxing", "lavender", "chamomile"]
                    }
                ]
            },
            {
                "id": "style_preference",
                "block": "lifestyle",
                "question": "👔 **Ваш стиль в одежде:**",
                "type": "single_choice",
                "options": [
                    {
                        "text": "👑 Классический и элегантный",
                        "value": "classic",
                        "keywords": ["классический", "элегантный", "timeless", "chypre", "aldehydic"]
                    },
                    {
                        "text": "🔥 Модный и трендовый",
                        "value": "trendy",
                        "keywords": ["модный", "современный", "trendy", "fruity", "synthetic"]
                    },
                    {
                        "text": "👕 Casual и комфортный",
                        "value": "casual",
                        "keywords": ["простой", "комфортный", "easy-going", "cotton", "clean"]
                    },
                    {
                        "text": "⚡ Экстравагантный и яркий",
                        "value": "bold",
                        "keywords": ["яркий", "смелый", "extravagant", "leather", "tobacco"]
                    }
                ]
            },
            {
                "id": "budget_category",
                "block": "lifestyle",
                "question": "💰 **Предпочтительная ценовая категория:**",
                "type": "single_choice",
                "options": [
                    {
                        "text": "💸 Доступная (масс-маркет)",
                        "value": "mass_market",
                        "keywords": ["популярный", "доступный", "commercial", "mainstream"]
                    },
                    {
                        "text": "💎 Средняя (селективная)",
                        "value": "selective",
                        "keywords": ["качественный", "селективный", "premium", "boutique"]
                    },
                    {
                        "text": "👑 Высокая (люкс/нишевая)",
                        "value": "luxury",
                        "keywords": ["люксовый", "нишевый", "luxury", "exclusive", "artisanal"]
                    }
                ]
            },
            {
                "id": "longevity_preference",
                "block": "lifestyle",
                "question": "⏱️ **Предпочтительная стойкость аромата:**",
                "type": "single_choice",
                "options": [
                    {
                        "text": "🌸 Легкий и ненавязчивый (2-4 часа)",
                        "value": "light",
                        "keywords": ["легкий", "деликатный", "eau_de_cologne", "citrus", "aromatic"]
                    },
                    {
                        "text": "⚖️ Умеренной стойкости (4-6 часов)",
                        "value": "moderate",
                        "keywords": ["умеренный", "сбалансированный", "eau_de_toilette", "balanced"]
                    },
                    {
                        "text": "💪 Стойкий и насыщенный (8+ часов)",
                        "value": "long_lasting",
                        "keywords": ["стойкий", "насыщенный", "eau_de_parfum", "intense", "heavy"]
                    }
                ]
            },

            # БЛОК 4: СЕНСОРНЫЙ (3 вопроса) - Edwards Fragrance Wheel
            {
                "id": "fragrance_families",
                "block": "sensory",
                "question": "🌸 **Какие ароматические семейства вам нравятся? (Edwards Wheel)**",
                "type": "multiple_choice",
                "options": [
                    {
                        "text": "🌸 Цветочные (роза, жасмин, пион)",
                        "value": "floral",
                        "keywords": ["floral", "rose", "jasmine", "peony", "lily", "romantic"]
                    },
                    {
                        "text": "🌟 Восточные/Амбровые (ваниль, амбра, мускус)",
                        "value": "oriental",
                        "keywords": ["oriental", "amber", "vanilla", "musk", "resin", "warm"]
                    },
                    {
                        "text": "🌳 Древесные (сандал, кедр, дуб)",
                        "value": "woody",
                        "keywords": ["woody", "sandalwood", "cedar", "oak", "pine", "forest"]
                    },
                    {
                        "text": "💧 Свежие (цитрус, зеленые, водные)",
                        "value": "fresh",
                        "keywords": ["fresh", "citrus", "green", "aquatic", "marine", "clean"]
                    }
                ]
            },
            {
                "id": "intensity_preference",
                "block": "sensory",
                "question": "📶 **Предпочтительная интенсивность аромата:**",
                "type": "single_choice",
                "options": [
                    {
                        "text": "🌸 Деликатная и тонкая",
                        "value": "delicate",
                        "keywords": ["деликатный", "тонкий", "subtle", "soft", "gentle"]
                    },
                    {
                        "text": "⚖️ Умеренная и сбалансированная",
                        "value": "moderate",
                        "keywords": ["умеренный", "сбалансированный", "moderate", "balanced"]
                    },
                    {
                        "text": "🔥 Яркая и насыщенная",
                        "value": "intense",
                        "keywords": ["яркий", "насыщенный", "intense", "bold", "powerful"]
                    }
                ]
            },
            {
                "id": "seasonal_preference",
                "block": "sensory",
                "question": "🌍 **В какие сезоны планируете носить аромат?**",
                "type": "multiple_choice",
                "options": [
                    {
                        "text": "🌸 Весна",
                        "value": "spring",
                        "keywords": ["весенний", "свежий", "green", "floral", "light"]
                    },
                    {
                        "text": "☀️ Лето",
                        "value": "summer",
                        "keywords": ["летний", "легкий", "citrus", "aquatic", "fresh"]
                    },
                    {
                        "text": "🍂 Осень",
                        "value": "autumn",
                        "keywords": ["осенний", "теплый", "spicy", "woody", "amber"]
                    },
                    {
                        "text": "❄️ Зима",
                        "value": "winter",
                        "keywords": ["зимний", "согревающий", "oriental", "heavy", "intense"]
                    }
                ]
            },

            # БЛОК 5: ЭМОЦИОНАЛЬНО-АССОЦИАТИВНЫЙ (3 вопроса)
            {
                "id": "desired_mood",
                "block": "emotional",
                "question": "😊 **Какие настроения и эмоции хотите передать?**",
                "type": "multiple_choice",
                "options": [
                    {
                        "text": "💪 Уверенность и силу",
                        "value": "confidence",
                        "keywords": ["уверенный", "сильный", "powerful", "dominant", "leader"]
                    },
                    {
                        "text": "💕 Романтику и нежность",
                        "value": "romance",
                        "keywords": ["романтичный", "нежный", "romantic", "tender", "loving"]
                    },
                    {
                        "text": "👑 Элегантность и изысканность",
                        "value": "elegance",
                        "keywords": ["элегантный", "изысканный", "sophisticated", "refined", "classy"]
                    },
                    {
                        "text": "⚡ Энергию и жизнерадостность",
                        "value": "energy",
                        "keywords": ["энергичный", "жизнерадостный", "energetic", "vibrant", "happy"]
                    },
                    {
                        "text": "🧘 Спокойствие и гармонию",
                        "value": "calm",
                        "keywords": ["спокойный", "гармоничный", "peaceful", "serene", "balanced"]
                    }
                ]
            },
            {
                "id": "scent_memories",
                "block": "emotional",
                "question": "🌺 **Какие ароматические воспоминания вам приятны?**",
                "type": "multiple_choice",
                "options": [
                    {
                        "text": "🌷 Цветущий сад весной",
                        "value": "garden",
                        "keywords": ["цветочный", "природный", "garden", "blooming", "natural"]
                    },
                    {
                        "text": "🏠 Уютный дом с выпечкой",
                        "value": "home_comfort",
                        "keywords": ["уютный", "сладкий", "gourmand", "vanilla", "caramel"]
                    },
                    {
                        "text": "🌲 Прогулка по лесу",
                        "value": "forest",
                        "keywords": ["лесной", "древесный", "forest", "pine", "earthy"]
                    },
                    {
                        "text": "🌊 Морской берег",
                        "value": "ocean",
                        "keywords": ["морской", "свежий", "marine", "salty", "breeze"]
                    },
                    {
                        "text": "🕌 Восточный базар",
                        "value": "oriental_market",
                        "keywords": ["восточный", "пряный", "spicy", "exotic", "incense"]
                    }
                ]
            },
            {
                "id": "color_associations",
                "block": "emotional",
                "question": "🎨 **Какие цвета ассоциируются с вашим идеальным ароматом?**",
                "type": "multiple_choice",
                "options": [
                    {
                        "text": "⚪ Белый и светлые оттенки",
                        "value": "white_light",
                        "keywords": ["чистый", "невинный", "clean", "pure", "innocent"]
                    },
                    {
                        "text": "🌸 Розовый и персиковый",
                        "value": "pink_peach",
                        "keywords": ["нежный", "женственный", "gentle", "feminine", "soft"]
                    },
                    {
                        "text": "🟡 Золотой и янтарный",
                        "value": "gold_amber",
                        "keywords": ["теплый", "роскошный", "warm", "luxurious", "rich"]
                    },
                    {
                        "text": "🟢 Зеленый и природные тона",
                        "value": "green_natural",
                        "keywords": ["природный", "свежий", "natural", "green", "herbal"]
                    },
                    {
                        "text": "🔵 Синий и морские оттенки",
                        "value": "blue_marine",
                        "keywords": ["прохладный", "свежий", "cool", "aquatic", "marine"]
                    },
                    {
                        "text": "⚫ Темные и глубокие цвета",
                        "value": "dark_deep",
                        "keywords": ["глубокий", "таинственный", "deep", "mysterious", "intense"]
                    }
                ]
            }
        ]

    async def start_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает квиз для пользователя"""
        user_id = update.effective_user.id
        
        # Сбрасываем прогресс квиза
        context.user_data['quiz_step'] = 0
        context.user_data['quiz_answers'] = {}
        
        await self._send_question(update, context, 0)
        
        logger.info(f"🎯 Пользователь {user_id} начал новый квиз (v3.0 Edwards Wheel)")

    async def handle_quiz_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback'ов квиза"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Получаем текущие данные
        current_step = context.user_data.get('quiz_step', 0)
        current_answers = context.user_data.get('quiz_answers', {})
        
        logger.info(f"Quiz callback: user={user_id}, step={current_step}, data={query.data}")
        
        try:
            if query.data == "quiz_next":
                # Переход к следующему вопросу
                next_step = current_step + 1
                if next_step < len(self.quiz_questions):
                    context.user_data['quiz_step'] = next_step
                    await self._send_question(update, context, next_step)
                else:
                    await self._finish_quiz(update, context, current_answers)
                    
            elif query.data == "quiz_finish":
                # Завершение квиза
                await self._finish_quiz(update, context, current_answers)
                
            elif query.data == "quiz_prev":
                # Переход к предыдущему вопросу
                prev_step = current_step - 1
                if prev_step >= 0:
                    context.user_data['quiz_step'] = prev_step
                    await self._send_question(update, context, prev_step)
                
            elif query.data.startswith("quiz_answer_"):
                # Обработка ответа на вопрос
                parts = query.data.split("_", 3)
                if len(parts) >= 4:
                    question_id = parts[2]
                    answer_value = parts[3]
                    
                    question = self.quiz_questions[current_step]
                    
                    # Проверяем что question_id соответствует текущему вопросу
                    if question['id'] == question_id:
                        if question['type'] == 'single_choice':
                            current_answers[question_id] = answer_value
                        elif question['type'] == 'multiple_choice':
                            if question_id not in current_answers:
                                current_answers[question_id] = []
                            
                            if answer_value in current_answers[question_id]:
                                current_answers[question_id].remove(answer_value)
                            else:
                                current_answers[question_id].append(answer_value)
                        
                        context.user_data['quiz_answers'] = current_answers
                        
                        # Обновляем отображение текущего вопроса
                        await self._send_question(update, context, current_step)
                    else:
                        logger.warning(f"Question ID mismatch: expected {question['id']}, got {question_id}")
                        await query.answer("❌ Ошибка синхронизации. Попробуйте еще раз.")
                    
        except Exception as e:
            logger.error(f"Ошибка в обработчике квиза: {e}")
            await query.answer("❌ Произошла ошибка. Попробуйте еще раз.")

    async def _send_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, step: int):
        """Отправляет вопрос пользователю"""
        if step >= len(self.quiz_questions):
            return
            
        question = self.quiz_questions[step]
        current_answers = context.user_data.get('quiz_answers', {})
        
        # Формируем клавиатуру
        keyboard = []
        
        for option in question['options']:
            # Проверяем, выбран ли этот вариант
            is_selected = False
            if question['type'] == 'single_choice':
                is_selected = current_answers.get(question['id']) == option['value']
            elif question['type'] == 'multiple_choice':
                is_selected = option['value'] in current_answers.get(question['id'], [])
            
            # Добавляем эмодзи для выбранных вариантов
            text = f"✅ {option['text']}" if is_selected else option['text']
            
            callback_data = f"quiz_answer_{question['id']}_{option['value']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
        
        # Добавляем кнопки управления
        control_buttons = []
        
        # Кнопка "Далее" (только если есть ответ на обязательный вопрос)
        has_answer = question['id'] in current_answers and bool(current_answers[question['id']])
        if has_answer:
            if step < len(self.quiz_questions) - 1:
                control_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data="quiz_next"))
            else:
                control_buttons.append(InlineKeyboardButton("🏁 Завершить квиз", callback_data="quiz_finish"))
        
        # Кнопка "Назад"
        if step > 0:
            control_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data="quiz_prev"))
        
        control_buttons.append(InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu"))
        
        if control_buttons:
            keyboard.append(control_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Определяем блок вопроса
        block_labels = {
            'demographic': '1️⃣ Демографический блок',
            'psychological': '2️⃣ Психологический блок', 
            'lifestyle': '3️⃣ Lifestyle блок',
            'sensory': '4️⃣ Сенсорный блок (Edwards Wheel)',
            'emotional': '5️⃣ Эмоционально-ассоциативный блок'
        }
        
        # Формируем текст вопроса
        progress = f"Вопрос {step + 1} из {len(self.quiz_questions)}"
        block_info = block_labels.get(question['block'], '')
        
        if question['type'] == 'multiple_choice':
            instruction = "\n💡 *Можно выбрать несколько вариантов*"
        else:
            instruction = "\n💡 *Выберите один вариант*"
        
        question_text = f"🔬 **{progress}**\n{block_info}\n\n{question['question']}{instruction}"
        
        # Отправляем или редактируем сообщение
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    text=question_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Ошибка при редактировании сообщения квиза: {e}")
                try:
                    await update.effective_chat.send_message(
                        text=question_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                except Exception as e2:
                    logger.error(f"Ошибка при отправке нового сообщения квиза: {e2}")
        else:
            await update.message.reply_text(
                text=question_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def _finish_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE, quiz_answers: Dict):
        """Завершает квиз и показывает результаты"""
        user_id = update.effective_user.id
        
        # Анализируем ответы с помощью Edwards Fragrance Wheel
        analysis_result = self._analyze_quiz_answers_edwards(quiz_answers)
        
        # Сохраняем профиль пользователя
        self.db.save_user_quiz_profile(user_id, analysis_result['profile'])
        
        # Получаем все подходящие парфюмы из БД
        suitable_perfumes = self.db.get_all_perfumes_from_database()
        
        # Формируем запрос к AI с анализом Edwards Wheel
        ai_prompt = self._create_ai_prompt_with_edwards(analysis_result, suitable_perfumes)
        
        # Отправляем запрос к AI
        try:
            ai_response = await self.ai_processor.process_message(ai_prompt, user_id)
            
            # Формируем итоговое сообщение
            result_text = f"""
🎯 **Квиз завершен!**

🔬 **Анализ по Edwards Fragrance Wheel:**
🌸 Цветочные: {analysis_result['edwards_analysis']['floral']}%
🌟 Восточные: {analysis_result['edwards_analysis']['oriental']}%
🌳 Древесные: {analysis_result['edwards_analysis']['woody']}%
💧 Свежие: {analysis_result['edwards_analysis']['fresh']}%

**Доминирующее семейство:** {analysis_result['dominant_family']}

🤖 **Персональные рекомендации:**
{ai_response}
            """
            
        except Exception as e:
            logger.error(f"Ошибка при обработке AI запроса: {e}")
            result_text = f"""
🎯 **Квиз завершен!**

🔬 **Анализ по Edwards Fragrance Wheel:**
🌸 Цветочные: {analysis_result['edwards_analysis']['floral']}%
🌟 Восточные: {analysis_result['edwards_analysis']['oriental']}%
🌳 Древесные: {analysis_result['edwards_analysis']['woody']}%
💧 Свежие: {analysis_result['edwards_analysis']['fresh']}%

**Доминирующее семейство:** {analysis_result['dominant_family']}

⚠️ AI-анализ временно недоступен, но ваш профиль сохранен!
            """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_quiz")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем результат
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    text=result_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception:
                await update.effective_chat.send_message(
                    text=result_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                text=result_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        logger.info(f"✅ Пользователь {user_id} завершил квиз. Доминирующее семейство: {analysis_result['dominant_family']}")

    def _analyze_quiz_answers_edwards(self, quiz_answers: Dict) -> Dict:
        """Анализирует ответы квиза с помощью Edwards Fragrance Wheel"""
        
        # Собираем все ключевые слова из ответов
        all_keywords = []
        profile = {}
        
        for question in self.quiz_questions:
            question_id = question['id']
            if question_id in quiz_answers:
                answer_values = quiz_answers[question_id]
                if not isinstance(answer_values, list):
                    answer_values = [answer_values]
                
                profile[question_id] = answer_values
                
                # Собираем ключевые слова
                for answer_value in answer_values:
                    for option in question['options']:
                        if option['value'] == answer_value:
                            all_keywords.extend(option.get('keywords', []))
        
        # Анализ по Edwards Fragrance Wheel
        edwards_keywords = {
            'floral': ['floral', 'rose', 'jasmine', 'peony', 'lily', 'romantic', 'feminine', 'gentle', 'нежный', 'романтичный', 'чувственный', 'женственный'],
            'oriental': ['oriental', 'amber', 'vanilla', 'musk', 'warm', 'spicy', 'exotic', 'intense', 'теплый', 'пряный', 'восточный', 'насыщенный', 'согревающий'],
            'woody': ['woody', 'sandalwood', 'cedar', 'forest', 'pine', 'earthy', 'masculine', 'древесный', 'лесной', 'мужской', 'строгий'],
            'fresh': ['fresh', 'citrus', 'green', 'aquatic', 'marine', 'clean', 'light', 'свежий', 'легкий', 'морской', 'чистый', 'прохладный', 'дневной', 'летний', 'весенний']
        }
        
        edwards_scores = {family: 0 for family in edwards_keywords.keys()}
        
        # Подсчитываем соответствия
        for keyword in all_keywords:
            keyword_lower = keyword.lower()
            for family, family_keywords in edwards_keywords.items():
                if keyword_lower in family_keywords:
                    edwards_scores[family] += 1
        
        # Вычисляем проценты
        total_score = sum(edwards_scores.values())
        if total_score > 0:
            edwards_percentages = {
                family: round((score / total_score) * 100)
                for family, score in edwards_scores.items()
            }
        else:
            edwards_percentages = {family: 0 for family in edwards_keywords.keys()}
        
        # Определяем доминирующее семейство
        dominant_family = max(edwards_percentages.keys(), key=lambda k: edwards_percentages[k])
        if edwards_percentages[dominant_family] == 0:
            dominant_family = 'fresh'  # По умолчанию
        
        return {
            'profile': profile,
            'all_keywords': all_keywords,
            'edwards_analysis': edwards_percentages,
            'dominant_family': dominant_family,
            'total_keywords': len(all_keywords),
            'unique_keywords': len(set(all_keywords))
        }

    def _create_ai_prompt_with_edwards(self, analysis_result: Dict, perfumes_data: List) -> str:
        """Создает промпт для AI с анализом Edwards Wheel"""
        
        family_names = {
            'floral': 'Цветочные',
            'oriental': 'Восточные/Амбровые',
            'woody': 'Древесные',
            'fresh': 'Свежие'
        }
        
        prompt = f"""
Ты эксперт-парфюмер. Проанализируй результаты научного квиза на основе Edwards Fragrance Wheel и подбери идеальные парфюмы.

АНАЛИЗ ПОЛЬЗОВАТЕЛЯ:
🔬 Edwards Fragrance Wheel анализ:
- Цветочные: {analysis_result['edwards_analysis']['floral']}%
- Восточные/Амбровые: {analysis_result['edwards_analysis']['oriental']}%  
- Древесные: {analysis_result['edwards_analysis']['woody']}%
- Свежие: {analysis_result['edwards_analysis']['fresh']}%

Доминирующее семейство: {family_names.get(analysis_result['dominant_family'], analysis_result['dominant_family'])}

Ключевые характеристики: {', '.join(analysis_result['all_keywords'][:15])}

ЗАДАЧА:
1. Подбери 3-5 конкретных парфюмов из предоставленного каталога
2. Учитывай доминирующее семейство Edwards Wheel
3. Объясни почему именно эти ароматы подходят
4. Укажи для каких случаев каждый аромат подходит
5. Дай краткое описание каждого аромата

КАТАЛОГ ПАРФЮМОВ:
{json.dumps(perfumes_data[:100], ensure_ascii=False, indent=2)}

Отвечай структурированно и профессионально, как консультант в парфюмерном магазине.
        """
        
        return prompt