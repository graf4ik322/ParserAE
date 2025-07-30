#!/bin/bash

# Скрипт для обновления парфюмерного бота

echo "🔄 Обновляем парфюмерного консультанта..."

# Останавливаем контейнеры
echo "🛑 Останавливаем сервисы..."
docker-compose down

# Получаем последние изменения (если используется git)
if [ -d ".git" ]; then
    echo "📥 Получаем последние изменения из репозитория..."
    git pull
fi

# Пересобираем образ
echo "🔨 Пересобираем Docker образ..."
docker-compose build --no-cache

# Запускаем обновленные сервисы
echo "🚀 Запускаем обновленные сервисы..."
docker-compose up -d

# Проверяем статус
echo "📊 Проверяем статус..."
sleep 5
docker-compose ps

echo ""
echo "✅ Обновление завершено!"
echo ""
echo "📋 Последние логи:"
docker-compose logs --tail=10 perfume-bot