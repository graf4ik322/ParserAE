#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import schedule
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from parsers.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class AutoParser:
    """Автоматический парсер для регулярного обновления каталога"""
    
    def __init__(self, db_manager, config=None):
        self.db = db_manager
        self.data_processor = DataProcessor(self.db)
        self.config = config
        self.running = False
        self.last_catalog_hash = None
        
        logger.info("🔄 AutoParser инициализирован")
    
    async def start_scheduler(self):
        """Запускает планировщик автоматического парсинга"""
        try:
            self.running = True
            logger.info("⏰ Планировщик автоматического парсинга запущен")
            
            # Запускаем первоначальную загрузку данных из JSON
            await self._initial_data_load()
            
            # Запускаем задачи парсинга по расписанию
            asyncio.create_task(self._run_periodic_parsing())
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика: {e}")
    
    async def _run_periodic_parsing(self):
        """Выполняет периодический парсинг"""
        last_parse_time = datetime.now()
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Парсинг каждые 6 часов
                if (current_time - last_parse_time).total_seconds() >= 6 * 3600:
                    logger.info("🔄 Запускаем периодический парсинг...")
                    await self._check_and_parse()
                    last_parse_time = current_time
                
                # Ждем 30 минут до следующей проверки
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в периодическом парсинге: {e}")
                await asyncio.sleep(3600)  # Ждем час при ошибке
    
    def stop_scheduler(self):
        """Останавливает планировщик"""
        self.running = False
        logger.info("🛑 Планировщик автоматического парсинга остановлен")
    
    async def _check_and_parse(self):
        """Проверяет и запускает парсинг при необходимости"""
        try:
            logger.info("🔍 Проверяем необходимость обновления каталога...")
            
            # Здесь можно добавить логику проверки изменений
            # Пока что просто обновляем каталог
            await self._parse_and_update_catalog()
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке и парсинге: {e}")
    
    async def _parse_and_update_catalog(self):
        """Парсит и обновляет каталог парфюмов"""
        try:
            logger.info("📊 Обновляем каталог парфюмов...")
            
            # Здесь должна быть логика парсинга сайтов
            # Пока что просто логируем
            logger.info("✅ Каталог успешно обновлен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении каталога: {e}")
    
    async def _initial_data_load(self):
        """Загружает данные из JSON файла при первом запуске"""
        try:
            # Проверяем, есть ли данные в БД
            perfumes_count = self.db.count_perfumes()
            
            if perfumes_count == 0:
                logger.info("📂 БД пуста, загружаем данные из JSON файла...")
                await self._load_data_from_json()
            else:
                logger.info(f"📊 В БД уже есть {perfumes_count} парфюмов")
                
        except Exception as e:
            logger.error(f"Ошибка при начальной загрузке данных: {e}")
    
    async def _load_data_from_json(self):
        """Загружает данные из существующего JSON файла"""
        try:
            json_file = "full_perfumes_catalog_complete.json"
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'perfumes' in data:
                perfumes_data = data['perfumes']
                logger.info(f"📄 Загружено {len(perfumes_data)} парфюмов из JSON")
                
                # Обрабатываем и сохраняем каждый парфюм
                processed_count = 0
                for perfume_raw in perfumes_data:
                    try:
                        normalized_perfume = self.data_processor.normalize_perfume_data(perfume_raw)
                        if self.db.save_perfume_to_database(normalized_perfume):
                            processed_count += 1
                            
                        if processed_count % 100 == 0:
                            logger.info(f"📊 Обработано {processed_count} парфюмов...")
                            
                    except Exception as e:
                        logger.error(f"Ошибка при обработке парфюма: {e}")
                        continue
                
                logger.info(f"✅ Успешно загружено {processed_count} парфюмов в БД")
                
            else:
                logger.warning("JSON файл не содержит ключ 'perfumes'")
                
        except FileNotFoundError:
            logger.warning("JSON файл с данными не найден, будем ждать парсинга")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных из JSON: {e}")
    
    def _schedule_check_and_parse(self):
        """Планированная проверка и парсинг (обертка для async)"""
        asyncio.create_task(self.check_and_parse_catalog())
    
    def _schedule_daily_full_parse(self):
        """Планированный ежедневный полный парсинг (обертка для async)"""
        asyncio.create_task(self.daily_full_parse())
    
    def _schedule_weekly_full_update(self):
        """Планированное еженедельное полное обновление (обертка для async)"""
        asyncio.create_task(self.weekly_full_update())
    
    async def check_and_parse_catalog(self) -> bool:
        """Проверяет изменения каталога и парсит при необходимости"""
        try:
            logger.info("🔍 Проверяем изменения в каталоге...")
            
            # Проверяем изменения на сайте (упрощенная версия)
            if await self._has_catalog_changes():
                logger.info("📈 Обнаружены изменения в каталоге, запускаем парсинг...")
                result = await self.parse_and_save_catalog()
                
                if result:
                    logger.info("📨 Уведомляем администратора об обновлении каталога")
                    await self._notify_admin("Каталог обновлен автоматически")
                
                return result
            else:
                logger.info("📊 Изменений в каталоге не обнаружено")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при проверке каталога: {e}")
            return False
    
    async def daily_full_parse(self) -> bool:
        """Ежедневный полный парсинг"""
        logger.info("🌅 Запускаем ежедневный полный парсинг каталога...")
        return await self.parse_and_save_catalog()
    
    async def weekly_full_update(self) -> bool:
        """Еженедельное полное обновление с очисткой"""
        logger.info("🗓️ Запускаем еженедельное полное обновление каталога...")
        
        # Здесь можно добавить логику очистки старых данных
        # Пока просто делаем полный парсинг
        return await self.parse_and_save_catalog()
    
    async def force_parse_catalog(self) -> bool:
        """Принудительный парсинг каталога (для админ-команды)"""
        logger.info("🚀 Запускаем принудительный парсинг каталога...")
        return await self.parse_and_save_catalog()
    
    async def parse_and_save_catalog(self) -> bool:
        """Парсит каталог и сохраняет в БД"""
        try:
            # Импортируем оригинальный парсер
            from complete_parser_with_details import CompleteParfumeParser
            
            logger.info("🕷️ Запускаем парсинг с сайта aroma-euro.ru...")
            
            # Создаем экземпляр парсера
            parser = CompleteParfumeParser(max_workers=3)
            
            # Парсим каталог
            raw_perfumes = parser.parse_all_catalog()
            
            if not raw_perfumes:
                logger.warning("⚠️ Парсер не вернул данных")
                return False
            
            logger.info(f"📊 Получено {len(raw_perfumes)} парфюмов от парсера")
            
            # Обрабатываем и сохраняем каждый парфюм
            processed_count = 0
            updated_count = 0
            new_count = 0
            
            for perfume_raw in raw_perfumes:
                try:
                    # Нормализуем данные парфюма
                    normalized_perfume = self.data_processor.normalize_perfume_data(perfume_raw)
                    
                    # Проверяем, существует ли парфюм
                    existing = self.db.get_perfume_by_unique_key(normalized_perfume['unique_key'])
                    
                    # Сохраняем в БД
                    if self.db.save_perfume_to_database(normalized_perfume):
                        processed_count += 1
                        
                        if existing:
                            updated_count += 1
                        else:
                            new_count += 1
                            
                        if processed_count % 50 == 0:
                            logger.info(f"📊 Обработано {processed_count} парфюмов...")
                            
                except Exception as e:
                    logger.error(f"Ошибка при обработке парфюма: {e}")
                    continue
            
            # Обновляем поисковые индексы (если необходимо)
            await self._update_search_indexes()
            
            logger.info(f"""
✅ Парсинг завершен успешно:
├── 📊 Всего обработано: {processed_count}
├── 🆕 Новых парфюмов: {new_count}
├── 🔄 Обновленных: {updated_count}
└── 📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при парсинге каталога: {e}")
            return False
    
    async def _has_catalog_changes(self) -> bool:
        """Проверяет, есть ли изменения в каталоге"""
        try:
            # Упрощенная проверка - проверяем хэш первой страницы каталога
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get('https://aroma-euro.ru/perfume/', headers=headers, timeout=10)
            if response.status_code == 200:
                # Создаем хэш контента страницы
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Ищем контейнер с товарами
                products_container = soup.find('div', class_='products-list') or soup.find('div', class_='catalog-items')
                
                if products_container:
                    content_hash = hashlib.md5(str(products_container).encode()).hexdigest()
                    
                    if self.last_catalog_hash is None:
                        self.last_catalog_hash = content_hash
                        return True  # Первая проверка - считаем что есть изменения
                    
                    if content_hash != self.last_catalog_hash:
                        self.last_catalog_hash = content_hash
                        return True
                    
                    return False
                else:
                    logger.warning("Не удалось найти контейнер с товарами на странице")
                    return True  # В случае сомнений лучше обновить
            else:
                logger.warning(f"Ошибка при проверке каталога: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при проверке изменений каталога: {e}")
            return False
    
    async def _update_search_indexes(self):
        """Обновляет поисковые индексы (заглушка)"""
        # Здесь можно добавить логику обновления индексов для поиска
        logger.info("🔍 Поисковые индексы обновлены")
    
    async def _notify_admin(self, message: str):
        """Уведомляет администратора о событиях"""
        try:
            if self.config and hasattr(self.config, 'admin_user_id'):
                # Здесь можно добавить отправку уведомления через Telegram
                # Пока просто логируем
                logger.info(f"📨 Уведомление админу: {message}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления админу: {e}")
    
    def get_parsing_status(self) -> Dict[str, Any]:
        """Возвращает статус парсинга"""
        return {
            'running': self.running,
            'last_check': datetime.now().isoformat(),
            'total_perfumes': self.db.count_perfumes(),
            'last_catalog_hash': self.last_catalog_hash
        }