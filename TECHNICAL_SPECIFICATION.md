# 📋 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Парфюмерный Консультант-Бот v2.0 (БЕЗ ЛИМИТОВ)

## 🎯 **ОБЩЕЕ ОПИСАНИЕ СИСТЕМЫ**

Система представляет собой Telegram-бота для консультации по парфюмам с использованием ИИ и автоматическим парсингом каталога. **ВСЕ ДАННЫЕ ИЗ БД ОТПРАВЛЯЮТСЯ В ПРОМПТ БЕЗ ОГРАНИЧЕНИЙ**.

## 🗄️ **АРХИТЕКТУРА БАЗЫ ДАННЫХ**

### **Схема БД (SQLite)**
```sql
-- Основная таблица парфюмов
CREATE TABLE perfumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article VARCHAR(50) UNIQUE NOT NULL,           -- Артикул товара
    unique_key VARCHAR(255) UNIQUE NOT NULL,       -- Уникальный ключ для дедупликации
    brand VARCHAR(100) NOT NULL,                   -- Бренд
    name VARCHAR(200) NOT NULL,                    -- Название аромата
    full_title TEXT NOT NULL,                      -- Полное название с мотивом
    factory VARCHAR(100),                          -- Фабрика-производитель
    factory_detailed VARCHAR(100),                 -- Детальная информация о фабрике
    price DECIMAL(10,2),                           -- Цена (числовая)
    price_formatted VARCHAR(50),                   -- Отформатированная цена
    currency VARCHAR(10) DEFAULT 'RUB',            -- Валюта
    gender VARCHAR(20),                            -- Пол (Женский/Мужской/Унисекс)
    fragrance_group TEXT,                          -- Ароматическая группа
    quality_level VARCHAR(50),                     -- Уровень качества
    url VARCHAR(500) NOT NULL,                     -- Ссылка на товар
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE                 -- Активность товара
);

-- Таблица пользователей
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,           -- Telegram User ID
    username VARCHAR(100),                         -- Username
    first_name VARCHAR(100),                       -- Имя
    last_name VARCHAR(100),                        -- Фамилия
    quiz_profile JSON,                             -- Профиль квиза
    preferences JSON,                              -- Предпочтения
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сессий пользователей
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    current_state VARCHAR(50),                     -- Текущее состояние бота
    quiz_answers JSON,                             -- Ответы квиза
    quiz_step INTEGER DEFAULT 0,                   -- Текущий шаг квиза
    context_data JSON,                             -- Контекстные данные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица статистики использования
CREATE TABLE usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action_type VARCHAR(50),                       -- Тип действия
    perfume_article VARCHAR(50),                   -- Артикул парфюма
    query_text TEXT,                               -- Текст запроса
    response_length INTEGER,                       -- Длина ответа
    api_tokens_used INTEGER,                       -- Использованные токены
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 **АЛГОРИТМ РАБОТЫ СИСТЕМЫ (БЕЗ ЛИМИТОВ)**

### **1. ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ**

```pseudocode
FUNCTION initialize_system():
    // Загружаем конфигурацию
    config = load_config_from_env()
    
    // Инициализируем подключение к БД
    db_connection = create_database_connection(config.db_path)
    
    // Создаем таблицы если не существуют
    create_tables_if_not_exist(db_connection)
    
    // Инициализируем Telegram бота
    bot = create_telegram_bot(config.bot_token)
    
    // Инициализируем OpenRouter API
    openrouter = create_openrouter_client(config.api_key)
    
    // Запускаем автопарсер в фоне
    start_auto_parser_scheduler()
    
    RETURN {bot, db_connection, openrouter, config}
