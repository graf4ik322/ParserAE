#!/bin/bash

# Perfume Consultant Bot v2.0 - Docker Control Script
set -e

COMPOSE_FILE="docker-compose.v2.yml"
ENV_FILE=".env.docker"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Проверка наличия файлов
check_files() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Файл $COMPOSE_FILE не найден!"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        warning "Файл $ENV_FILE не найден, создаю из примера..."
        if [ -f ".env.docker" ]; then
            cp .env.docker "$ENV_FILE"
        else
            error "Файл .env.docker не найден!"
            exit 1
        fi
    fi
}

# Показать помощь
show_help() {
    echo "🤖 Perfume Consultant Bot v2.0 - Docker Control"
    echo "================================================"
    echo
    echo "Использование: $0 [команда] [опции]"
    echo
    echo "Команды:"
    echo "  start [profile]     - Запуск сервисов"
    echo "  stop               - Остановка сервисов"
    echo "  restart [profile]  - Перезапуск сервисов"
    echo "  status             - Статус сервисов"
    echo "  logs [service]     - Просмотр логов"
    echo "  update             - Только обновление данных"
    echo "  build              - Пересборка образов"
    echo "  clean              - Очистка (остановка + удаление)"
    echo "  shell              - Подключение к контейнеру"
    echo
    echo "Профили:"
    echo "  basic              - Только основной бот (по умолчанию)"
    echo "  redis              - Бот + Redis кэш"
    echo "  postgres           - Бот + PostgreSQL"
    echo "  monitoring         - Бот + мониторинг (Prometheus + Grafana)"
    echo "  full               - Все сервисы"
    echo
    echo "Примеры:"
    echo "  $0 start           - Базовый запуск"
    echo "  $0 start redis     - Запуск с Redis"
    echo "  $0 start full      - Полная конфигурация"
    echo "  $0 logs perfume-bot - Логи основного сервиса"
    echo "  $0 update          - Обновление данных"
}

# Получить профили для команды
get_profiles() {
    case "${1:-basic}" in
        "basic")
            echo ""
            ;;
        "redis")
            echo "--profile with-redis"
            ;;
        "postgres")
            echo "--profile with-postgres"
            ;;
        "monitoring")
            echo "--profile monitoring"
            ;;
        "full")
            echo "--profile with-redis --profile with-postgres --profile monitoring"
            ;;
        *)
            error "Неизвестный профиль: $1"
            echo "Доступные профили: basic, redis, postgres, monitoring, full"
            exit 1
            ;;
    esac
}

# Запуск сервисов
start_services() {
    local profile="${1:-basic}"
    local profiles=$(get_profiles "$profile")
    
    log "🚀 Запуск Perfume Bot v2.0 (профиль: $profile)"
    
    check_files
    
    # Создаем необходимые директории
    mkdir -p perfume_bot/data/{raw,processed,cache}
    mkdir -p logs
    
    info "Запуск сервисов..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" $profiles up -d
    
    log "✅ Сервисы запущены!"
    
    # Показываем статус
    sleep 3
    show_status
}

# Остановка сервисов
stop_services() {
    log "⏹️ Остановка сервисов..."
    docker-compose -f "$COMPOSE_FILE" down
    log "✅ Сервисы остановлены"
}

# Перезапуск сервисов
restart_services() {
    local profile="${1:-basic}"
    log "🔄 Перезапуск сервисов..."
    stop_services
    sleep 2
    start_services "$profile"
}

# Статус сервисов
show_status() {
    log "📊 Статус сервисов:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo
    info "Доступные эндпоинты:"
    
    # Проверяем какие сервисы запущены
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "perfume-bot.*Up"; then
        echo "  🤖 Telegram Bot: активен"
        echo "  📊 Статус бота: docker exec perfume-bot-v2 python run_perfume_bot.py status"
    fi
    
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "grafana.*Up"; then
        echo "  📈 Grafana: http://localhost:3000 (admin/admin)"
    fi
    
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "prometheus.*Up"; then
        echo "  🔍 Prometheus: http://localhost:9090"
    fi
}

# Просмотр логов
show_logs() {
    local service="${1:-perfume-bot}"
    log "📋 Логи сервиса: $service"
    docker-compose -f "$COMPOSE_FILE" logs -f "$service"
}

# Обновление данных
update_data() {
    log "🔄 Обновление данных парфюмов..."
    
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "perfume-bot.*Up"; then
        error "Контейнер perfume-bot не запущен!"
        exit 1
    fi
    
    docker exec perfume-bot-v2 python run_perfume_bot.py update
    log "✅ Обновление данных завершено"
}

# Пересборка образов
build_images() {
    log "🔨 Пересборка образов..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    log "✅ Образы пересобраны"
}

# Очистка
clean_all() {
    log "🧹 Полная очистка..."
    
    warning "Это удалит все контейнеры, сети и volumes!"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
        docker system prune -f
        log "✅ Очистка завершена"
    else
        info "Очистка отменена"
    fi
}

# Подключение к контейнеру
connect_shell() {
    local service="${1:-perfume-bot}"
    log "🐚 Подключение к контейнеру: $service"
    
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "$service.*Up"; then
        error "Контейнер $service не запущен!"
        exit 1
    fi
    
    docker exec -it "perfume-bot-v2" /bin/bash
}

# Главная функция
main() {
    case "${1:-help}" in
        "start")
            start_services "$2"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services "$2"
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "update")
            update_data
            ;;
        "build")
            build_images
            ;;
        "clean")
            clean_all
            ;;
        "shell")
            connect_shell "$2"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            error "Неизвестная команда: $1"
            echo "Используйте '$0 help' для справки"
            exit 1
            ;;
    esac
}

# Запуск
main "$@"