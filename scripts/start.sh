#!/bin/bash

# Скрипт для запуска парфюмерного бота

echo "🚀 Запускаем парфюмерного консультанта..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Запустите deploy.sh для первоначальной настройки."
    exit 1
fi

# Запускаем контейнеры
docker-compose up -d

echo "✅ Бот запущен!"
echo ""
echo "📋 Статус сервисов:"
docker-compose ps

echo ""
echo "🔧 Полезные команды:"
echo "  Просмотр логов: docker-compose logs -f perfume-bot"
echo "  Остановка:      docker-compose down"