```

### **2. ОБРАБОТКА ВХОДЯЩИХ СООБЩЕНИЙ**

```pseudocode
FUNCTION handle_user_message(update, context):
    user_id = update.user.id
    message_text = update.message.text
    
    // Получаем или создаем пользователя
    user = get_or_create_user(user_id, update.user)
    
    // Получаем текущую сессию
    session = get_user_session(user_id)
    
    // Определяем команду или состояние
    IF message_text starts with "/":
        handle_command(message_text, user, session)
    ELSE:
        handle_state_message(message_text, user, session)
    
    // Обновляем время последней активности
    update_user_activity(user_id)
```

### **3. ОБРАБОТКА КОМАНД**

```pseudocode
FUNCTION handle_command(command, user, session):
    SWITCH command:
        CASE "/start":
            // Сбрасываем сессию и показываем главное меню
            reset_user_session(user.id)
            show_main_menu(user.id)
            session.current_state = "MAIN_MENU"
            
        CASE "/help":
            show_help_message(user.id)
            
        CASE "/stats" (IF user is admin):
            show_admin_statistics(user.id)
            
        CASE "/parse" (IF user is admin):
            force_parse_catalog(user.id)
            
        DEFAULT:
            show_unknown_command_message(user.id)
```

### **4. ОБРАБОТКА СОСТОЯНИЙ**

```pseudocode
FUNCTION handle_state_message(message, user, session):
    SWITCH session.current_state:
        CASE "MAIN_MENU":
            handle_main_menu_selection(message, user, session)
            
        CASE "PERFUME_QUESTION":
            handle_perfume_question(message, user, session)
            
        CASE "QUIZ_IN_PROGRESS":
            handle_quiz_answer(message, user, session)
            
        CASE "FRAGRANCE_INFO":
            handle_fragrance_info_request(message, user, session)
            
        DEFAULT:
            reset_to_main_menu(user.id, session)
```

### **5. ОБРАБОТКА ВОПРОСОВ О ПАРФЮМАХ (ВСЕ ДАННЫЕ)**

```pseudocode
FUNCTION handle_perfume_question(message, user, session):
    // Проверяем кулдаун API
    IF is_api_cooldown_active(user.id):
        send_cooldown_message(user.id)
        RETURN
    
    // ПОЛУЧАЕМ ВСЕ ДАННЫЕ ПАРФЮМОВ ИЗ БД БЕЗ ЛИМИТОВ
    perfumes_data = get_all_perfumes_from_database()
    
    // Создаем промпт для ИИ со ВСЕМИ данными
    prompt = create_perfume_question_prompt(message, perfumes_data)
    
    // Отправляем запрос в OpenRouter API
    ai_response = call_openrouter_api(prompt, max_tokens=4000)
    
    // Обрабатываем ответ и добавляем ссылки
    processed_response = process_ai_response_with_links(ai_response)
    
    // Отправляем ответ пользователю
    send_formatted_response(user.id, processed_response)
    
    // Сохраняем статистику
    save_usage_stat(user.id, "perfume_question", null, message, len(processed_response))
    
    // Устанавливаем кулдаун
    set_api_cooldown(user.id, 30 seconds)
    
    // Возвращаем в главное меню
    session.current_state = "MAIN_MENU"
    show_main_menu(user.id)
```

### **6. СИСТЕМА КВИЗА**

```pseudocode
FUNCTION start_quiz(user, session):
    // Сбрасываем ответы квиза
    session.quiz_answers = {}
    session.quiz_step = 0
    session.current_state = "QUIZ_IN_PROGRESS"
    
    // Показываем первый вопрос
    show_quiz_question(user.id, session.quiz_step)

FUNCTION handle_quiz_answer(message, user, session):
    // Сохраняем ответ
    current_question = get_quiz_question(session.quiz_step)
    session.quiz_answers[current_question.key] = message
    session.quiz_step += 1
    
    // Проверяем, есть ли еще вопросы
    IF session.quiz_step < total_quiz_questions:
        show_quiz_question(user.id, session.quiz_step)
    ELSE:
        show_quiz_results(user, session)

