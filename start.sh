#!/bin/bash

# Скрипт быстрого запуска Парфюмерного Консультант-Бота

set -e  # Выход при ошибке

echo "🌸 Запуск Парфюмерного Консультант-Бота v2.0"
echo "=============================================="

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и Docker Compose."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose."
    exit 1
fi

# Проверяем файл .env
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создаем из примера..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Файл .env создан. Отредактируйте его перед запуском:"
        echo "   - TELEGRAM_BOT_TOKEN"
        echo "   - OPENROUTER_API_KEY" 
        echo "   - ADMIN_USER_ID"
        echo ""
        echo "Затем запустите скрипт еще раз."
        exit 1
    else
        echo "❌ Файл .env.example не найден!"
        exit 1
    fi
fi

# Проверяем обязательные переменные
echo "🔍 Проверяем конфигурацию..."

source .env

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не настроен в .env"
    exit 1
fi

if [ -z "$OPENROUTER_API_KEY" ] || [ "$OPENROUTER_API_KEY" = "your_openrouter_api_key_here" ]; then
    echo "❌ OPENROUTER_API_KEY не настроен в .env"
    exit 1
fi

if [ -z "$ADMIN_USER_ID" ] || [ "$ADMIN_USER_ID" = "123456789" ]; then
    echo "❌ ADMIN_USER_ID не настроен в .env"
    exit 1
fi

echo "✅ Конфигурация проверена"

# Создаем необходимые директории
echo "📁 Создаем директории..."
mkdir -p data logs
chmod 755 data logs

# Проверяем наличие JSON файла с данными
if [ -f "full_perfumes_catalog_complete.json" ]; then
    echo "📊 Найден файл с данными парфюмов"
else
    echo "⚠️  Файл full_perfumes_catalog_complete.json не найден"
    echo "   Данные будут загружены при первом парсинге"
fi

# Функция для остановки сервисов
cleanup() {
    echo ""
    echo "🛑 Остановка сервисов..."
    docker-compose down
    exit 0
}

# Обработка сигналов
trap cleanup SIGINT SIGTERM

# Запуск сервисов
echo "🚀 Запуск сервисов..."
echo ""

# Сборка образа (если нужно)
docker-compose build

# Запуск в фоне
docker-compose up -d

# Ждем запуска
echo "⏳ Ждем запуска сервисов..."
sleep 10

# Проверяем статус
if docker-compose ps | grep -q "Up"; then
    echo "✅ Сервисы запущены успешно!"
    echo ""
    echo "📱 Ваш бот готов к работе!"
    echo "   Найдите бота в Telegram и отправьте /start"
    echo ""
    echo "📊 Команды администратора:"
    echo "   /stats - статистика системы"
    echo "   /parse - обновить каталог"
    echo ""
    echo "🔍 Просмотр логов:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Остановка:"
    echo "   docker-compose down"
    echo ""
    echo "Нажмите Ctrl+C для остановки или запустите в фоне:"
    echo "   docker-compose up -d"
    
    # Показываем логи в реальном времени
    echo ""
    echo "📋 Логи в реальном времени (Ctrl+C для выхода):"
    echo "================================================"
    docker-compose logs -f
    
else
    echo "❌ Ошибка запуска сервисов!"
    echo "Проверьте логи: docker-compose logs"
    exit 1
fi