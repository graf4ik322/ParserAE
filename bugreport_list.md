# 🐛 Bug Report List

## Обзор
Этот файл содержит список всех найденных багов в проекте Perfume Bot с их описанием, статусом и решениями.

---

## 🐛 BOT-001: Отсутствует автоматический запуск планировщика парсера при старте бота

### **Статус:** 🔍 Открыт
### **Severity:** Medium
### **Priority:** Medium
### **Дата создания:** 2025-08-02

### **Description:**
При старте бота не запускается автоматический планировщик парсера (`AutoParser.start_scheduler()`), что приводит к отсутствию автоматического обновления каталога парфюмов.

### **Current Behavior:**
- Бот запускается без автоматического планировщика парсера
- Парсинг выполняется только по команде администратора
- Каталог не обновляется автоматически

### **Expected Behavior:**
- При старте бота должен автоматически запускаться планировщик парсера
- Парсинг должен выполняться каждые 6 часов
- Ежедневный полный парсинг в 06:00
- Еженедельное полное обновление по воскресеньям в 03:00

### **Root Cause:**
В методе `run()` класса `PerfumeBot` отсутствует вызов `await self.auto_parser.start_scheduler()`.

### **Affected Files:**
- `main.py` - метод `run()` класса `PerfumeBot`

### **Steps to Reproduce:**
1. Запустить бота
2. Проверить логи - отсутствует сообщение "⏰ Планировщик автоматического парсинга запущен"
3. Проверить статус парсера через админ-панель

### **Proposed Fix:**
Добавить в метод `run()` класса `PerfumeBot`:

```python
def run(self):
    """Запускает бота"""
    try:
        # Проверяем, не запущен ли уже другой экземпляр
        if not self._acquire_lock():
            logger.error("❌ Бот уже запущен! Завершаем работу.")
            sys.exit(1)
        
        # Настраиваем обработчики сигналов
        self._setup_signal_handlers()
        
        # Запускаем автоматический планировщик парсера
        asyncio.create_task(self.auto_parser.start_scheduler())
        
        logger.info("🚀 Perfume Bot запущен и готов к работе!")
        
        # Запускаем polling с логированием
        logger.info("📡 Запускаем polling для получения обновлений...")
        self.application.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise
    finally:
        # Освобождаем блокировку при любом завершении
        self._release_lock()
```

### **Testing:**
1. После исправления при запуске бота должно появиться сообщение "⏰ Планировщик автоматического парсинга запущен"
2. В админ-панели статус парсера должен показывать "🔄 Активен"
3. Парсинг должен выполняться автоматически по расписанию

### **Additional Notes:**
Два HTTP запроса при старте (`getMe` и `deleteWebhook`) - это нормальное поведение python-telegram-bot и не является багом.

---

## 🐛 BOT-002: Отсутствует валидация входных данных в обработчиках сообщений

### **Статус:** 🔍 Открыт
### **Severity:** Medium
### **Priority:** Medium
### **Дата создания:** 2025-08-02

### **Description:**
В обработчиках сообщений отсутствует валидация входных данных, что может привести к ошибкам при обработке пустых или некорректных сообщений.

### **Current Behavior:**
- Обработчики принимают любые сообщения без проверки
- Пустые сообщения могут вызвать ошибки
- Отсутствует проверка длины сообщений
- Нет фильтрации нежелательного контента

### **Expected Behavior:**
- Валидация длины сообщений (минимум 2 символа, максимум 1000)
- Проверка на пустые сообщения
- Фильтрация нежелательного контента
- Информативные сообщения об ошибках валидации

### **Root Cause:**
В методах `handle_perfume_question()` и `handle_fragrance_info()` отсутствует валидация параметра `message_text`.

### **Affected Files:**
- `main.py` - методы `handle_perfume_question()` и `handle_fragrance_info()`

### **Steps to Reproduce:**
1. Отправить пустое сообщение в режиме "Задать вопрос о парфюмах"
2. Отправить сообщение из одного символа
3. Отправить очень длинное сообщение (>1000 символов)

### **Proposed Fix:**
Добавить валидацию в начало методов:

```python
async def handle_perfume_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Обрабатывает вопросы о парфюмах"""
    user_id = update.effective_user.id
    
    # Валидация входных данных
    if not message_text or not message_text.strip():
        await update.message.reply_text(
            "❌ Пожалуйста, введите ваш вопрос о парфюмах.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
        )
        return
    
    message_text = message_text.strip()
    
    if len(message_text) < 2:
        await update.message.reply_text(
            "❌ Вопрос должен содержать минимум 2 символа.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
        )
        return
    
    if len(message_text) > 1000:
        await update.message.reply_text(
            "❌ Вопрос слишком длинный. Пожалуйста, сократите его до 1000 символов.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
        )
        return
    
    # Остальной код...
```