FUNCTION show_quiz_results(user, session):
    // Анализируем ответы и создаем профиль
    user_profile = analyze_quiz_answers(session.quiz_answers)
    
    // ПОЛУЧАЕМ ВСЕ ПОДХОДЯЩИЕ ПАРФЮМЫ ИЗ БД БЕЗ ЛИМИТОВ
    suitable_perfumes = get_all_perfumes_for_profile(user_profile)
    
    // Создаем промпт для рекомендаций со ВСЕМИ данными
    prompt = create_quiz_results_prompt(user_profile, suitable_perfumes)
    
    // Получаем рекомендации от ИИ
    ai_response = call_openrouter_api(prompt, max_tokens=4000)
    
    // Обрабатываем ответ
    processed_response = process_ai_response_with_links(ai_response)
    
    // Отправляем результаты
    send_quiz_results(user.id, processed_response)
    
    // Сохраняем профиль пользователя
    save_user_quiz_profile(user.id, user_profile)
    
    // Возвращаем в главное меню
    session.current_state = "MAIN_MENU"
    show_main_menu(user.id)
```

### **7. ПОЛУЧЕНИЕ ВСЕХ ДАННЫХ ИЗ БД**

```pseudocode
FUNCTION get_all_perfumes_from_database():
    // ПОЛУЧАЕМ ВСЕ АКТИВНЫЕ ПАРФЮМЫ БЕЗ ЛИМИТОВ
    query = """
    SELECT name, factory, article, price_formatted, brand, gender, fragrance_group, quality_level
    FROM perfumes 
    WHERE is_active = TRUE 
    ORDER BY brand, name
    """
    
    perfumes = execute_query(query)
    RETURN perfumes

FUNCTION get_all_perfumes_for_profile(user_profile):
    // ПОЛУЧАЕМ ВСЕ ПАРФЮМЫ БЕЗ ФИЛЬТРАЦИИ ПО ЛИМИТАМ
    query = """
    SELECT name, factory, article, price_formatted, brand, gender, fragrance_group, quality_level
    FROM perfumes 
    WHERE is_active = TRUE 
    ORDER BY brand, name
    """
    
    perfumes = execute_query(query)
    RETURN perfumes
```

### **8. СОЗДАНИЕ ПРОМПТОВ СО ВСЕМИ ДАННЫМИ**

```pseudocode
FUNCTION create_perfume_question_prompt(user_question, perfumes_data):
    // ФОРМИРУЕМ СПИСОК ВСЕХ ПАРФЮМОВ БЕЗ ЛИМИТОВ
    perfumes_list = []
    FOR EACH perfume IN perfumes_data:
        perfumes_list.append(
            perfume.name + " | " + 
            perfume.factory + " | " + 
            perfume.article + " | " + 
            perfume.price_formatted + " | " +
            perfume.brand + " | " +
            perfume.gender + " | " +
            perfume.fragrance_group
        )
    
    // Создаем промпт со ВСЕМИ данными
    prompt = """
    Ты - эксперт-парфюмер. Ответь на вопрос клиента.
    
    ВОПРОС: "{user_question}"
    
    ВСЕ ДОСТУПНЫЕ АРОМАТЫ (Название | Фабрика | Артикул | Цена | Бренд | Пол | Ароматическая группа):
    {perfumes_list}
    
    ИНСТРУКЦИИ:
    1. Выбери 3-5 наиболее подходящих ароматов из ВСЕГО каталога
    2. Для каждого обязательно укажи артикул в формате [Артикул: XXX]
    3. Объясни почему аромат подходит для данного запроса
    4. Дай практические советы по использованию
    5. Учитывай все характеристики: бренд, пол, ароматическую группу, цену
    
    ФОРМАТ ОТВЕТА:
    🎯 **Рекомендуемые ароматы:**
    
    1. **[Название]** ([Фабрика]) [Артикул: XXX]
       - Бренд: [бренд]
       - Пол: [пол]
       - Ароматическая группа: [группа]
       - Цена: [цена]
       - Почему подходит: [объяснение]
       - Советы по использованию: [практика]
    
    💡 **Дополнительные рекомендации:**
    [Общие советы и лайфхаки]
    
    ВАЖНО: Обязательно указывай артикул в формате [Артикул: XXX] для каждого аромата!
    """
    
    RETURN prompt

