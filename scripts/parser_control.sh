#!/bin/bash

# Скрипт управления автопарсером парфюмерного каталога

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

show_help() {
    echo "🤖 Управление AutoParser для парфюмерного каталога"
    echo ""
    echo "Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  start       - Запустить автопарсер"
    echo "  stop        - Остановить автопарсер"
    echo "  restart     - Перезапустить автопарсер"
    echo "  status      - Показать статус автопарсера"
    echo "  logs        - Показать логи автопарсера"
    echo "  force-parse - Принудительно запустить парсинг"
    echo "  stats       - Показать статистику каталога"
    echo "  help        - Показать эту справку"
    echo ""
}

check_docker() {
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose не установлен"
        exit 1
    fi
}

start_parser() {
    echo "🚀 Запуск автопарсера..."
    check_docker
    docker-compose up -d auto-parser
    echo "✅ Автопарсер запущен"
    echo ""
    echo "📋 Статус:"
    docker-compose ps auto-parser
}

stop_parser() {
    echo "🛑 Остановка автопарсера..."
    check_docker
    docker-compose stop auto-parser
    echo "✅ Автопарсер остановлен"
}

restart_parser() {
    echo "🔄 Перезапуск автопарсера..."
    check_docker
    docker-compose restart auto-parser
    echo "✅ Автопарсер перезапущен"
    echo ""
    echo "📋 Статус:"
    docker-compose ps auto-parser
}

show_status() {
    echo "📊 Статус автопарсера:"
    echo ""
    check_docker
    
    # Статус контейнера
    echo "🐳 Docker контейнер:"
    docker-compose ps auto-parser
    echo ""
    
    # Проверяем файл последней проверки
    if [ -f "last_check.json" ]; then
        echo "📅 Последняя проверка:"
        cat last_check.json | python3 -m json.tool
        echo ""
    else
        echo "⚠️ Файл последней проверки не найден"
        echo ""
    fi
    
    # Размер лог файла
    if [ -f "auto_parser.log" ]; then
        LOG_SIZE=$(du -h auto_parser.log | cut -f1)
        LOG_LINES=$(wc -l < auto_parser.log)
        echo "📝 Лог файл: ${LOG_SIZE}, ${LOG_LINES} строк"
    else
        echo "📝 Лог файл не найден"
    fi
}

show_logs() {
    echo "📋 Логи автопарсера (последние 50 строк):"
    echo ""
    check_docker
    docker-compose logs --tail=50 auto-parser
}

force_parse() {
    echo "🔄 Принудительный запуск парсинга..."
    check_docker
    
    # Удаляем файл последней проверки для принудительного обновления
    if [ -f "last_check.json" ]; then
        rm last_check.json
        echo "🗑️ Удален файл последней проверки"
    fi
    
    # Отправляем сигнал контейнеру для немедленного парсинга
    docker-compose exec auto-parser python3 -c "
import os
import json
from datetime import datetime

# Создаем файл-триггер для немедленного парсинга
trigger_data = {
    'force_parse': True,
    'timestamp': datetime.now().isoformat(),
    'triggered_by': 'manual_script'
}

with open('/tmp/force_parse_trigger.json', 'w') as f:
    json.dump(trigger_data, f)

print('✅ Триггер принудительного парсинга создан')
"
    
    echo "🚀 Принудительный парсинг запущен"
    echo "📋 Следите за логами: $0 logs"
}

show_stats() {
    echo "📊 Статистика каталога парфюмов:"
    echo ""
    
    if [ -f "full_perfumes_catalog_complete.json" ]; then
        # Получаем статистику из JSON
        python3 -c "
import json
from collections import Counter
from datetime import datetime

with open('full_perfumes_catalog_complete.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

perfumes = data.get('perfumes', [])
metadata = data.get('metadata', {})

print(f'📅 Дата парсинга: {metadata.get(\"parsing_date\", \"Неизвестно\")}')
print(f'🧴 Всего ароматов: {len(perfumes)}')
print(f'🌐 Источник: {metadata.get(\"source\", \"aroma-euro.ru\")}')
print()

# Статистика по фабрикам
factories = [p.get('factory', 'Не указано') for p in perfumes if p.get('factory')]
factory_stats = Counter(factories)

print('🏭 Топ-10 фабрик:')
for factory, count in factory_stats.most_common(10):
    print(f'   {factory}: {count} ароматов')

print()

# Статистика по брендам
brands = [p.get('brand', 'Не указано') for p in perfumes if p.get('brand')]
brand_stats = Counter(brands)

print('🏷️ Топ-10 брендов:')
for brand, count in brand_stats.most_common(10):
    print(f'   {brand}: {count} ароматов')
"
    else
        echo "❌ Файл каталога не найден"
    fi
}

# Основная логика
case "${1:-help}" in
    "start")
        start_parser
        ;;
    "stop")
        stop_parser
        ;;
    "restart")
        restart_parser
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "force-parse")
        force_parse
        ;;
    "stats")
        show_stats
        ;;
    "help"|*)
        show_help
        ;;
esac