### **Testing:**
1. Отправить пустое сообщение - должно появиться предупреждение
2. Отправить короткое сообщение - должно появиться предупреждение
3. Отправить длинное сообщение - должно появиться предупреждение
4. Отправить корректное сообщение - должно обработаться нормально

### **Additional Notes:**
Аналогичную валидацию нужно добавить в `handle_fragrance_info()`.

---

## 🐛 BOT-003: Отсутствует обработка неизвестных callback'ов в button_callback

### **Статус:** 🔍 Открыт
### **Severity:** Low
### **Priority:** Low
### **Дата создания:** 2025-08-02

### **Description:**
В методе `button_callback()` отсутствует обработка неизвестных callback'ов, что может привести к тихим ошибкам и неожиданному поведению.

### **Current Behavior:**
- Неизвестные callback'ы игнорируются без логирования
- Пользователь не получает обратной связи
- Отсутствует логирование неизвестных callback'ов для отладки

### **Expected Behavior:**
- Логирование неизвестных callback'ов для отладки
- Информативное сообщение пользователю о неизвестной команде
- Возврат в главное меню при неизвестном callback'е

### **Root Cause:**
В методе `button_callback()` отсутствует блок `else` для обработки неизвестных callback'ов.

### **Affected Files:**
- `main.py` - метод `button_callback()`

### **Steps to Reproduce:**
1. Отправить неизвестный callback через API
2. Проверить логи - отсутствует информация о неизвестном callback'е
3. Пользователь не получает обратной связи

### **Proposed Fix:**
Добавить обработку неизвестных callback'ов:

```python
async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "perfume_question":
        await self.start_perfume_question(update, context)
    elif query.data == "start_quiz":
        await self.quiz.start_quiz(update, context)
    elif query.data == "fragrance_info":
        await self.start_fragrance_info(update, context)
    elif query.data == "help":
        await self.help_command(update, context)
    elif query.data == "back_to_menu":
        await self.show_main_menu(update, context)
    elif query.data.startswith("quiz_"):
        await self.quiz.handle_quiz_callback(update, context)
    # Админ-панель callbacks
    elif query.data == "admin_panel":
        await self._handle_admin_panel_callback(update, context)
    elif query.data == "admin_db":
        await self._handle_admin_db_callback(update, context)
    elif query.data == "admin_api":
        await self._handle_admin_api_callback(update, context)
    elif query.data == "admin_parser":
        await self._handle_admin_parser_callback(update, context)
    elif query.data == "admin_force_parse":
        await self._handle_admin_force_parse_callback(update, context)
    elif query.data == "admin_full_stats":
        await self._handle_admin_full_stats_callback(update, context)
    else:
        # Обработка неизвестных callback'ов
        logger.warning(f"Неизвестный callback: {query.data} от пользователя {user_id}")
        try:
            await query.edit_message_text(
                "❌ Неизвестная команда. Возвращаюсь в главное меню.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке неизвестного callback: {e}")
            # Fallback - отправляем новое сообщение
            await update.effective_chat.send_message(
                "❌ Произошла ошибка. Возвращаюсь в главное меню.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
```

### **Testing:**
1. Отправить неизвестный callback - должно появиться предупреждение в логах
2. Пользователь должен получить сообщение об ошибке
3. Бот должен вернуться в главное меню

### **Additional Notes:**
Это улучшит отладку и пользовательский опыт.

---

## 🐛 BOT-004: Тайм-ауты в функциях квиза и вопросов о парфюмах

### **Статус:** 🔍 Открыт
### **Severity:** High
### **Priority:** High
### **Дата создания:** 2025-08-02

### **Description:**
Функции квиза и вопросов о парфюмах работают с тайм-аутами, что приводит к отсутствию ответов от ИИ.

### **Current Behavior:**
- Функции квиза и вопросов о парфюмах отправляют запрос к ИИ
- После отправки запроса ничего не происходит (тайм-аут)
- Пользователь не получает ответ
- Логи показывают отправку запроса, но нет ответа

### **Expected Behavior:**
- Функции должны работать корректно и возвращать ответы
- Не должно быть тайм-аутов
- Пользователь должен получать ответы от ИИ

### **Root Cause:**
Проблема может быть связана с:
- Настройками тайм-аутов в API запросах
- Проблемами с сетью или API сервисом
- Ошибками в обработке ответов ИИ