FUNCTION create_quiz_results_prompt(user_profile, suitable_perfumes):
    // Анализируем профиль пользователя
    profile_summary = analyze_user_profile(user_profile)
    
    // ФОРМИРУЕМ СПИСОК ВСЕХ ПОДХОДЯЩИХ ПАРФЮМОВ БЕЗ ЛИМИТОВ
    perfumes_list = []
    FOR EACH perfume IN suitable_perfumes:
        perfumes_list.append(
            perfume.name + " | " + 
            perfume.factory + " | " + 
            perfume.article + " | " + 
            perfume.price_formatted + " | " +
            perfume.brand + " | " +
            perfume.gender + " | " +
            perfume.fragrance_group + " | " +
            perfume.quality_level
        )
    
    prompt = """
    Ты - эксперт-парфюмер. Создай персонализированные рекомендации.
    
    ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
    {profile_summary}
    
    ВСЕ ПОДХОДЯЩИЕ АРОМАТЫ (Название | Фабрика | Артикул | Цена | Бренд | Пол | Ароматическая группа | Качество):
    {perfumes_list}
    
    ИНСТРУКЦИИ:
    1. Выбери 5-7 наиболее подходящих ароматов из ВСЕГО каталога
    2. Объясни почему каждый аромат подходит данному профилю
    3. Учитывай все характеристики: бренд, пол, ароматическую группу, цену, качество
    4. Дай рекомендации по использованию
    5. Обязательно указывай артикулы в формате [Артикул: XXX]
    
    ФОРМАТ ОТВЕТА:
    🎯 **Персональные рекомендации для вас:**
    
    1. **[Название]** ([Фабрика]) [Артикул: XXX]
       - Бренд: [бренд]
       - Пол: [пол]
       - Ароматическая группа: [группа]
       - Качество: [качество]
       - Цена: [цена]
       - Почему подходит вашему профилю: [объяснение]
       - Рекомендации по использованию: [советы]
    
    💡 **Общие рекомендации:**
    [Советы по выбору и использованию парфюмов]
    
    ВАЖНО: Обязательно указывай артикул в формате [Артикул: XXX] для каждого аромата!
    """
    
    RETURN prompt
```

### **9. ОБРАБОТКА ИНФОРМАЦИИ ОБ АРОМАТЕ (ВСЕ ДАННЫЕ)**

```pseudocode
FUNCTION handle_fragrance_info_request(message, user, session):
    // ПОЛУЧАЕМ ВСЕ ДАННЫЕ ПАРФЮМОВ ДЛЯ ПОИСКА
    all_perfumes = get_all_perfumes_from_database()
    
    // Ищем подходящие ароматы по запросу
    matching_perfumes = find_perfumes_by_query(message, all_perfumes)
    
    // Создаем промпт со ВСЕМИ найденными ароматами
    prompt = create_fragrance_info_prompt(message, matching_perfumes)
    
    // Получаем информацию от ИИ
    ai_response = call_openrouter_api(prompt, max_tokens=3000)
    
    // Обрабатываем ответ
    processed_response = process_ai_response_with_links(ai_response)
    
    // Отправляем информацию
    send_formatted_response(user.id, processed_response)
    
    // Возвращаем в главное меню
    session.current_state = "MAIN_MENU"
    show_main_menu(user.id)

FUNCTION find_perfumes_by_query(query, all_perfumes):
    // Ищем все парфюмы, соответствующие запросу
    matching = []
    query_lower = to_lowercase(query)
    
    FOR EACH perfume IN all_perfumes:
        IF contains(perfume.name.lower(), query_lower) OR
           contains(perfume.brand.lower(), query_lower) OR
           contains(perfume.factory.lower(), query_lower):
            matching.append(perfume)
    
    RETURN matching
