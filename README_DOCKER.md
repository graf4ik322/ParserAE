# 🐳 Perfume Consultant Bot v2.0 - Docker Deployment

Полное руководство по развертыванию Perfume Consultant Bot v2.0 в Docker контейнерах.

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий
git clone <repository_url>
cd perfume-bot

# Скопируйте и настройте переменные окружения
cp .env.docker .env
# Отредактируйте .env файл с вашими токенами
```

### 2. Базовый запуск

```bash
# Используйте удобный скрипт управления
./docker/docker-control.sh start

# Или напрямую через docker-compose
docker-compose -f docker-compose.v2.yml up -d
```

### 3. Проверка статуса

```bash
./docker/docker-control.sh status
```

## 📋 Команды управления

### Основные команды

```bash
# Запуск (базовая конфигурация)
./docker/docker-control.sh start

# Запуск с различными профилями
./docker/docker-control.sh start redis      # С Redis кэшем
./docker/docker-control.sh start postgres  # С PostgreSQL
./docker/docker-control.sh start monitoring # С мониторингом
./docker/docker-control.sh start full      # Полная конфигурация

# Остановка
./docker/docker-control.sh stop

# Перезапуск
./docker/docker-control.sh restart

# Статус сервисов
./docker/docker-control.sh status

# Просмотр логов
./docker/docker-control.sh logs
./docker/docker-control.sh logs perfume-bot

# Обновление данных
./docker/docker-control.sh update

# Подключение к контейнеру
./docker/docker-control.sh shell

# Пересборка образов
./docker/docker-control.sh build

# Полная очистка
./docker/docker-control.sh clean
```

## 🏗️ Архитектура Docker

### Основные сервисы

```yaml
services:
  perfume-bot:     # Основное приложение
  redis:           # Кэширование (опционально)
  postgres:        # База данных (опционально)
  nginx:           # Прокси-сервер (опционально)
  prometheus:      # Мониторинг (опционально)
  grafana:         # Визуализация (опционально)
```

### Профили развертывания

| Профиль | Описание | Сервисы |
|---------|----------|---------|
| `basic` | Минимальная конфигурация | perfume-bot |
| `redis` | С кэшированием | perfume-bot + redis |
| `postgres` | С базой данных | perfume-bot + postgres |
| `monitoring` | С мониторингом | perfume-bot + prometheus + grafana |
| `full` | Полная конфигурация | Все сервисы |

## ⚙️ Конфигурация

### Переменные окружения

Основные переменные в `.env` файле:

```env
# Обязательные
BOT_TOKEN=your_telegram_bot_token
ADMIN_USER_ID=your_telegram_user_id
OPENROUTER_API_KEY=your_openrouter_api_key

# Опциональные
OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324:free
LOG_LEVEL=INFO
UPDATE_INTERVAL_HOURS=24
ENVIRONMENT=production
```

### Volumes (Постоянные данные)

```yaml
volumes:
  - ./perfume_bot/data:/app/perfume_bot/data  # Данные парфюмов
  - ./logs:/app/logs                          # Логи приложения
  - ./.env:/app/.env:ro                       # Конфигурация
```

### Порты

| Сервис | Порт | Описание |
|--------|------|----------|
| perfume-bot | 8080 | Веб-интерфейс (будущий) |
| grafana | 3000 | Мониторинг |
| prometheus | 9090 | Метрики |
| nginx | 80, 443 | HTTP/HTTPS прокси |

## 🔧 Управление данными

### Обновление данных парфюмов

```bash
# Ручное обновление
./docker/docker-control.sh update

# Или через docker exec
docker exec perfume-bot-v2 python run_perfume_bot.py update
```

### Резервное копирование

```bash
# Создание бэкапа данных
docker run --rm -v $(pwd)/perfume_bot/data:/data -v $(pwd)/backup:/backup \
  alpine tar czf /backup/perfume-data-$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Восстановление из бэкапа
docker run --rm -v $(pwd)/perfume_bot/data:/data -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/perfume-data-YYYYMMDD_HHMMSS.tar.gz -C /data
```

### Очистка кэша

```bash
# Очистка кэша через API
docker exec perfume-bot-v2 python -c "
from perfume_bot.core.application import app
import asyncio
asyncio.run(app.clear_cache())
"
```

## 📊 Мониторинг

### Healthcheck

Docker автоматически проверяет здоровье контейнера:

```bash
# Проверка статуса здоровья
docker inspect perfume-bot-v2 | jq '.[0].State.Health'
```

### Логи

```bash
# Логи основного приложения
docker logs -f perfume-bot-v2

