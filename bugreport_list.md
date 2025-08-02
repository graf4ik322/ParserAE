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

## 📊 Статистика багов

| Статус | Количество |
|--------|------------|
| 🔍 Открыт | 3 |
| 🔧 В работе | 0 |
| ✅ Исправлен | 0 |
| ❌ Закрыт | 0 |

**Всего багов:** 3

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