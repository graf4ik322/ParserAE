# 🚀 Развертывание Парфюмерного Консультант-Бота v2.0

## 📋 Обзор проекта

Парфюмерный Консультант-Бот - это полнофункциональная система для консультации по парфюмам с использованием ИИ и автоматическим парсингом каталога aroma-euro.ru.

### 🎯 Ключевые особенности:
- **ИИ-консультант** на базе OpenRouter API с доступом ко ВСЕМУ каталогу (режим без лимитов)
- **Автоматический парсинг** каталога с регулярными обновлениями
- **Интерактивная система квизов** для определения предпочтений
- **Telegram бот** с удобным интерфейсом
- **База данных SQLite** с полной схемой данных
- **Docker-контейнеризация** для легкого развертывания

## 🔧 Предварительные требования

### Системные требования:
- **Docker** и **Docker Compose** (рекомендуется)
- Или **Python 3.11+** для ручного запуска
- **2GB RAM** минимум (рекомендуется 4GB)
- **10GB свободного места** на диске

### API ключи (обязательно):
1. **Telegram Bot Token** - создайте бота через [@BotFather](https://t.me/botfather)
2. **OpenRouter API Key** - зарегистрируйтесь на [OpenRouter.ai](https://openrouter.ai/)
3. **Admin User ID** - ваш Telegram ID (получите через [@userinfobot](https://t.me/userinfobot))

## 🚀 Быстрый запуск с Docker (рекомендуется)

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd perfume-bot
```

### 2. Настройка переменных окружения
```bash
# Копируем пример конфигурации
cp .env.example .env

# Редактируем файл .env
nano .env
```

Заполните обязательные переменные в `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
ADMIN_USER_ID=123456789
```

### 3. Создание директорий
```bash
mkdir -p data logs
chmod 755 data logs
```

### 4. Запуск с Docker Compose
```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## 🔧 Ручной запуск (без Docker)

### 1. Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
```bash
# Копируем и редактируем .env
cp .env.example .env
nano .env
```

### 3. Запуск приложения
```bash
python main.py
```

## ⚙️ Конфигурация

### Основные переменные окружения:

| Переменная | Описание | Обязательна | По умолчанию |
|------------|----------|-------------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | ✅ | - |
| `OPENROUTER_API_KEY` | API ключ OpenRouter | ✅ | - |
| `ADMIN_USER_ID` | Telegram ID администратора | ✅ | - |
| `DATABASE_PATH` | Путь к файлу БД | ❌ | `perfumes.db` |
| `API_COOLDOWN_SECONDS` | Кулдаун между запросами | ❌ | `30` |
| `MAX_TOKENS_PER_REQUEST` | Максимум токенов на запрос | ❌ | `8000` |
| `PARSE_INTERVAL_HOURS` | Интервал парсинга (часы) | ❌ | `6` |
| `PARSER_MAX_WORKERS` | Потоки для парсинга | ❌ | `3` |
| `LOG_LEVEL` | Уровень логирования | ❌ | `INFO` |

### Расширенные настройки:
```env
# OpenRouter настройки
OPENROUTER_MODEL=openai/gpt-4-turbo-preview

# Настройки кэширования
CACHE_TTL_SECONDS=3600

# Настройки запросов
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

## 📊 Инициализация данных

При первом запуске система автоматически:

1. **Создает таблицы БД** согласно схеме
2. **Загружает данные** из `full_perfumes_catalog_complete.json` (если файл существует)
3. **Запускает планировщик** автоматического парсинга

### Ручная загрузка данных:
```bash
# Если нужно принудительно обновить каталог
# Отправьте команду /parse администратору в Telegram
```

## 🔍 Мониторинг и логи

### Просмотр логов:
```bash
# Docker
docker-compose logs -f

# Ручной запуск
tail -f perfume_bot.log
```

### Основные лог-файлы:
- `perfume_bot.log` - Основные логи приложения
- `complete_parser.log` - Логи парсера

### Статистика (команда /stats для админа):
- Количество пользователей
- Количество парфюмов в БД
- Статистика использования API
- Активность пользователей

## 🛡️ Безопасность

### Рекомендации:
1. **Не публикуйте** файл `.env` в репозитории
2. **Ограничьте доступ** к серверу с ботом
3. **Регулярно обновляйте** зависимости
4. **Мониторьте** использование API токенов
5. **Делайте резервные копии** базы данных

### Создание резервной копии:
```bash
# Копирование БД
cp data/perfumes.db backup/perfumes_$(date +%Y%m%d).db

# Архивирование логов
tar -czf backup/logs_$(date +%Y%m%d).tar.gz logs/
```

## 🔧 Администрирование

### Команды администратора в Telegram:
- `/stats` - Статистика системы
- `/parse` - Принудительное обновление каталога
- `/help` - Справка

### Обслуживание:
```bash
# Проверка статуса контейнера
docker-compose ps

# Перезапуск сервиса
docker-compose restart

# Обновление образа
docker-compose pull
docker-compose up -d

# Очистка ресурсов
docker system prune
```

## 📈 Масштабирование

### Для высоких нагрузок:
1. **Увеличьте ресурсы** контейнера
2. **Настройте rate limiting** в OpenRouter
3. **Оптимизируйте кэширование**
4. **Рассмотрите PostgreSQL** вместо SQLite

### Настройки производительности:
```env
# Увеличение лимитов
MAX_TOKENS_PER_REQUEST=12000
PARSER_MAX_WORKERS=5
CACHE_TTL_SECONDS=7200

# Оптимизация парсинга
PARSE_INTERVAL_HOURS=12
```

## 🐛 Устранение неполадок

### Частые проблемы:

#### Бот не отвечает:
```bash
# Проверьте логи
docker-compose logs perfume-bot

# Проверьте токен бота
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

#### Ошибки OpenRouter API:
```bash
# Проверьте API ключ
curl -H "Authorization: Bearer <API_KEY>" https://openrouter.ai/api/v1/models
```

#### Проблемы с БД:
```bash
# Проверьте файл БД
sqlite3 data/perfumes.db ".tables"

# Пересоздание БД (удалит все данные!)
rm data/perfumes.db
# Перезапустите бота
```

#### Проблемы с парсингом:
```bash
# Проверьте доступность сайта
curl -I https://aroma-euro.ru/perfume/

# Логи парсера
grep "парсинг\|parsing" perfume_bot.log
```

## 📞 Поддержка

### Логи для отладки:
```bash
# Подробное логирование
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart

# Экспорт логов
docker-compose logs > debug_logs.txt
```

### Системная информация:
```bash
# Версия Docker
docker --version
docker-compose --version

# Использование ресурсов
docker stats

# Место на диске
df -h
```

## 🔄 Обновление системы

### Обновление кода:
```bash
# Остановка сервиса
docker-compose down

# Обновление кода
git pull

# Пересборка и запуск
docker-compose build --no-cache
docker-compose up -d
```

### Миграция БД:
При обновлениях схемы БД система автоматически применит миграции при запуске.

---

## 🎉 Готово!

Ваш Парфюмерный Консультант-Бот готов к работе! 

**Найдите своего бота в Telegram и отправьте команду `/start`**

Для получения статистики (только для администратора): `/stats`