### **Affected Files:**
- `ai/processor.py` - настройки тайм-аутов и обработка запросов
- `main.py` - обработчики вопросов о парфюмах
- `quiz/quiz_system.py` - обработка результатов квиза

### **Steps to Reproduce:**
1. Запустить квиз и дойти до конца
2. Задать вопрос о парфюмах
3. Наблюдать тайм-аут без ответа

### **Proposed Fix:**
Исследовать и исправить проблемы с тайм-аутами:

1. **Проверить настройки тайм-аутов в `ai/processor.py`:**
   ```python
   # Увеличить тайм-аут для больших запросов
   timeout=aiohttp.ClientTimeout(total=300)  # 5 минут вместо 180
   ```

2. **Добавить retry логику для API запросов**

3. **Улучшить обработку ошибок и логирование**

### **Testing:**
1. Протестировать функции квиза и вопросов о парфюмах
2. Проверить логи на наличие ошибок API
3. Убедиться, что ответы приходят в разумное время

### **Additional Notes:**
Требуется детальное исследование причин тайм-аутов.
{chr(10).join(factory_summary)}

ИНСТРУКЦИИ:
1. Проанализируй запрос клиента и выбери 3-5 наиболее подходящих ароматов
2. Для каждого аромата укажи:
   - Почему он подходит для данного запроса
   - Наилучшую Фабрику-производителя и её особенности
   - Практические советы по использованию
   - ОБЯЗАТЕЛЬНО добавь ссылку на карточку товара в формате: 🛒 [Заказать на aroma-euro.ru](URL)
3. Дай рекомендации по фабрикам
4. Добавь профессиональные советы

ВАЖНО: 
- В названии аромата используй точное название из списка!
- Обязательно указывай артикул в формате [Артикул: XXX]!

ФОРМАТ ОТВЕТА:
🎯 **Рекомендуемые ароматы:**

1. **[Название аромата]** ([Фабрика]) [Артикул: XXX]
   - Почему подходит: [объяснение]
   - Особенности фабрики: [анализ]
   - Советы по использованию: [практика]
   - 🛒 [Ссылка на товар]

🏭 **Анализ фабрик:**
[Сравнение и рекомендации]

💡 **Профессиональные советы:**
[Дополнительные рекомендации]

