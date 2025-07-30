#!/bin/bash

# Скрипт для развертывания парфюмерного бота через Docker
# Версия: 1.0

set -e

echo "🚀 Начинаем развертывание парфюмерного консультанта..."

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаем из примера..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Файл .env создан из .env.example"
        echo "🔧 ВАЖНО: Отредактируйте .env файл с вашими настройками!"
        echo ""
        echo "Необходимо настроить:"
        echo "- BOT_TOKEN (получить у @BotFather)"
        echo "- OPENROUTER_API_KEY (получить на openrouter.ai)"
        echo "- ADMIN_USER_ID (получить у @userinfobot)"
        echo ""
        read -p "Нажмите Enter после настройки .env файла..."
    else
        echo "❌ Файл .env.example не найден. Создайте .env файл вручную."
        exit 1
    fi
fi

# Создаем директорию для логов
mkdir -p logs

# Проверяем наличие необходимых файлов данных
echo "🔍 Проверяем наличие файлов данных..."
required_files=(
    "full_perfumes_catalog_complete.json"
    "full_basic_catalog.json"
    "names_only.json"
    "brand_name.json"
    "name_factory.json"
    "brand_name_factory.json"
    "full_data_compact.json"
    "factory_analysis.json"
    "quiz_reference.json"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "⚠️  Отсутствуют файлы данных:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Запустите парсер для создания файлов данных:"
    echo "python3 data_normalizer.py"
    echo ""
    read -p "Продолжить развертывание без этих файлов? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose down --remove-orphans

# Собираем образ
echo "🔨 Собираем Docker образ..."
docker-compose build --no-cache

# Запускаем сервисы
echo "▶️  Запускаем сервисы..."
docker-compose up -d

# Проверяем статус
echo "📊 Проверяем статус сервисов..."
sleep 5
docker-compose ps

# Показываем логи
echo ""
echo "📋 Последние логи:"
docker-compose logs --tail=20 perfume-bot

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "🔧 Полезные команды:"
echo "  Просмотр логов:      docker-compose logs -f perfume-bot"
echo "  Перезапуск:          docker-compose restart perfume-bot"
echo "  Остановка:           docker-compose down"
echo "  Статус:              docker-compose ps"
echo ""
echo "🌐 Дополнительные сервисы:"
echo "  Логи (веб):          docker-compose --profile monitoring up -d"
echo "  Авто-обновления:     docker-compose --profile auto-update up -d"
echo ""
echo "🎉 Бот запущен и готов к работе!"