#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import schedule
import time
import logging
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
import subprocess
import asyncio
import aiohttp
from pathlib import Path

# Импорты локальных модулей
from complete_parser_with_details import CompleteParfumeParser
from data_normalizer import PerfumeDataNormalizer

# Настройка логирования
import os
from pathlib import Path

# Создаем директорию для логов если не существует
log_dir = Path('/app/logs')
log_dir.mkdir(exist_ok=True)

# Используем файл в директории logs вместо корневой
log_file = log_dir / 'auto_parser.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoParserService:
    """Автоматизированный сервис парсинга и нормализации парфюмерных данных"""
    
    def __init__(self):
        self.last_check_file = "last_check.json"
        self.data_changed = False
        self.telegram_bot_token = os.getenv('BOT_TOKEN')
        self.admin_user_id = os.getenv('ADMIN_USER_ID')
        
        # Файлы для мониторинга
        self.catalog_file = "full_perfumes_catalog_complete.json"
        self.normalized_files = [
            "names_only.json",
            "brand_name.json", 
            "name_factory.json",
            "brand_name_factory.json",
            "full_data_compact.json",
            "factory_analysis.json"
        ]
        
        logger.info("🤖 AutoParserService инициализирован")
    
    def get_file_hash(self, filepath: str) -> Optional[str]:
        """Получает хеш файла для отслеживания изменений"""
        try:
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"Ошибка получения хеша {filepath}: {e}")
            return None
    
    def load_last_check_data(self) -> Dict[str, Any]:
        """Загружает данные последней проверки"""
        try:
            if os.path.exists(self.last_check_file):
                with open(self.last_check_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки данных последней проверки: {e}")
        
        return {
            "last_parse_time": None,
            "last_catalog_hash": None,
            "last_perfume_count": 0,
            "last_factory_count": 0
        }
    
    def save_last_check_data(self, data: Dict[str, Any]):
        """Сохраняет данные последней проверки"""
        try:
            with open(self.last_check_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных проверки: {e}")
    
    async def send_telegram_notification(self, message: str):
        """Отправляет уведомление администратору в Telegram"""
        if not self.telegram_bot_token or not self.admin_user_id:
            logger.warning("Telegram токен или admin ID не настроены")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": self.admin_user_id,
                "text": f"🤖 **AutoParser Update**\n\n{message}",
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info("✅ Уведомление отправлено администратору")
                    else:
                        logger.error(f"❌ Ошибка отправки уведомления: {response.status}")
        
        except Exception as e:
            logger.error(f"Ошибка отправки Telegram уведомления: {e}")
    
    def run_parser(self) -> bool:
        """Запускает парсер и возвращает True если данные изменились"""
        try:
            logger.info("🔄 Запуск парсера...")
            
            # Получаем текущий хеш каталога
            old_hash = self.get_file_hash(self.catalog_file)
            
            # Запускаем парсер
            parser = CompleteParfumeParser(max_workers=2)
            parser.run_complete_parsing()
            
            # Проверяем изменения
            new_hash = self.get_file_hash(self.catalog_file)
            
            if old_hash != new_hash:
                logger.info("✅ Обнаружены изменения в каталоге")
                return True
            else:
                logger.info("ℹ️ Изменений в каталоге не обнаружено")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            return False
    
    def run_normalizer(self) -> bool:
        """Запускает нормализатор данных"""
        try:
            logger.info("🔄 Запуск нормализации данных...")
            
            # Инициализируем нормализатор
            normalizer = PerfumeDataNormalizer(self.catalog_file)
            
            # Создаем все нормализованные файлы
            normalizer.create_all_normalized_files()
            
            logger.info("✅ Нормализация данных завершена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка нормализации: {e}")
            return False
    
    def restart_bot_service(self):
        """Перезапускает бот-сервис для обновления данных"""
        try:
            logger.info("🔄 Перезапуск бот-сервиса...")
            
            # Если используется Docker Compose
            if os.path.exists('docker-compose.yml'):
                subprocess.run(['docker-compose', 'restart', 'perfume-bot'], 
                             check=True, capture_output=True)
                logger.info("✅ Бот-сервис перезапущен через Docker Compose")
            else:
                logger.warning("⚠️ docker-compose.yml не найден, ручной перезапуск требуется")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Ошибка перезапуска сервиса: {e}")
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при перезапуске: {e}")
    
    def check_and_update(self):
        """Основная функция проверки и обновления данных"""
        logger.info("🔍 Начинаем проверку обновлений...")
        
        # Загружаем данные последней проверки
        last_check = self.load_last_check_data()
        
        # Запускаем парсер
        data_changed = self.run_parser()
        
        if data_changed:
            logger.info("📊 Данные изменились, запускаем нормализацию...")
            
            # Нормализуем данные
            if self.run_normalizer():
                # Получаем статистику
                stats = self.get_catalog_stats()
                
                # Сохраняем данные проверки
                current_check = {
                    "last_parse_time": datetime.now().isoformat(),
                    "last_catalog_hash": self.get_file_hash(self.catalog_file),
                    "last_perfume_count": stats['perfume_count'],
                    "last_factory_count": stats['factory_count']
                }
                self.save_last_check_data(current_check)
                
                # Отправляем уведомление
                notification = f"""
📊 **Обновление каталога парфюмов**

🔄 Время обновления: {datetime.now().strftime('%d.%m.%Y %H:%M')}
🧴 Всего ароматов: {stats['perfume_count']} (было: {last_check.get('last_perfume_count', 0)})
🏭 Всего фабрик: {stats['factory_count']} (было: {last_check.get('last_factory_count', 0)})
📈 Изменение: +{stats['perfume_count'] - last_check.get('last_perfume_count', 0)} ароматов

✅ Все файлы обновлены и готовы к использованию
🤖 Бот-сервис будет перезапущен для загрузки новых данных
"""
                
                asyncio.run(self.send_telegram_notification(notification))
                
                # Перезапускаем бот для загрузки новых данных
                self.restart_bot_service()
                
                logger.info("✅ Полное обновление завершено успешно")
            else:
                logger.error("❌ Ошибка нормализации данных")
        else:
            logger.info("ℹ️ Обновления не требуются")
    
    def get_catalog_stats(self) -> Dict[str, int]:
        """Получает статистику каталога"""
        try:
            with open(self.catalog_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            perfume_count = len(data.get('perfumes', []))
            
            # Подсчитываем уникальные фабрики
            factories = set()
            for perfume in data.get('perfumes', []):
                factory = perfume.get('factory', '').strip()
                if factory:
                    factories.add(factory)
            
            return {
                'perfume_count': perfume_count,
                'factory_count': len(factories)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {'perfume_count': 0, 'factory_count': 0}
    
    def run_scheduler(self):
        """Запускает планировщик задач"""
        logger.info("⏰ Запуск планировщика автообновлений...")
        
        # Ежедневная проверка в 06:00
        schedule.every().day.at("06:00").do(self.check_and_update)
        
        # Проверка каждые 6 часов
        schedule.every(6).hours.do(self.check_and_update)
        
        # Еженедельная принудительная проверка по воскресеньям в 03:00
        schedule.every().sunday.at("03:00").do(self.force_full_update)
        
        logger.info("📅 Расписание настроено:")
        logger.info("   • Ежедневно в 06:00")
        logger.info("   • Каждые 6 часов")
        logger.info("   • Еженедельно по воскресеньям в 03:00 (полное обновление)")
        
        # Первоначальная проверка при запуске
        logger.info("🚀 Выполняем первоначальную проверку...")
        self.check_and_update()
        
        # Основной цикл планировщика
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
            except KeyboardInterrupt:
                logger.info("🛑 Получен сигнал остановки")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике: {e}")
                time.sleep(300)  # Ждем 5 минут при ошибке
    
    def force_full_update(self):
        """Принудительное полное обновление"""
        logger.info("🔄 Принудительное полное обновление...")
        
        # Удаляем файл последней проверки для принудительного обновления
        if os.path.exists(self.last_check_file):
            os.remove(self.last_check_file)
        
        self.check_and_update()

def main():
    """Главная функция запуска сервиса"""
    logger.info("🚀 Запуск AutoParserService...")
    
    service = AutoParserService()
    
    try:
        service.run_scheduler()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка сервиса: {e}")
        # Отправляем уведомление об ошибке
        error_message = f"🚨 **Критическая ошибка AutoParser**\n\n```\n{str(e)}\n```"
        asyncio.run(service.send_telegram_notification(error_message))

if __name__ == "__main__":
    main()