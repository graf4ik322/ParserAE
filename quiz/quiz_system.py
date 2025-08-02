#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, List, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

logger = logging.getLogger(__name__)

class QuizSystem:
    """Система квизов для определения предпочтений пользователей"""
    
    def __init__(self, db_manager, ai_processor=None):
        self.db = db_manager
        self.ai_processor = ai_processor
        self.quiz_questions = self._initialize_quiz_questions()
        logger.info("📝 QuizSystem инициализирована")
    
    def _initialize_quiz_questions(self) -> List[Dict[str, Any]]:
        """Инициализирует вопросы квиза"""
        return [
            {
                "id": "gender",
                "question": "👤 **Укажите ваш пол:**",
                "type": "single_choice",
                "options": [
                    {"text": "👨 Мужской", "value": "Мужской"},
                    {"text": "👩 Женский", "value": "Женский"},
                    {"text": "🌈 Унисекс", "value": "Унисекс"}
                ]
            },
            {
                "id": "age_group",
                "question": "🎂 **Ваша возрастная группа:**",
                "type": "single_choice",
                "options": [
                    {"text": "🌱 18-25 лет", "value": "18-25"},
                    {"text": "🌿 26-35 лет", "value": "26-35"},
                    {"text": "🌳 36-45 лет", "value": "36-45"},
                    {"text": "🍂 46+ лет", "value": "46+"}
                ]
            },
            {
                "id": "budget",
                "question": "💰 **Какой у вас бюджет на парфюм?**",
                "type": "single_choice",
                "options": [
                    {"text": "💸 До 2000 рублей", "value": "до 2000"},
                    {"text": "💵 2000-5000 рублей", "value": "2000-5000"},
                    {"text": "💴 5000-10000 рублей", "value": "5000-10000"},
                    {"text": "💎 Свыше 10000 рублей", "value": "свыше 10000"}
                ]
            },
            {
                "id": "occasion",
                "question": "🎭 **Для каких случаев вы планируете использовать парфюм?**",
                "type": "multiple_choice",
                "options": [
                    {"text": "🏢 Работа/офис", "value": "работа"},
                    {"text": "💕 Романтические встречи", "value": "свидания"},
                    {"text": "🎉 Особые мероприятия", "value": "события"},
                    {"text": "🌅 Повседневная жизнь", "value": "повседневно"},
                    {"text": "🌙 Вечерние выходы", "value": "вечер"}
                ]
            },
            {
                "id": "intensity_preference",
                "question": "💨 **Какую интенсивность аромата вы предпочитаете?**",
                "type": "single_choice",
                "options": [
                    {"text": "🌸 Легкий и ненавязчивый", "value": "легкий"},
                    {"text": "🌺 Умеренный", "value": "умеренный"},
                    {"text": "🌹 Насыщенный и стойкий", "value": "насыщенный"}
                ]
            },
            {
                "id": "season_preference",
                "question": "🌍 **В какое время года вы чаще всего используете парфюм?**",
                "type": "multiple_choice",
                "options": [
                    {"text": "🌸 Весна", "value": "весна"},
                    {"text": "☀️ Лето", "value": "лето"},
                    {"text": "🍂 Осень", "value": "осень"},
                    {"text": "❄️ Зима", "value": "зима"}
                ]
            },
            {
                "id": "fragrance_families",
                "question": "🌿 **Какие группы ароматов вам нравятся?**",
                "type": "multiple_choice",
                "options": [
                    {"text": "🌸 Цветочные", "value": "цветочные"},
                    {"text": "🍊 Цитрусовые", "value": "цитрусовые"},
                    {"text": "🌲 Древесные", "value": "древесные"},
                    {"text": "🌿 Свежие", "value": "свежие"},
                    {"text": "🍯 Восточные", "value": "восточные"},
                    {"text": "🌰 Гурманские", "value": "гурманские"}
                ]
            },
            {
                "id": "experience_level",
                "question": "🎓 **Ваш опыт с парфюмерией:**",
                "type": "single_choice",
                "options": [
                    {"text": "🌱 Новичок", "value": "новичок"},
                    {"text": "🌿 Немного разбираюсь", "value": "средний"},
                    {"text": "🌳 Хорошо разбираюсь", "value": "продвинутый"},
                    {"text": "🎯 Эксперт", "value": "эксперт"}
                ]
            }
        ]
    
    async def start_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает квиз"""
        user_id = update.effective_user.id
        
        # Сбрасываем предыдущие данные квиза
        self.db.update_session_state(user_id, "QUIZ_IN_PROGRESS", {"quiz_answers": {}, "quiz_step": 0})
        
        # Показываем первый вопрос
        await self._show_quiz_question(update, context, 0)
        
        logger.info(f"📝 Пользователь {user_id} начал квиз")
    
    async def handle_quiz_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатия кнопок в квизе"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Получаем текущую сессию
        session = self.db.get_user_session(user_id)
        if not session or session.get('current_state') != 'QUIZ_IN_PROGRESS':
            await query.edit_message_text("❌ Сессия квиза истекла. Начните заново.")
            return
        
        quiz_answers = session.get('quiz_answers', {})
        quiz_step = session.get('quiz_step', 0)
        
        # Парсим callback_data
        callback_parts = query.data.split('_')
        action = callback_parts[1]  # quiz_answer, quiz_next, quiz_finish
        
        if action == "answer":
            # Сохраняем ответ
            question_id = callback_parts[2]
            answer_value = "_".join(callback_parts[3:])
            
            current_question = self.quiz_questions[quiz_step]
            
            if current_question['type'] == 'single_choice':
                quiz_answers[question_id] = answer_value
            elif current_question['type'] == 'multiple_choice':
                if question_id not in quiz_answers:
                    quiz_answers[question_id] = []
                
                if answer_value in quiz_answers[question_id]:
                    quiz_answers[question_id].remove(answer_value)
                else:
                    quiz_answers[question_id].append(answer_value)
            
            # Обновляем сессию
            self.db.update_quiz_session(user_id, quiz_answers, quiz_step)
            
            # Обновляем отображение вопроса
            await self._show_quiz_question(update, context, quiz_step, quiz_answers)
            
        elif action == "next":
            # Переходим к следующему вопросу
            quiz_step += 1
            
            if quiz_step < len(self.quiz_questions):
                self.db.update_quiz_session(user_id, quiz_answers, quiz_step)
                await self._show_quiz_question(update, context, quiz_step, quiz_answers)
            else:
                # Квиз завершен
                await self._finish_quiz(update, context, quiz_answers)
                
        elif action == "finish":
            # Завершаем квиз
            await self._finish_quiz(update, context, quiz_answers)
    
    async def handle_quiz_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
        """Обрабатывает текстовые ответы в квизе (если потребуется)"""
        # В текущей реализации все ответы через кнопки, но можно расширить
        await update.message.reply_text(
            "📝 Пожалуйста, используйте кнопки для ответов на вопросы квиза.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
        )
    
    async def _show_quiz_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 step: int, current_answers: Dict = None):
        """Показывает вопрос квиза"""
        if step >= len(self.quiz_questions):
            return
        
        question = self.quiz_questions[step]
        current_answers = current_answers or {}
        
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
        has_answer = question['id'] in current_answers and current_answers[question['id']]
        if has_answer:
            if step < len(self.quiz_questions) - 1:
                control_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data="quiz_next"))
            else:
                control_buttons.append(InlineKeyboardButton("🏁 Завершить квиз", callback_data="quiz_finish"))
        
        # Кнопка "Назад"
        control_buttons.append(InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu"))
        
        if control_buttons:
            keyboard.append(control_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Формируем текст вопроса
        progress = f"Вопрос {step + 1} из {len(self.quiz_questions)}"
        
        if question['type'] == 'multiple_choice':
            instruction = "\n💡 *Можно выбрать несколько вариантов*"
        else:
            instruction = "\n💡 *Выберите один вариант*"
        
        question_text = f"📋 **{progress}**\n\n{question['question']}{instruction}"
        
        # Отправляем или редактируем сообщение
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=question_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=question_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def _finish_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE, quiz_answers: Dict):
        """Завершает квиз и показывает результаты"""
        user_id = update.effective_user.id
        
        # Анализируем ответы и создаем профиль
        user_profile = self._analyze_quiz_answers(quiz_answers)
        
        # Сохраняем профиль пользователя
        self.db.save_user_quiz_profile(user_id, user_profile)
        
        # Получаем все подходящие парфюмы из БД (без лимитов!)
        suitable_perfumes = self.db.get_all_perfumes_from_database()
        
        # Здесь можно добавить фильтрацию по профилю пользователя
        # Но согласно техническому заданию, используем ВСЕ данные
        
        try:
            # Используем AI для создания рекомендаций
            from ai.processor import AIProcessor
            from config import Config
            
            config = Config()
            ai_processor = AIProcessor(config.openrouter_api_key)
            
            # Создаем промпт для рекомендаций
            prompt = ai_processor.create_quiz_results_prompt(user_profile, suitable_perfumes)
            
            # Отправляем уведомление о обработке
            processing_msg = await update.callback_query.edit_message_text(
                "🤔 Анализирую ваши ответы и подбираю персональные рекомендации..."
            )
            
            # Получаем рекомендации от ИИ
            ai_response = await ai_processor.call_openrouter_api(prompt, max_tokens=4000)
            
            # Обрабатываем ответ и добавляем ссылки
            processed_response = ai_processor.process_ai_response_with_links(ai_response, self.db)
            
            # Формируем финальный ответ
            final_response = f"""🎉 **Квиз завершен!**