# Логи всех сервисов
docker-compose -f docker-compose.v2.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.v2.yml logs -f redis
```

### Метрики (с профилем monitoring)

После запуска с профилем `monitoring`:

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## 🔍 Отладка

### Подключение к контейнеру

```bash
# Через скрипт управления
./docker/docker-control.sh shell

# Напрямую
docker exec -it perfume-bot-v2 /bin/bash
```

### Проверка конфигурации

```bash
# Проверка переменных окружения
docker exec perfume-bot-v2 env | grep -E "(BOT_TOKEN|OPENROUTER|ADMIN)"

# Проверка конфигурации Python
docker exec perfume-bot-v2 python -c "
from perfume_bot.core.config import config
print('✅ Конфигурация загружена успешно')
print(f'Модель: {config.api.model}')
print(f'Админ ID: {config.bot.admin_user_id}')
"
```

### Тестирование API

```bash
# Тест OpenRouter API
docker exec perfume-bot-v2 python -c "
import asyncio
from perfume_bot.api.openrouter_client import OpenRouterClient
from perfume_bot.core.config import config

async def test():
    client = OpenRouterClient(config.api.api_key, model=config.api.model)
    result = await client.check_api_key()
    print('✅ API работает' if result.success else f'❌ API ошибка: {result.error}')

asyncio.run(test())
"
```

## 🚨 Устранение неполадок

### Проблема: Контейнер не запускается

```bash
# Проверьте логи
docker logs perfume-bot-v2

# Проверьте переменные окружения
cat .env

# Пересоберите образ
./docker/docker-control.sh build
```

### Проблема: API не работает

```bash
# Проверьте ключи API
docker exec perfume-bot-v2 python -c "
from perfume_bot.core.config import config
print(f'API Key: {config.api.api_key[:20]}...')
print(f'Model: {config.api.model}')
"

# Тест подключения
docker exec perfume-bot-v2 curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Проблема: Нет данных

```bash
# Принудительное обновление
docker exec perfume-bot-v2 python run_perfume_bot.py update

# Проверка наличия файлов данных
docker exec perfume-bot-v2 ls -la /app/perfume_bot/data/processed/
```

## 🔒 Безопасность

### Рекомендации

1. **Переменные окружения**: Никогда не коммитьте `.env` файл с реальными токенами
2. **Пользователь**: Контейнер запускается от непривилегированного пользователя `perfume`
3. **Сеть**: Используется изолированная Docker сеть
4. **Ресурсы**: Установлены ограничения на память и CPU

### Обновление токенов

```bash
# Остановите сервисы
./docker/docker-control.sh stop

# Обновите .env файл
nano .env

# Перезапустите
./docker/docker-control.sh start
```

## 📈 Масштабирование

### Горизонтальное масштабирование

```bash
# Запуск нескольких экземпляров бота
docker-compose -f docker-compose.v2.yml up -d --scale perfume-bot=3
```

### Вертикальное масштабирование

Отредактируйте `docker-compose.v2.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 2G      # Увеличьте лимит памяти
      cpus: '1.0'     # Увеличьте лимит CPU
```

## 🔄 Обновление

### Обновление до новой версии

```bash
# Остановите сервисы
./docker/docker-control.sh stop

# Получите обновления
git pull

# Пересоберите образы
./docker/docker-control.sh build

# Запустите с новой версией
./docker/docker-control.sh start
```

## 📝 Примеры использования

### Разработка

```bash
# Запуск для разработки с монтированием кода
docker-compose -f docker-compose.v2.yml -f docker-compose.dev.yml up
```

### Продакшн

```bash
# Полная конфигурация для продакшна
./docker/docker-control.sh start full
```

### Тестирование

```bash
# Запуск только для тестирования
docker run --rm -it --env-file .env perfume-bot:latest python run_perfume_bot.py status
```

---

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `./docker/docker-control.sh logs`
2. Проверьте статус: `./docker/docker-control.sh status`
3. Проверьте конфигурацию: `cat .env`
4. Пересоберите образы: `./docker/docker-control.sh build`

**Happy Dockering! 🐳**