Ответ должен быть экспертным и полезным для клиента!"""
    
    return prompt
```

### **Testing:**
1. Протестировать функции квиза и вопросов о парфюмах
2. Проверить логи на наличие ошибок API
3. Убедиться, что ответы приходят в разумное время

### **Additional Notes:**
Требуется детальное исследование причин тайм-аутов.

---

## 🐛 BOT-005: Двойное форматирование в handle_fragrance_info приводит к ошибкам

### **Статус:** ✅ Исправлен
### **Severity:** Medium
### **Priority:** Medium
### **Дата создания:** 2025-08-02

### **Description:**
В методе `handle_fragrance_info()` происходит двойное форматирование ответа ИИ, что может приводить к ошибкам и некорректному отображению.

### **Current Behavior:**
- Ответ ИИ форматируется дважды: сначала в `process_message()`, потом в `_format_text_for_telegram()`
- Это может приводить к избыточному экранированию символов
- Возможны ошибки форматирования

### **Expected Behavior:**
- Ответ должен форматироваться только один раз
- Форматирование должно быть корректным
- Не должно быть избыточного экранирования

### **Root Cause:**
В `handle_fragrance_info()` ответ ИИ форматируется дважды:
1. В `process_message()` через `_format_text_for_telegram()` (строка 407 в `ai/processor.py`)
2. В `handle_fragrance_info()` снова через `_format_text_for_telegram()` (строка 804 в `main.py`)

**Важное наблюдение:** В отличие от `handle_perfume_question()`, который использует `processed_response` напрямую без дополнительного форматирования, `handle_fragrance_info()` применяет дополнительное форматирование, что создает несоответствие в архитектуре.

### **Affected Files:**
- `main.py` - метод `handle_fragrance_info()`

### **Steps to Reproduce:**
1. Задать вопрос об аромате
2. Наблюдать возможные ошибки форматирования
3. Проверить логи на наличие ошибок экранирования

### **Proposed Fix:**
Убрать двойное форматирование в `handle_fragrance_info()`:

```python
async def handle_fragrance_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Обрабатывает запросы информации об аромате"""
    user_id = update.effective_user.id
    
    # Отправляем уведомление о поиске
    searching_msg = await update.message.reply_text("🔍 Ищу информацию об аромате...")
    
    try:
        # Используем улучшенный промпт для профессиональной информации об ароматах
        from ai.prompts import PromptTemplates
        prompt = PromptTemplates.create_fragrance_info_prompt(message_text)

        # Получаем ответ от ИИ
        ai_response_raw = await self.ai.process_message(prompt, user_id)
        
        # Проверяем, не вернулся ли ответ о кулдауне
        if "Пожалуйста, подождите" in ai_response_raw:
            await searching_msg.delete()
            await update.message.reply_text(ai_response_raw)
            return
        
        # Обрабатываем ответ и добавляем ссылки по артикулам
        ai_response = self.ai.process_ai_response_with_links(ai_response_raw, self.db)
        
        # Удаляем сообщение о поиске
        await searching_msg.delete()
        
        # Безопасно отправляем информацию с защитой от ошибок форматирования
        try:
            # НЕ форматируем повторно, так как это уже сделано в process_message()
            await update.message.reply_text(
                ai_response,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
        except Exception as format_error:
            logger.warning(f"Ошибка форматирования ответа об аромате: {format_error}")
            # Fallback к простому тексту без форматирования
            plain_response = re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', ai_response)[:4000]
            await update.message.reply_text(
                plain_response,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
            )
        
        # Сохраняем статистику
        self.db.save_usage_stat(user_id, "fragrance_info", None, message_text, len(ai_response))
        
        # Возвращаем в главное меню
        self.db.update_session_state(user_id, "MAIN_MENU")
        
    except Exception as e:
        logger.error(f"Ошибка при поиске информации: {e}")
        await searching_msg.delete()
        await update.message.reply_text(
            "❌ Произошла ошибка при поиске информации. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]])
        )
```

### **Testing:**
1. Задать вопрос об аромате - должен работать без ошибок форматирования
2. Проверить логи - не должно быть ошибок экранирования
3. Ответ должен отображаться корректно

### **Additional Notes:**
Это исправление устранит двойное форматирование и потенциальные ошибки.

---

## 🐛 BOT-006: Несоответствие в обработке форматирования между handle_perfume_question и handle_fragrance_info

### **Статус:** ✅ Исправлен
### **Severity:** Medium
### **Priority:** Medium
### **Дата создания:** 2025-08-02

### **Description:**
В коде существует несоответствие в обработке форматирования между двумя похожими методами, что может приводить к непредсказуемому поведению.

### **Current Behavior:**
- `handle_perfume_question` использует `processed_response` напрямую (без дополнительного форматирования)
- `handle_fragrance_info` применяет дополнительное форматирование через `self.ai._format_text_for_telegram(ai_response)`

### **Expected Behavior:**
- Оба метода должны использовать одинаковый подход к форматированию
- Форматирование должно происходить только один раз в цепочке обработки

### **Root Cause:**
- Несогласованность в архитектуре обработки ответов ИИ
- Отсутствие единого стандарта форматирования

### **Affected Files:**
- `main.py` (строки 747 и 804)

### **Steps to Reproduce:**
1. Запустить бота
2. Протестировать обе функции: "Вопрос о парфюме" и "Информация об аромате"
3. Сравнить поведение форматирования

### **Proposed Fix:**
Унифицировать подход к форматированию в обоих методах, убрав дополнительное форматирование в `handle_fragrance_info`.

### **Testing:**
1. Применить исправление
2. Протестировать обе функции
3. Убедиться в одинаковом поведении форматирования
4. Проверить корректность отображения текста и ссылок

### **Additional Notes:**
Это исправление обеспечит консистентность в обработке ответов ИИ.

---

## 🐛 BOT-007: Сложное форматирование на стороне бота вместо готового формата от ИИ

### **Статус:** ✅ Исправлен
### **Severity:** Medium
### **Priority:** Medium
### **Дата создания:** 2025-08-02

### **Description:**
Вместо сложного форматирования на стороне бота, лучше указать ИИ возвращать данные уже в готовом для Telegram формате.

### **Current Behavior:**
- ИИ возвращает простой текст
- Бот применяет сложное экранирование и форматирование
- Возможны ошибки при экранировании символов
- Двойное форматирование в некоторых случаях

### **Expected Behavior:**
- ИИ возвращает текст уже в готовом для Telegram формате
- Бот применяет минимальную обработку
- Нет ошибок экранирования
- Единообразное форматирование

### **Root Cause:**
- Отсутствие четких инструкций по форматированию в промптах
- Сложная логика экранирования на стороне бота

### **Affected Files:**
- `ai/prompts.py` - добавлены инструкции по форматированию
- `ai/processor.py` - упрощено форматирование

### **Steps to Reproduce:**
1. Запустить любую функцию (квиз, вопросы о парфюмах, информация об аромате)
2. Наблюдать за форматированием ответа

### **Proposed Fix:**
Добавить в промпты четкие инструкции по форматированию для Telegram и упростить обработку на стороне бота.

### **Testing:**
1. Протестировать все функции
2. Проверить корректность отображения Markdown
3. Убедиться в отсутствии ошибок экранирования

### **Additional Notes:**
Это улучшение сделает код более надежным и упростит поддержку.

---

## 🐛 BOT-008: Предложение по улучшению архитектуры форматирования

### **Статус:** 🔍 Открыт
### **Severity:** Low
### **Priority:** Medium
### **Дата создания:** 2025-08-02

### **Description:**
Предложение по улучшению архитектуры: вместо сложного форматирования на стороне бота, указать ИИ возвращать данные уже в готовом для Telegram формате.

### **Current Behavior:**
- ИИ возвращает простой текст
- Бот применяет сложное экранирование и форматирование через `_escape_markdown_safely()`
- Возможны ошибки при экранировании символов
- Двойное форматирование в некоторых случаях
- Сложная логика обработки Markdown
- Ссылки подставляются через `process_ai_response_with_links()` (это хорошо, нужно сохранить)

### **Expected Behavior:**
- ИИ возвращает текст уже в готовом для Telegram формате
- Бот применяет минимальную обработку
- Нет ошибок экранирования
- Единообразное форматирование
- Упрощенная архитектура
- **Сохранение автоматической подстановки гиперссылок** через `process_ai_response_with_links()`

### **Root Cause:**
- Отсутствие четких инструкций по форматированию в промптах
- Сложная логика экранирования на стороне бота
- Неоптимальная архитектура обработки ответов

### **Affected Files:**
- `ai/prompts.py` - нужно добавить инструкции по форматированию
- `ai/processor.py` - упростить `_format_text_for_telegram()`
- `main.py` - убрать двойное форматирование

### **Steps to Reproduce:**
1. Запустить любую функцию (квиз, вопросы о парфюмах, информация об аромате)
2. Наблюдать за сложной обработкой форматирования

### **Proposed Fix:**
1. **В промптах добавить четкие инструкции:**
   ```
   ФОРМАТ ОТВЕТА (готовый для Telegram):
   - Используй *курсив* для заголовков
   - Используй **жирный** для ключевых терминов
   - Не экранируй символы _ и * - они нужны для Markdown
   - Ссылки в формате [Текст](URL)
   ```

2. **Упростить `_format_text_for_telegram()`:**
   ```python
   def _format_text_for_telegram(self, text: str) -> str:
       # Только ограничение длины и уборка лишних строк
       if len(text) > 4000:
           text = text[:3900] + "\n\n📝 *Сообщение сокращено*"
       text = re.sub(r'\n{3,}', '\n\n', text)
       return text
   ```

3. **Убрать сложную логику экранирования:**
   - Удалить `_escape_markdown_safely()`
   - Удалить `_fix_over_escaped_text()`
   - Удалить `_minimal_markdown_escape()`

4. **Обеспечить автоматическую подстановку гиперссылок:**
   - Сохранить функциональность `process_ai_response_with_links()`
   - ИИ должен указывать артикулы в формате `[Артикул: XXX]`
   - Бот автоматически заменяет артикулы на гиперссылки `[Заказать](URL)`
   - Это обеспечивает кликабельность ссылок в Telegram

### **Benefits:**
- ✅ Упрощение кода
- ✅ Устранение ошибок экранирования
- ✅ Единообразное форматирование
- ✅ Лучшая производительность
- ✅ Легче поддерживать

### **Testing:**
1. Протестировать все функции после изменений
2. Проверить корректность отображения Markdown
3. Убедиться в отсутствии ошибок экранирования
4. **Проверить, что гиперссылки работают корректно:**
   - ИИ указывает артикулы в формате `[Артикул: XXX]`
   - Бот автоматически заменяет на `[Заказать](URL)`
   - Ссылки кликабельны в Telegram

### **Additional Notes:**
Это архитектурное улучшение, которое сделает код более надежным и упростит поддержку.

---

## 📊 Статистика багов

| Статус | Количество |
|--------|------------|
| 🔍 Открыт | 5 |
| 🔧 В работе | 0 |
| ✅ Исправлен | 3 |
| ❌ Закрыт | 0 |

**Всего багов:** 8

---

## 🔍 Поиск дополнительных багов

### Области для проверки:
- [ ] Обработка ошибок и исключений
- [ ] Валидация входных данных
- [ ] Производительность и оптимизация
- [ ] Безопасность
- [ ] Логирование и мониторинг
- [ ] Тестирование
- [ ] Документация