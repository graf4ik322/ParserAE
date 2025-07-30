#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import schedule
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from .config import config
from .logger import get_logger, setup_logging
from ..parsers.scrapers.perfume_scraper import PerfumeScraper
from ..parsers.normalizers.data_normalizer import PerfumeDataNormalizer
from ..data.data_manager import DataManager
from ..bot.telegram_bot import TelegramBot

logger = get_logger("perfume_bot")

class PerfumeApplication:
    """Главное приложение парфюмерного консультанта"""
    
    def __init__(self):
        # Инициализируем логирование
        setup_logging()
        logger.info("🚀 Инициализация Perfume Consultant Bot v2.0")
        
        # Основные компоненты
        self.data_manager = DataManager()
        self.telegram_bot = None
        self.is_running = False
        
        # Планировщик задач
        self.scheduler_running = False
        
        logger.info("✅ Приложение инициализировано")
    
    async def initialize(self):
        """Асинхронная инициализация компонентов"""
        logger.info("🔧 Инициализация компонентов...")
        
        # Инициализируем менеджер данных
        await self.data_manager.initialize()
        
        # Создаем Telegram бота
        self.telegram_bot = TelegramBot(self.data_manager)
        await self.telegram_bot.initialize()
        
        # Настраиваем планировщик
        self._setup_scheduler()
        
        logger.info("✅ Все компоненты инициализированы")
    
    def _setup_scheduler(self):
        """Настраивает планировщик автоматических задач"""
        # Автоматическое обновление данных каждые 24 часа
        schedule.every(config.data.update_interval_hours).hours.do(self._scheduled_data_update)
        
        # Очистка кэша каждые 7 дней
        schedule.every(config.data.cache_expiry_days).days.do(self._scheduled_cache_cleanup)
        
        # Ротация логов каждую неделю
        schedule.every().week.do(self._scheduled_log_rotation)
        
        logger.info("📅 Планировщик задач настроен")
    
    async def run_bot(self):
        """Запускает Telegram бота"""
        if not self.telegram_bot:
            raise RuntimeError("Бот не инициализирован")
        
        logger.info("🤖 Запуск Telegram бота...")
        self.is_running = True
        
        # Запускаем планировщик в отдельной задаче
        scheduler_task = asyncio.create_task(self._run_scheduler())
        
        try:
            # Запускаем бота
            await self.telegram_bot.run()
        except KeyboardInterrupt:
            logger.info("⏹️ Получен сигнал остановки")
        finally:
            self.is_running = False
            scheduler_task.cancel()
            await self._cleanup()
    
    async def _run_scheduler(self):
        """Запускает планировщик в асинхронном режиме"""
        self.scheduler_running = True
        logger.info("⏰ Планировщик задач запущен")
        
        while self.is_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут при ошибке
        
        self.scheduler_running = False
        logger.info("⏰ Планировщик задач остановлен")
    
    async def parse_and_update_data(self, force: bool = False) -> bool:
        """Парсит и обновляет данные парфюмов"""
        logger.info("🔄 Начинаю обновление данных парфюмов...")
        
        try:
            # Проверяем, нужно ли обновление
            if not force and not self._need_data_update():
                logger.info("ℹ️ Данные актуальны, обновление не требуется")
                return True
            
            # Парсим данные
            async with PerfumeScraper() as scraper:
                logger.info("🕷️ Запуск парсера...")
                perfumes = await scraper.scrape_all_perfumes()
                
                if not perfumes:
                    logger.error("❌ Парсер не получил данных")
                    return False
                
                # Сохраняем сырые данные
                raw_file = scraper.save_to_json()
                logger.info(f"💾 Сырые данные сохранены: {raw_file}")
            
            # Нормализуем данные
            logger.info("🔧 Нормализация данных...")
            normalizer = PerfumeDataNormalizer()
            normalizer.load_raw_data(raw_file)
            normalized_data = normalizer.normalize_all_data()
            
            # Сохраняем нормализованные данные
            normalized_file = normalizer.save_normalized_data(normalized_data)
            separate_files = normalizer.save_separate_files(normalized_data)
            
            logger.info(f"💾 Нормализованные данные сохранены: {normalized_file}")
            logger.info(f"📁 Создано {len(separate_files)} отдельных файлов")
            
            # Обновляем данные в менеджере
            await self.data_manager.reload_data()
            
            logger.info("✅ Обновление данных завершено успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении данных: {e}")
            return False
    
    def _need_data_update(self) -> bool:
        """Проверяет, нужно ли обновление данных"""
        try:
            # Проверяем время последнего обновления
            last_update_file = config.get_cache_file_path("last_update.txt")
            
            if not last_update_file.exists():
                return True
            
            with open(last_update_file, 'r') as f:
                last_update_str = f.read().strip()
                last_update = datetime.fromisoformat(last_update_str)
            
            # Проверяем, прошло ли достаточно времени
            time_since_update = datetime.now() - last_update
            update_interval = timedelta(hours=config.data.update_interval_hours)
            
            return time_since_update >= update_interval
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки времени обновления: {e}")
            return True
    
    def _update_last_update_time(self):
        """Обновляет время последнего обновления"""
        try:
            last_update_file = config.get_cache_file_path("last_update.txt")
            with open(last_update_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logger.error(f"❌ Ошибка записи времени обновления: {e}")
    
    def _scheduled_data_update(self):
        """Плановое обновление данных"""
        logger.info("📅 Плановое обновление данных...")
        
        # Запускаем обновление в новом event loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self.parse_and_update_data())
            
            if success:
                self._update_last_update_time()
                logger.info("✅ Плановое обновление завершено")
            else:
                logger.error("❌ Плановое обновление не удалось")
        except Exception as e:
            logger.error(f"❌ Ошибка планового обновления: {e}")
        finally:
            loop.close()
    
    def _scheduled_cache_cleanup(self):
        """Плановая очистка кэша"""
        logger.info("📅 Плановая очистка кэша...")
        
        try:
            cache_dir = config.data.cache_dir
            current_time = datetime.now()
            expiry_time = timedelta(days=config.data.cache_expiry_days)
            
            cleaned_files = 0
            for cache_file in cache_dir.glob("*"):
                if cache_file.is_file():
                    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if current_time - file_time > expiry_time:
                        cache_file.unlink()
                        cleaned_files += 1
            
            logger.info(f"✅ Очищено {cleaned_files} устаревших файлов кэша")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}")
    
    def _scheduled_log_rotation(self):
        """Плановая ротация логов"""
        logger.info("📅 Плановая ротация логов...")
        
        try:
            # Логи ротируются автоматически через RotatingFileHandler
            # Здесь можем добавить дополнительную логику если нужно
            logger.info("✅ Ротация логов выполнена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка ротации логов: {e}")
    
    async def _cleanup(self):
        """Очистка ресурсов при завершении"""
        logger.info("🧹 Очистка ресурсов...")
        
        try:
            if self.telegram_bot:
                await self.telegram_bot.cleanup()
            
            if self.data_manager:
                await self.data_manager.cleanup()
            
            logger.info("✅ Очистка завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Возвращает статус приложения"""
        try:
            data_stats = await self.data_manager.get_statistics()
            
            return {
                "application": {
                    "version": "2.0.0",
                    "running": self.is_running,
                    "scheduler_running": self.scheduler_running,
                    "uptime": "N/A"  # TODO: добавить отслеживание времени работы
                },
                "data": data_stats,
                "bot": {
                    "active": self.telegram_bot is not None,
                    "users_count": len(self.telegram_bot.user_sessions) if self.telegram_bot else 0
                },
                "config": {
                    "environment": "production" if config.is_production else "development",
                    "update_interval": config.data.update_interval_hours,
                    "cache_expiry": config.data.cache_expiry_days
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            return {"error": str(e)}
    
    # Управляющие команды
    
    async def force_data_update(self) -> bool:
        """Принудительное обновление данных"""
        logger.info("🔄 Принудительное обновление данных...")
        success = await self.parse_and_update_data(force=True)
        if success:
            self._update_last_update_time()
        return success
    
    async def clear_cache(self) -> bool:
        """Очистка всего кэша"""
        logger.info("🧹 Очистка кэша...")
        try:
            cache_dir = config.data.cache_dir
            for cache_file in cache_dir.glob("*"):
                if cache_file.is_file():
                    cache_file.unlink()
            
            logger.info("✅ Кэш очищен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}")
            return False
    
    async def restart_bot(self) -> bool:
        """Перезапуск бота"""
        logger.info("🔄 Перезапуск бота...")
        try:
            if self.telegram_bot:
                await self.telegram_bot.stop()
                await self.telegram_bot.start()
            
            logger.info("✅ Бот перезапущен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка перезапуска бота: {e}")
            return False

# Глобальный экземпляр приложения
app = PerfumeApplication()