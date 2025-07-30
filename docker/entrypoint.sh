#!/bin/bash
set -e

echo "🐳 Perfume Consultant Bot v2.0 - Docker Entrypoint"
echo "=================================================="

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверяем переменные окружения
check_env() {
    log "🔍 Проверка переменных окружения..."
    
    if [ -z "$BOT_TOKEN" ]; then
        log "❌ ERROR: BOT_TOKEN не установлен"
        exit 1
    fi
    
    if [ -z "$OPENROUTER_API_KEY" ]; then
        log "❌ ERROR: OPENROUTER_API_KEY не установлен"
        exit 1
    fi
    
    if [ -z "$ADMIN_USER_ID" ]; then
        log "❌ ERROR: ADMIN_USER_ID не установлен"
        exit 1
    fi
    
    log "✅ Основные переменные окружения проверены"
}

# Инициализация директорий
init_directories() {
    log "📁 Инициализация директорий..."
    
    # Создаем необходимые директории если они не существуют
    mkdir -p /app/perfume_bot/data/raw
    mkdir -p /app/perfume_bot/data/processed
    mkdir -p /app/perfume_bot/data/cache
    mkdir -p /app/logs
    
    log "✅ Директории инициализированы"
}

# Проверка зависимостей Python
check_python_deps() {
    log "🐍 Проверка Python зависимостей..."
    
    python -c "
import sys
try:
    from perfume_bot.core.config import config
    print('✅ Конфигурация загружена успешно')
except Exception as e:
    print(f'❌ Ошибка загрузки конфигурации: {e}')
    sys.exit(1)
"
}

# Проверка доступности API
check_api_connectivity() {
    log "🌐 Проверка доступности API..."
    
    # Проверяем доступность OpenRouter API
    if command -v curl >/dev/null 2>&1; then
        if curl -s --connect-timeout 10 https://openrouter.ai/api/v1/auth/key \
           -H "Authorization: Bearer $OPENROUTER_API_KEY" >/dev/null; then
            log "✅ OpenRouter API доступен"
        else
            log "⚠️ WARNING: OpenRouter API недоступен или ключ неверный"
        fi
    else
        log "⚠️ WARNING: curl недоступен для проверки API"
    fi
}

# Инициализация данных при первом запуске
init_data_if_needed() {
    log "📊 Проверка наличия данных..."
    
    # Проверяем, есть ли обработанные данные
    if [ ! -f "/app/perfume_bot/data/processed/names_only.json" ]; then
        log "📥 Данные отсутствуют, запускаю первичную загрузку..."
        
        # Запускаем обновление данных в фоне
        python run_perfume_bot.py update &
        update_pid=$!
        
        # Ждем завершения с таймаутом
        timeout=1800  # 30 минут
        elapsed=0
        
        while kill -0 $update_pid 2>/dev/null && [ $elapsed -lt $timeout ]; do
            sleep 30
            elapsed=$((elapsed + 30))
            log "⏳ Обновление данных... ($elapsed/$timeout сек)"
        done
        
        if kill -0 $update_pid 2>/dev/null; then
            log "⏰ Таймаут обновления данных, завершаю процесс"
            kill $update_pid
            wait $update_pid 2>/dev/null || true
        else
            wait $update_pid
            if [ $? -eq 0 ]; then
                log "✅ Первичная загрузка данных завершена"
            else
                log "❌ Ошибка при первичной загрузке данных"
            fi
        fi
    else
        log "✅ Данные уже присутствуют"
    fi
}

# Главная функция
main() {
    log "🚀 Запуск Perfume Consultant Bot v2.0..."
    
    # Выполняем проверки
    check_env
    init_directories
    check_python_deps
    check_api_connectivity
    
    # Обрабатываем команды
    case "${1:-}" in
        "update")
            log "🔄 Режим обновления данных"
            exec python run_perfume_bot.py update
            ;;
        "status")
            log "📊 Режим проверки статуса"
            exec python run_perfume_bot.py status
            ;;
        "help")
            log "📖 Показ справки"
            exec python run_perfume_bot.py help
            ;;
        "")
            # Основной режим запуска
            log "🤖 Основной режим запуска бота"
            
            # Инициализируем данные если нужно
            init_data_if_needed
            
            log "🎯 Запускаю основное приложение..."
            exec python run_perfume_bot.py
            ;;
        *)
            log "❌ Неизвестная команда: $1"
            log "📖 Доступные команды: update, status, help"
            exit 1
            ;;
    esac
}

# Обработка сигналов для graceful shutdown
cleanup() {
    log "📶 Получен сигнал завершения, выполняю graceful shutdown..."
    if [ ! -z "$main_pid" ]; then
        kill -TERM "$main_pid" 2>/dev/null || true
        wait "$main_pid" 2>/dev/null || true
    fi
    log "✅ Graceful shutdown завершен"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Запускаем главную функцию
main "$@" &
main_pid=$!
wait $main_pid