```

### **10. АВТОМАТИЧЕСКИЙ ПАРСЕР**

```pseudocode
FUNCTION auto_parser_scheduler():
    // Запускаем планировщик
    schedule.every(6).hours.do(check_and_parse_catalog)
    schedule.every().day.at("06:00").do(daily_full_parse)
    schedule.every().sunday.at("03:00").do(weekly_full_update)
    
    WHILE True:
        schedule.run_pending()
        sleep(60 seconds)

FUNCTION check_and_parse_catalog():
    // Проверяем изменения на сайте
    IF has_catalog_changes():
        // Запускаем парсинг
        parse_and_save_catalog()
        
        // Перезапускаем бота для применения обновлений
        restart_bot_service()
        
        // Уведомляем администратора
        notify_admin("Каталог обновлен")
    ELSE:
        log("Изменений в каталоге не обнаружено")

FUNCTION parse_and_save_catalog():
    // Парсим каталог с сайта
    raw_perfumes = parse_aroma_euro_catalog()
    
    // Обрабатываем каждый парфюм
    FOR EACH perfume IN raw_perfumes:
        // Нормализуем данные
        normalized_perfume = normalize_perfume_data(perfume)
        
        // Сохраняем в БД (ВСЕ ДАННЫЕ)
        save_perfume_to_database(normalized_perfume)
    
    // Обновляем поисковые индексы
    update_search_indexes()
    
    log("Парсинг завершен: " + count + " парфюмов обработано и сохранено")
```

### **11. ОБРАБОТКА ДАННЫХ ПАРФЮМОВ**

```pseudocode
FUNCTION normalize_perfume_data(raw_perfume):
    // Извлекаем основные данные
    article = extract_article(raw_perfume.full_title)
    brand = raw_perfume.brand
    name = raw_perfume.name
    factory = raw_perfume.factory
    
    // Обрабатываем цену
    price_str = raw_perfume.price
    price = extract_numeric_price(price_str)
    
    // Создаем уникальный ключ
    unique_key = create_unique_key(brand, name, factory)
    
    // Извлекаем детали
    details = raw_perfume.details
    gender = details.gender
    fragrance_group = details.fragrance_group
    quality_level = details.quality
    
    RETURN {
        article: article,
        unique_key: unique_key,
        brand: brand,
        name: name,
        full_title: raw_perfume.full_title,
        factory: factory,
        factory_detailed: details.factory_detailed,
        price: price,
        price_formatted: price_str,
        gender: gender,
        fragrance_group: fragrance_group,
        quality_level: quality_level,
        url: raw_perfume.url
    }

FUNCTION save_perfume_to_database(perfume_data):
    // Проверяем существование по unique_key
    existing = get_perfume_by_unique_key(perfume_data.unique_key)
    
    IF existing:
        // Обновляем существующий (ВСЕ ПОЛЯ)
        update_perfume_completely(existing.id, perfume_data)
    ELSE:
        // Создаем новый (ВСЕ ПОЛЯ)
        insert_perfume_complete(perfume_data)
```

### **12. ОБРАБОТКА ОТВЕТОВ ИИ**

```pseudocode
FUNCTION process_ai_response_with_links(ai_response):
    // Ищем ВСЕ артикулы в ответе
    article_pattern = "\[Артикул:\s*([A-Z0-9\-]+)\]"
    matches = find_all_matches(ai_response, article_pattern)
    
    processed_response = ai_response
    
    FOR EACH match IN matches:
        article = match.group(1)
        
        // Получаем ссылку из БД
        url = get_perfume_url_by_article(article)
        
        IF url:
            // Заменяем артикул на кликабельную ссылку
            article_mark = "[Артикул: " + article + "]"
            link_mark = "[🛒 Заказать " + article + "](" + url + ")"
            processed_response = replace(processed_response, article_mark, link_mark)
    
    // Форматируем текст для Telegram
    formatted_response = format_text_for_telegram(processed_response)
    
    RETURN formatted_response

