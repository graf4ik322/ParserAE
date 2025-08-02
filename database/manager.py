#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager

from .models import PerfumeModel, UserModel, UserSessionModel, UsageStatModel

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Создаем директорию для базы данных, если она не существует
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"📁 Создана директория для базы данных: {db_dir}")
        
        self._cache = {}
        self._cache_timestamps = {}
        logger.info(f"📊 DatabaseManager инициализирован: {db_path}")
        
        # Создаем таблицы при инициализации
        try:
            self.create_tables()
        except Exception as e:
            logger.error(f"❌ Ошибка при создании таблиц: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с соединением"""
        # Создаем соединение с правильными правами
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Возвращать строки как dict-like объекты
        
        # Устанавливаем правильные настройки для записи
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        try:
            yield conn
        finally:
            conn.close()
    
    def create_tables(self):
        """Создает все таблицы согласно схеме из технического задания"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица парфюмов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS perfumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article VARCHAR(50) UNIQUE NOT NULL,
                    unique_key VARCHAR(255) UNIQUE NOT NULL,
                    brand VARCHAR(100) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    full_title TEXT NOT NULL,
                    factory VARCHAR(100),
                    factory_detailed VARCHAR(100),
                    price DECIMAL(10,2),
                    price_formatted VARCHAR(50),
                    currency VARCHAR(10) DEFAULT 'RUB',
                    gender VARCHAR(20),
                    fragrance_group TEXT,
                    quality_level VARCHAR(50),
                    url VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username VARCHAR(100),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    quiz_profile JSON,
                    preferences JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица сессий пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    current_state VARCHAR(50),
                    quiz_answers JSON,
                    quiz_step INTEGER DEFAULT 0,
                    context_data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица статистики использования
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    action_type VARCHAR(50),
                    perfume_article VARCHAR(50),
                    query_text TEXT,
                    response_length INTEGER,
                    api_tokens_used INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создаем индексы для оптимизации
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_perfumes_article ON perfumes(article)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_perfumes_brand ON perfumes(brand)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_perfumes_active ON perfumes(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_user_id ON usage_stats(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_created_at ON usage_stats(created_at)")
            
            conn.commit()
            logger.info("✅ Таблицы базы данных созданы/обновлены")
    
    # === МЕТОДЫ ДЛЯ ПАРФЮМОВ ===
    
    def get_all_perfumes_from_database(self) -> List[Dict[str, Any]]:
        """Получает ВСЕ активные парфюмы из БД (режим без лимитов)"""
        cache_key = "all_perfumes"
        
        # Проверяем кэш
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, factory, article, price_formatted, brand, gender, 
                       fragrance_group, quality_level, url
                FROM perfumes 
                WHERE is_active = TRUE 
                ORDER BY brand, name
            """)
            
            perfumes = []
            for row in cursor.fetchall():
                perfumes.append({
                    'name': row['name'],
                    'factory': row['factory'] or '',
                    'article': row['article'],
                    'price_formatted': row['price_formatted'] or '',
                    'brand': row['brand'],
                    'gender': row['gender'] or '',
                    'fragrance_group': row['fragrance_group'] or '',
                    'quality_level': row['quality_level'] or '',
                    'url': row['url']
                })
            
            # Кэшируем результат на 1 час
            self._set_cache(cache_key, perfumes, ttl=3600)
            
            logger.info(f"📊 Загружено {len(perfumes)} парфюмов из БД")
            return perfumes
    
    def save_perfume_to_database(self, perfume_data: Dict[str, Any]) -> bool:
        """Сохраняет парфюм в БД (обновляет существующий или создает новый)"""
        try:
            # Валидируем данные перед сохранением
            if not self._validate_perfume_data(perfume_data):
                logger.error(f"Данные парфюма не прошли валидацию: {perfume_data.get('article', 'Unknown')}")
                return False
            
            # Очищаем и нормализуем данные
            perfume_data = self._normalize_perfume_data(perfume_data)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем существование по unique_key
                cursor.execute(
                    "SELECT id FROM perfumes WHERE unique_key = ?",
                    (perfume_data['unique_key'],)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Обновляем существующий
                    cursor.execute("""
                        UPDATE perfumes SET
                            article = ?, brand = ?, name = ?, full_title = ?,
                            factory = ?, factory_detailed = ?, price = ?, price_formatted = ?,
                            currency = ?, gender = ?, fragrance_group = ?, quality_level = ?,
                            url = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE unique_key = ?
                    """, (
                        perfume_data['article'], perfume_data['brand'], perfume_data['name'],
                        perfume_data['full_title'], perfume_data['factory'], 
                        perfume_data['factory_detailed'], perfume_data['price'],
                        perfume_data['price_formatted'], perfume_data['currency'],
                        perfume_data['gender'], perfume_data['fragrance_group'],
                        perfume_data['quality_level'], perfume_data['url'],
                        perfume_data['unique_key']
                    ))
                else:
                    # Создаем новый
                    cursor.execute("""
                        INSERT INTO perfumes (
                            article, unique_key, brand, name, full_title, factory,
                            factory_detailed, price, price_formatted, currency, gender,
                            fragrance_group, quality_level, url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        perfume_data['article'], perfume_data['unique_key'], perfume_data['brand'],
                        perfume_data['name'], perfume_data['full_title'], perfume_data['factory'],
                        perfume_data['factory_detailed'], perfume_data['price'], 
                        perfume_data['price_formatted'], perfume_data['currency'],
                        perfume_data['gender'], perfume_data['fragrance_group'],
                        perfume_data['quality_level'], perfume_data['url']
                    ))
                
                conn.commit()
                
                # Очищаем кэш
                self._clear_cache()
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении парфюма: {e}")
            logger.error(f"Проблемные данные: {perfume_data}")
            return False
    
    def _validate_perfume_data(self, data: Dict[str, Any]) -> bool:
        """Валидирует данные парфюма перед сохранением"""
        required_fields = ['article', 'unique_key', 'brand', 'name', 'full_title']
        
        # Проверяем наличие обязательных полей
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"Отсутствует обязательное поле: {field}")
                return False
        
        # Проверяем длину строк
        string_limits = {
            'article': 50,
            'unique_key': 100,
            'brand': 100,
            'name': 200,
            'full_title': 500,
            'factory': 100,
            'factory_detailed': 200,
            'currency': 10,
            'gender': 20,
            'fragrance_group': 100,
            'quality_level': 50,
            'url': 1000
        }
        
        for field, limit in string_limits.items():
            if field in data and data[field] and len(str(data[field])) > limit:
                logger.warning(f"Поле {field} превышает максимальную длину {limit}: {len(str(data[field]))}")
                return False
        
        # Проверяем числовые поля
        if 'price' in data and data['price'] is not None:
            try:
                float(data['price'])
            except (ValueError, TypeError):
                logger.warning(f"Некорректная цена: {data['price']}")
                return False
        
        return True
    
    def _normalize_perfume_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализует данные парфюма"""
        normalized = data.copy()
        
        # Обрезаем строки до максимальной длины
        string_limits = {
            'article': 50,
            'unique_key': 100,
            'brand': 100,
            'name': 200,
            'full_title': 500,
            'factory': 100,
            'factory_detailed': 200,
            'currency': 10,
            'gender': 20,
            'fragrance_group': 100,
            'quality_level': 50,
            'url': 1000
        }
        
        for field, limit in string_limits.items():
            if field in normalized and normalized[field]:
                normalized[field] = str(normalized[field])[:limit].strip()
        
        # Нормализуем цену
        if 'price' in normalized and normalized['price'] is not None:
            try:
                normalized['price'] = float(normalized['price'])
            except (ValueError, TypeError):
                normalized['price'] = None
        
        return normalized
    
    def get_perfume_url_by_article(self, article: str) -> Optional[str]:
        """Получает URL парфюма по артикулу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT url FROM perfumes WHERE article = ? AND is_active = TRUE",
                (article,)
            )
            result = cursor.fetchone()
            return result['url'] if result else None
    
    def count_perfumes(self) -> int:
        """Подсчитывает общее количество активных парфюмов"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM perfumes WHERE is_active = TRUE")
            return cursor.fetchone()['count']
    
    def get_perfume_by_unique_key(self, unique_key: str) -> Optional[Dict[str, Any]]:
        """Получает парфюм по уникальному ключу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM perfumes WHERE unique_key = ?", (unique_key,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': result['id'],
                    'article': result['article'],
                    'unique_key': result['unique_key'],
                    'brand': result['brand'],
                    'name': result['name'],
                    'full_title': result['full_title'],
                    'factory': result['factory'],
                    'factory_detailed': result['factory_detailed'],
                    'price': result['price'],
                    'price_formatted': result['price_formatted'],
                    'currency': result['currency'],
                    'gender': result['gender'],
                    'fragrance_group': result['fragrance_group'],
                    'quality_level': result['quality_level'],
                    'url': result['url'],
                    'created_at': result['created_at'],
                    'updated_at': result['updated_at'],
                    'is_active': result['is_active']
                }
            return None
    
    # === МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===
    
    def get_or_create_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """Получает существующего пользователя или создает нового"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ищем существующего
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            
            if user:
                # Обновляем время последней активности
                cursor.execute(
                    "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE telegram_id = ?",
                    (telegram_id,)
                )
                conn.commit()
                
                return {
                    'id': user['id'],
                    'telegram_id': user['telegram_id'],
                    'username': user['username'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'quiz_profile': json.loads(user['quiz_profile'] or '{}'),
                    'preferences': json.loads(user['preferences'] or '{}'),
                    'created_at': user['created_at'],
                    'last_activity': user['last_activity']
                }
            else:
                # Создаем нового
                cursor.execute("""
                    INSERT INTO users (telegram_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                """, (telegram_id, username, first_name, last_name))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"👤 Создан новый пользователь: {telegram_id}")
                
                return {
                    'id': user_id,
                    'telegram_id': telegram_id,
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'quiz_profile': {},
                    'preferences': {},
                    'created_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat()
                }
    
    def save_user_quiz_profile(self, user_id: int, profile: Dict[str, Any]):
        """Сохраняет профиль квиза пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET quiz_profile = ? WHERE telegram_id = ?",
                (json.dumps(profile, ensure_ascii=False), user_id)
            )
            conn.commit()
    
    def count_users(self) -> int:
        """Подсчитывает общее количество пользователей"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            return cursor.fetchone()['count']
    
    def count_active_users_today(self) -> int:
        """Подсчитывает активных пользователей за сегодня"""
        today = datetime.now().date()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM users WHERE DATE(last_activity) = ?",
                (today,)
            )
            return cursor.fetchone()['count']
    
    # === МЕТОДЫ ДЛЯ СЕССИЙ ===
    
    def get_user_session(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает текущую сессию пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем user_id
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if not user:
                return None
            
            user_id = user['id']
            
            # Получаем сессию
            cursor.execute("""
                SELECT * FROM user_sessions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            
            session = cursor.fetchone()
            if not session:
                return None
            
            # Проверяем актуальность сессии (не старше 24 часов)
            session_time = datetime.fromisoformat(session['created_at'])
            if datetime.now() - session_time > timedelta(hours=24):
                # Удаляем устаревшую сессию
                cursor.execute("DELETE FROM user_sessions WHERE id = ?", (session['id'],))
                conn.commit()
                return None
            
            return {
                'id': session['id'],
                'user_id': session['user_id'],
                'current_state': session['current_state'],
                'quiz_answers': json.loads(session['quiz_answers'] or '{}'),
                'quiz_step': session['quiz_step'],
                'context_data': json.loads(session['context_data'] or '{}'),
                'created_at': session['created_at'],
                'updated_at': session['updated_at']
            }
    
    def update_session_state(self, telegram_id: int, new_state: str, context_data: Dict = None):
        """Обновляет состояние сессии пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем user_id
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if not user:
                return
            
            user_id = user['id']
            
            # Проверяем существующую сессию
            cursor.execute(
                "SELECT id FROM user_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            session = cursor.fetchone()
            
            if session:
                # Обновляем существующую
                update_data = [new_state]
                update_query = "UPDATE user_sessions SET current_state = ?, updated_at = CURRENT_TIMESTAMP"
                
                if context_data:
                    update_query += ", context_data = ?"
                    update_data.append(json.dumps(context_data, ensure_ascii=False))
                
                update_query += " WHERE id = ?"
                update_data.append(session['id'])
                
                cursor.execute(update_query, update_data)
            else:
                # Создаем новую
                cursor.execute("""
                    INSERT INTO user_sessions (user_id, current_state, context_data)
                    VALUES (?, ?, ?)
                """, (user_id, new_state, json.dumps(context_data or {}, ensure_ascii=False)))
            
            conn.commit()
    
    def reset_user_session(self, telegram_id: int):
        """Сбрасывает сессию пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем user_id
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if not user:
                return
            
            user_id = user['id']
            
            # Удаляем все сессии пользователя
            cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
            conn.commit()
    
    def update_quiz_session(self, telegram_id: int, quiz_answers: Dict, quiz_step: int):
        """Обновляет данные квиза в сессии"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем user_id
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if not user:
                return
            
            user_id = user['id']
            
            # Обновляем квиз данные
            cursor.execute("""
                UPDATE user_sessions 
                SET quiz_answers = ?, quiz_step = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (json.dumps(quiz_answers, ensure_ascii=False), quiz_step, user_id))
            
            conn.commit()
    
    # === МЕТОДЫ ДЛЯ СТАТИСТИКИ ===
    
    def save_usage_stat(self, telegram_id: int, action_type: str, perfume_article: str = None,
                       query_text: str = None, response_length: int = 0):
        """Сохраняет статистику использования"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем user_id
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if not user:
                return
            
            user_id = user['id']
            
            # Оцениваем количество токенов
            api_tokens_used = self._estimate_tokens_used(query_text, response_length)
            
            cursor.execute("""
                INSERT INTO usage_stats (
                    user_id, action_type, perfume_article, query_text, 
                    response_length, api_tokens_used
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, action_type, perfume_article, query_text, response_length, api_tokens_used))
            
            conn.commit()
    
    def get_admin_statistics(self) -> Dict[str, int]:
        """Получает статистику для администратора"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Общие статистики
            stats['total_users'] = self.count_users()
            stats['active_users_today'] = self.count_active_users_today()
            stats['total_perfumes'] = self.count_perfumes()
            
            # Статистика действий
            cursor.execute(
                "SELECT COUNT(*) as count FROM usage_stats WHERE action_type = 'perfume_question'"
            )
            stats['total_questions'] = cursor.fetchone()['count']
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM usage_stats WHERE action_type = 'quiz_completed'"
            )
            stats['total_quizzes'] = cursor.fetchone()['count']
            
            # API использование за сегодня
            today = datetime.now().date()
            cursor.execute(
                "SELECT COALESCE(SUM(api_tokens_used), 0) as total FROM usage_stats WHERE DATE(created_at) = ?",
                (today,)
            )
            stats['api_usage_today'] = cursor.fetchone()['total']
            
            return stats

    def get_detailed_database_info(self) -> Dict[str, Any]:
        """Получает подробную информацию о базе данных для админ-панели"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            info = {
                'database_path': self.db_path,
                'database_size': self._get_database_size(),
                'tables': {},
                'recent_activity': {},
                'top_users': [],
                'perfume_stats': {},
                'errors': []
            }
            
            try:
                # Информация о таблицах
                tables = ['perfumes', 'users', 'user_sessions', 'usage_stats']
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                        count = cursor.fetchone()['count']
                        
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                        exists = cursor.fetchone() is not None
                        
                        info['tables'][table] = {
                            'count': count,
                            'exists': exists
                        }
                        
                        # Дополнительная информация для каждой таблицы
                        if table == 'perfumes':
                            # Статистика по брендам
                            cursor.execute("""
                                SELECT brand, COUNT(*) as count 
                                FROM perfumes 
                                GROUP BY brand 
                                ORDER BY count DESC 
                                LIMIT 10
                            """)
                            info['perfume_stats']['top_brands'] = [dict(row) for row in cursor.fetchall()]
                            
                            # Статистика по гендеру
                            cursor.execute("""
                                SELECT gender, COUNT(*) as count 
                                FROM perfumes 
                                GROUP BY gender 
                                ORDER BY count DESC
                            """)
                            info['perfume_stats']['by_gender'] = [dict(row) for row in cursor.fetchall()]
                            
                        elif table == 'users':
                            # Топ активных пользователей
                            cursor.execute("""
                                SELECT u.telegram_id, u.username, u.first_name, 
                                       COUNT(us.id) as activity_count,
                                       MAX(us.created_at) as last_activity
                                FROM users u
                                LEFT JOIN usage_stats us ON u.telegram_id = us.user_id
                                GROUP BY u.telegram_id
                                ORDER BY activity_count DESC
                                LIMIT 10
                            """)
                            info['top_users'] = [dict(row) for row in cursor.fetchall()]
                            
                    except Exception as e:
                        info['errors'].append(f"Ошибка при анализе таблицы {table}: {str(e)}")
                
                # Активность за последние дни
                cursor.execute("""
                    SELECT DATE(created_at) as date, 
                           action_type,
                           COUNT(*) as count
                    FROM usage_stats 
                    WHERE created_at >= datetime('now', '-7 days')
                    GROUP BY DATE(created_at), action_type
                    ORDER BY date DESC
                """)
                activity_data = cursor.fetchall()
                
                activity_by_date = {}
                for row in activity_data:
                    date = row['date']
                    if date not in activity_by_date:
                        activity_by_date[date] = {}
                    activity_by_date[date][row['action_type']] = row['count']
                
                info['recent_activity'] = activity_by_date
                
                # Статистика API использования
                cursor.execute("""
                    SELECT DATE(created_at) as date,
                           COUNT(*) as requests,
                           COALESCE(SUM(api_tokens_used), 0) as total_tokens,
                           COALESCE(AVG(api_tokens_used), 0) as avg_tokens
                    FROM usage_stats 
                    WHERE created_at >= datetime('now', '-30 days')
                    AND api_tokens_used > 0
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    LIMIT 10
                """)
                info['api_usage'] = [dict(row) for row in cursor.fetchall()]
                
            except Exception as e:
                info['errors'].append(f"Общая ошибка при получении информации о БД: {str(e)}")
            
            return info

    def get_parser_statistics(self) -> Dict[str, Any]:
        """Получает статистику работы парсера"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {
                'last_parse_time': None,
                'total_parses': 0,
                'successful_parses': 0,
                'failed_parses': 0,
                'items_added_last_parse': 0,
                'items_updated_last_parse': 0,
                'parse_history': [],
                'errors': []
            }
            
            try:
                # Проверяем, есть ли таблица для статистики парсера
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='parser_logs'
                """)
                
                if cursor.fetchone():
                    # Получаем последний парсинг
                    cursor.execute("""
                        SELECT * FROM parser_logs 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """)
                    last_parse = cursor.fetchone()
                    if last_parse:
                        stats['last_parse_time'] = last_parse['created_at']
                        stats['items_added_last_parse'] = last_parse.get('items_added', 0)
                        stats['items_updated_last_parse'] = last_parse.get('items_updated', 0)
                    
                    # Общая статистика
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed
                        FROM parser_logs
                    """)
                    totals = cursor.fetchone()
                    if totals:
                        stats['total_parses'] = totals['total']
                        stats['successful_parses'] = totals['successful']
                        stats['failed_parses'] = totals['failed']
                    
                    # История парсинга
                    cursor.execute("""
                        SELECT * FROM parser_logs 
                        ORDER BY created_at DESC 
                        LIMIT 20
                    """)
                    stats['parse_history'] = [dict(row) for row in cursor.fetchall()]
                else:
                    stats['errors'].append("Таблица parser_logs не существует")
                    
            except Exception as e:
                stats['errors'].append(f"Ошибка при получении статистики парсера: {str(e)}")
            
            return stats

    def _get_database_size(self) -> str:
        """Получает размер файла базы данных"""
        try:
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                
                # Конвертируем в удобный формат
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
            else:
                return "Файл не найден"
        except Exception as e:
            return f"Ошибка: {str(e)}"

    def create_parser_logs_table(self):
        """Создает таблицу для логов парсера если она не существует"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parser_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    items_added INTEGER DEFAULT 0,
                    items_updated INTEGER DEFAULT 0,
                    source TEXT,
                    error_message TEXT,
                    execution_time_seconds REAL,
                    metadata TEXT
                )
            """)
            conn.commit()

    def log_parser_execution(self, status: str, items_added: int = 0, items_updated: int = 0, 
                           source: str = None, error_message: str = None, 
                           execution_time: float = None, metadata: Dict = None):
        """Логирует выполнение парсера"""
        try:
            self.create_parser_logs_table()  # Убедимся что таблица существует
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO parser_logs 
                    (status, items_added, items_updated, source, error_message, execution_time_seconds, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    status, items_added, items_updated, source, error_message, 
                    execution_time, json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                logger.info(f"📝 Логирование парсера: {status}, +{items_added}, ~{items_updated}")
        except Exception as e:
            logger.error(f"❌ Ошибка при логировании парсера: {e}")
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _is_cache_valid(self, key: str, ttl: int = 3600) -> bool:
        """Проверяет актуальность кэша"""
        if key not in self._cache:
            return False
        
        timestamp = self._cache_timestamps.get(key, 0)
        return (datetime.now().timestamp() - timestamp) < ttl
    
    def _set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Устанавливает значение в кэш"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now().timestamp()
    
    def _clear_cache(self):
        """Очищает весь кэш"""
        self._cache.clear()
        self._cache_timestamps.clear()
    
    def _estimate_tokens_used(self, query_text: str = None, response_length: int = 0) -> int:
        """Оценивает количество использованных токенов"""
        # Примерная оценка: 1 токен = 4 символа для русского текста
        query_tokens = len(query_text or '') // 4
        response_tokens = response_length // 4
        return query_tokens + response_tokens