{processed_response}

📝 Ваш профиль сохранен. В будущем я смогу давать еще более точные рекомендации!"""
            
            # Удаляем сообщение о обработке и отправляем результат
            await processing_msg.delete()
            
            await update.effective_chat.send_message(
                text=final_response,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
            
            # Сохраняем статистику
            self.db.save_usage_stat(user_id, "quiz_completed", None, str(quiz_answers), len(final_response))
            
            # Закрываем AI processor
            await ai_processor.close()
            
        except Exception as e:
            logger.error(f"Ошибка при завершении квиза: {e}")
            await update.callback_query.edit_message_text(
                "❌ Произошла ошибка при обработке результатов квиза. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
        
        # Возвращаем пользователя в главное меню
        self.db.update_session_state(user_id, "MAIN_MENU")
        
        logger.info(f"✅ Пользователь {user_id} завершил квиз")
    
    def _analyze_quiz_answers(self, quiz_answers: Dict) -> Dict[str, Any]:
        """Анализирует ответы квиза и создает профиль пользователя"""
        profile = {}
        
        # Прямое сопоставление ответов
        direct_mapping = {
            'gender': 'gender',
            'age_group': 'age_group',
            'budget': 'budget',
            'intensity_preference': 'intensity_preference',
            'experience_level': 'experience_level'
        }
        
        for quiz_key, profile_key in direct_mapping.items():
            if quiz_key in quiz_answers:
                profile[profile_key] = quiz_answers[quiz_key]
        
        # Массивы
        array_mapping = {
            'occasion': 'occasion',
            'season_preference': 'season_preference',
            'fragrance_families': 'preferred_fragrance_groups'
        }
        
        for quiz_key, profile_key in array_mapping.items():
            if quiz_key in quiz_answers:
                profile[profile_key] = quiz_answers[quiz_key]
        
        # Добавляем метаданные
        profile['quiz_completed_at'] = datetime.now().isoformat()
        profile['quiz_version'] = '1.0'
        
        return profile
    
    async def _finish_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE, quiz_answers: Dict):
        """Завершает квиз и генерирует персональные рекомендации"""
        user_id = update.effective_user.id
        
        try:
            # Анализируем ответы и создаем профиль пользователя
            user_profile = self._analyze_quiz_results(quiz_answers)
            
            # Сохраняем профиль пользователя
            self.db.save_user_profile(user_id, user_profile)
            
            # Получаем все парфюмы
            all_perfumes = self.db.get_all_perfumes_for_ai()
            
            if not all_perfumes:
                await update.callback_query.edit_message_text(
                    "❌ Извините, каталог парфюмов временно недоступен."
                )
                return
            
            # Фильтруем подходящие парфюмы на основе профиля
            suitable_perfumes = self._filter_perfumes_by_profile(user_profile, all_perfumes)
            
            # Используем переданный AIProcessor
            if not self.ai_processor:
                await update.callback_query.edit_message_text(
                    "❌ Извините, сервис рекомендаций временно недоступен."
                )
                return
            ai_processor = self.ai_processor
            
            # Создаем промпт для ИИ
            prompt = ai_processor.create_quiz_results_prompt(user_profile, suitable_perfumes)
            
            # Отправляем сообщение о генерации рекомендаций
            await update.callback_query.edit_message_text("🧠 Анализирую ваши предпочтения и готовлю персональные рекомендации...")
            
            # Получаем ответ от ИИ
            ai_response = await ai_processor.call_openrouter_api(prompt, max_tokens=6000)
            
            if ai_response.startswith("Извините"):
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ {ai_response}"
                )
                return
            
            # Обрабатываем ответ и добавляем ссылки "Приобрести"
            processed_response = ai_processor.process_ai_response_with_links(ai_response, self.db)
            
            # Отправляем результат
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎯 **Ваши персональные рекомендации:**\n\n{processed_response}",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            # Сохраняем статистику
            self.db.save_usage_stat(user_id, 'quiz_completed')
            
            # Завершаем сессию
            self.db.end_user_session(user_id)
            
            logger.info(f"👤 Пользователь {user_id} завершил квиз и получил персональные рекомендации")
            
        except Exception as e:
            logger.error(f"Ошибка при завершении квиза для пользователя {user_id}: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Произошла ошибка при генерации рекомендаций. Попробуйте позже."
            )
    
    def _filter_perfumes_by_profile(self, user_profile: Dict, all_perfumes: List[Dict]) -> List[Dict]:
        """Фильтрует парфюмы на основе профиля пользователя"""
        suitable = []
        
        # Базовые предпочтения
        preferred_gender = user_profile.get('gender', '')
        preferred_groups = user_profile.get('preferred_fragrance_groups', [])
        budget_preference = user_profile.get('budget_preference', '')
        
        for perfume in all_perfumes:
            # Проверяем соответствие полу
            if preferred_gender and preferred_gender != 'unisex':
                perfume_gender = perfume.get('gender', '').lower()
                if perfume_gender and perfume_gender != 'унисекс' and preferred_gender.lower() not in perfume_gender:
                    continue
            
            # Проверяем ароматические группы
            if preferred_groups:
                perfume_group = perfume.get('fragrance_group', '').lower()
                group_match = any(group.lower() in perfume_group for group in preferred_groups)
                if not group_match:
                    continue
            
            # Проверяем бюджет (если указан)
            if budget_preference and budget_preference != 'no_limit':
                price = perfume.get('price', 0)
                if budget_preference == 'budget' and price > 100:
                    continue
                elif budget_preference == 'medium' and (price < 50 or price > 200):
                    continue
                elif budget_preference == 'premium' and price < 150:
                    continue
            
            suitable.append(perfume)
        
        # Если подходящих мало, добавляем популярные варианты
        if len(suitable) < 10:
            suitable.extend([p for p in all_perfumes if p not in suitable][:20])
        
        return suitable[:50]  # Ограничиваем количество для оптимизации