FUNCTION get_perfume_url_by_article(article):
    query = "SELECT url FROM perfumes WHERE article = ? AND is_active = TRUE"
    result = execute_query(query, [article])
    
    IF result:
        RETURN result[0].url
    ELSE:
        RETURN null
```

### **13. УПРАВЛЕНИЕ СОСТОЯНИЯМИ ПОЛЬЗОВАТЕЛЯ**

```pseudocode
FUNCTION get_user_session(user_id):
    // Ищем существующую сессию
    session = find_session_by_user_id(user_id)
    
    IF session:
        // Проверяем актуальность сессии
        IF is_session_expired(session):
            delete_session(session.id)
            session = null
    
    IF NOT session:
        // Создаем новую сессию
        session = create_new_session(user_id)
    
    RETURN session

FUNCTION update_session_state(user_id, new_state, context_data = null):
    session = get_user_session(user_id)
    session.current_state = new_state
    
    IF context_data:
        session.context_data = context_data
    
    session.updated_at = current_timestamp()
    save_session(session)
```

### **14. СТАТИСТИКА И МОНИТОРИНГ**

```pseudocode
FUNCTION save_usage_stat(user_id, action_type, perfume_article, query_text, response_length):
    stat = {
        user_id: user_id,
        action_type: action_type,
        perfume_article: perfume_article,
        query_text: query_text,
        response_length: response_length,
        api_tokens_used: estimate_tokens_used(query_text, response_length),
        created_at: current_timestamp()
    }
    
    insert_usage_stat(stat)

FUNCTION get_admin_statistics():
    stats = {
        total_users: count_users(),
        active_users_today: count_active_users_today(),
        total_perfumes: count_perfumes(),
        total_questions: count_usage_stats_by_type("perfume_question"),
        total_quizzes: count_usage_stats_by_type("quiz_completed"),
        api_usage_today: sum_api_tokens_today()
    }
    
    RETURN stats
```

### **15. ОПТИМИЗАЦИЯ ДЛЯ БОЛЬШИХ ОБЪЕМОВ ДАННЫХ**

```pseudocode
FUNCTION optimize_large_prompt(perfumes_data):
    // Если данных слишком много, группируем по категориям
    IF length(perfumes_data) > 5000:
        // Группируем по брендам
        grouped_perfumes = group_perfumes_by_brand(perfumes_data)
        
        // Создаем краткую сводку
        summary = create_brand_summary(grouped_perfumes)
        
        // Добавляем полный список в конце
        full_list = format_all_perfumes_compact(perfumes_data)
        
        RETURN summary + "\n\nПОЛНЫЙ СПИСОК АРОМАТОВ:\n" + full_list
    ELSE:
        // Возвращаем полный список
        RETURN format_all_perfumes_detailed(perfumes_data)

FUNCTION group_perfumes_by_brand(perfumes_data):
    groups = {}
    FOR EACH perfume IN perfumes_data:
        brand = perfume.brand
        IF NOT groups[brand]:
            groups[brand] = []
        groups[brand].append(perfume)
    
    RETURN groups

FUNCTION create_brand_summary(grouped_perfumes):
    summary = "КРАТКАЯ СВОДКА ПО БРЕНДАМ:\n"
    
    FOR EACH brand, perfumes IN grouped_perfumes:
        summary += f"\n{brand}: {length(perfumes)} ароматов"
        // Добавляем несколько примеров
        FOR i = 0 TO min(3, length(perfumes)):
            summary += f"\n  - {perfumes[i].name} ({perfumes[i].factory}) [Артикул: {perfumes[i].article}]"
    
    RETURN summary
