#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Perfume Consultant Bot v2.0 - Основной файл запуска

Единая система парфюмерного консультанта включающая:
- Автоматический парсинг и нормализацию данных
- Telegram бот с ИИ консультантом  
- Планировщик автоматических задач
- Систему кэширования и логирования
"""

import asyncio
import sys
import signal
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from perfume_bot import PerfumeApplication, setup_logging, get_logger

# Настраиваем логирование
setup_logging()
logger = get_logger("perfume_bot.main")

class GracefulShutdown:
    """Обработчик graceful shutdown"""
    
    def __init__(self, app: PerfumeApplication):
        self.app = app
        self.shutdown_event = asyncio.Event()
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов завершения"""
        logger.info(f"📶 Получен сигнал {signum}, начинаю graceful shutdown...")
        self.shutdown_event.set()

async def main():
    """Основная функция запуска"""
    logger.info("🚀 Запуск Perfume Consultant Bot v2.0")
    logger.info("=" * 60)
    
    # Создаем приложение
    app = PerfumeApplication()
    
    # Настраиваем graceful shutdown
    shutdown_handler = GracefulShutdown(app)
    signal.signal(signal.SIGINT, shutdown_handler.signal_handler)
    signal.signal(signal.SIGTERM, shutdown_handler.signal_handler)
    
    try:
        # Инициализируем приложение
        await app.initialize()
        
        # Проверяем, нужно ли обновить данные при старте
        logger.info("🔍 Проверка актуальности данных...")
        if not await app.data_manager.has_data():
            logger.info("📥 Данные отсутствуют, выполняю первичную загрузку...")
            success = await app.parse_and_update_data(force=True)
            if not success:
                logger.error("❌ Не удалось загрузить данные, завершаю работу")
                return 1
        
        # Показываем статус
        status = await app.get_status()
        logger.info("📊 Статус системы:")
        logger.info(f"   • Парфюмов в базе: {status['data'].get('total_perfumes', 0)}")
        logger.info(f"   • Брендов: {status['data'].get('total_brands', 0)}")
        logger.info(f"   • Фабрик: {status['data'].get('total_factories', 0)}")
        logger.info(f"   • Окружение: {status['config']['environment']}")
        
        logger.info("🤖 Все системы готовы, запускаю бота...")
        logger.info("=" * 60)
        
        # Запускаем бота и ждем сигнала завершения
        bot_task = asyncio.create_task(app.run_bot())
        shutdown_task = asyncio.create_task(shutdown_handler.shutdown_event.wait())
        
        # Ждем завершения одной из задач
        done, pending = await asyncio.wait(
            [bot_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Отменяем оставшиеся задачи
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Приложение завершено успешно")
        return 0
        
    except KeyboardInterrupt:
        logger.info("⏹️ Получен Ctrl+C, завершаю работу...")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.exception("Детали ошибки:")
        return 1

def run_data_update():
    """Запуск только обновления данных (без бота)"""
    logger.info("🔄 Запуск обновления данных...")
    
    async def update_only():
        app = PerfumeApplication()
        await app.initialize()
        success = await app.parse_and_update_data(force=True)
        return 0 if success else 1
    
    return asyncio.run(update_only())

def show_status():
    """Показ статуса системы"""
    logger.info("📊 Получение статуса системы...")
    
    async def status_only():
        app = PerfumeApplication()
        await app.initialize()
        status = await app.get_status()
        
        print("\n🤖 Perfume Consultant Bot - Статус системы")
        print("=" * 50)
        print(f"Версия: {status['application']['version']}")
        print(f"Окружение: {status['config']['environment']}")
        print(f"Парфюмов в базе: {status['data'].get('total_perfumes', 0)}")
        print(f"Брендов: {status['data'].get('total_brands', 0)}")
        print(f"Фабрик: {status['data'].get('total_factories', 0)}")
        print(f"Интервал обновления: {status['config']['update_interval']} часов")
        print("=" * 50)
        
        return 0
    
    return asyncio.run(status_only())

if __name__ == "__main__":
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "update":
            sys.exit(run_data_update())
        elif command == "status":
            sys.exit(show_status())
        elif command == "help":
            print("\n🤖 Perfume Consultant Bot v2.0")
            print("=" * 40)
            print("Использование:")
            print("  python run_perfume_bot.py         - Запуск бота")
            print("  python run_perfume_bot.py update  - Обновление данных")
            print("  python run_perfume_bot.py status  - Статус системы")
            print("  python run_perfume_bot.py help    - Эта справка")
            print("=" * 40)
            sys.exit(0)
        else:
            print(f"❌ Неизвестная команда: {command}")
            print("Используйте 'help' для списка команд")
            sys.exit(1)
    
    # Запуск основного приложения
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("⏹️ Завершение по Ctrl+C")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка запуска: {e}")
        sys.exit(1)