```

## 🔧 **ТЕХНИЧЕСКИЕ ДЕТАЛИ**

### **Конфигурация системы**
```python
CONFIG = {
    'bot_token': 'TELEGRAM_BOT_TOKEN',
    'openrouter_api_key': 'OPENROUTER_API_KEY',
    'admin_user_id': 123456789,
    'database_path': 'perfumes.db',
    'api_cooldown_seconds': 30,
    'max_tokens_per_request': 8000,  # Увеличиваем лимит токенов
    'parse_interval_hours': 6,
    # УБИРАЕМ ВСЕ ЛИМИТЫ НА КОЛИЧЕСТВО ПАРФЮМОВ
    'use_all_perfumes': True,  # Всегда использовать все парфюмы
    'no_limits_mode': True     # Режим без лимитов
}
```

### **Обработка ошибок**
```pseudocode
FUNCTION handle_error(error, context):
    // Логируем ошибку
    log_error(error, context)
    
    // Уведомляем пользователя
    send_error_message(context.user_id, "Произошла ошибка. Попробуйте позже.")
    
    // Сбрасываем состояние пользователя
    reset_user_session(context.user_id)
    
    // Показываем главное меню
    show_main_menu(context.user_id)
```

### **Кэширование и оптимизация**
```pseudocode
FUNCTION get_all_perfumes_from_database():
    // Проверяем кэш
    cache_key = "all_perfumes"
    cached_data = get_cache(cache_key)
    
    IF cached_data AND is_cache_valid(cached_data):
        RETURN cached_data.data
    
    // Получаем данные из БД
    query = "SELECT name, factory, article, price_formatted, brand, gender, fragrance_group, quality_level FROM perfumes WHERE is_active = TRUE ORDER BY brand, name"
    data = execute_query(query)
    
    // Кэшируем результат на 1 час
    set_cache(cache_key, data, ttl=3600)
    
    RETURN data
```

## 🚀 **ПРЕИМУЩЕСТВА АРХИТЕКТУРЫ БЕЗ ЛИМИТОВ**

### **1. Максимальная полнота данных**
- **Все парфюмы** доступны для ИИ
- **Полная информация** о каждом аромате
- **Точные рекомендации** на основе всего каталога

### **2. Простота реализации**
- **Один запрос** к БД вместо сложной логики
- **Нет ограничений** на количество данных
- **Прямая передача** всех данных в промпт

### **3. Качество рекомендаций**
- **ИИ видит весь каталог** и может выбрать лучшее
- **Нет пропуска** подходящих ароматов
- **Полный контекст** для принятия решений

### **4. Масштабируемость**
- **Работает с любым количеством** парфюмов
- **Автоматическая оптимизация** больших промптов
- **Гибкая группировка** данных при необходимости

## 📋 **ТРЕБОВАНИЯ К РЕАЛИЗАЦИИ**

### **Технологический стек**
- **Язык программирования**: Python 3.9+
- **База данных**: SQLite (для разработки), PostgreSQL (для продакшена)
- **Telegram Bot API**: python-telegram-bot 20.7+
- **ИИ API**: OpenRouter API
- **Парсинг**: BeautifulSoup4, requests
- **Планировщик**: schedule

### **Структура проекта**
```
perfume-bot/
├── main.py                 # Главный файл бота
├── database/
│   ├── models.py          # Модели БД
│   ├── manager.py         # Менеджер БД
│   └── migrations.py      # Миграции
├── parsers/
│   ├── catalog_parser.py  # Парсер каталога
│   └── auto_parser.py     # Автопарсер
├── ai/
│   ├── prompts.py         # Промпты для ИИ
│   └── processor.py       # Обработка ответов
├── quiz/
│   └── quiz_system.py     # Система квиза
├── config.py              # Конфигурация
├── requirements.txt       # Зависимости
└── docker-compose.yml     # Docker конфигурация
```

Эта архитектура обеспечивает максимальное использование всех данных каталога без искусственных ограничений, что значительно повышает качество рекомендаций ИИ.