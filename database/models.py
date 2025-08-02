#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional

class PerfumeModel:
    """Модель парфюма"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.article = data.get('article', '')
        self.unique_key = data.get('unique_key', '')
        self.brand = data.get('brand', '')
        self.name = data.get('name', '')
        self.full_title = data.get('full_title', '')
        self.factory = data.get('factory', '')
        self.factory_detailed = data.get('factory_detailed', '')
        self.price = data.get('price', 0.0)
        self.price_formatted = data.get('price_formatted', '')
        self.currency = data.get('currency', 'RUB')
        self.gender = data.get('gender', '')
        self.fragrance_group = data.get('fragrance_group', '')
        self.quality_level = data.get('quality_level', '')
        self.url = data.get('url', '')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self.is_active = data.get('is_active', True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь"""
        return {
            'id': self.id,
            'article': self.article,
            'unique_key': self.unique_key,
            'brand': self.brand,
            'name': self.name,
            'full_title': self.full_title,
            'factory': self.factory,
            'factory_detailed': self.factory_detailed,
            'price': self.price,
            'price_formatted': self.price_formatted,
            'currency': self.currency,
            'gender': self.gender,
            'fragrance_group': self.fragrance_group,
            'quality_level': self.quality_level,
            'url': self.url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active
        }

class UserModel:
    """Модель пользователя"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.telegram_id = data.get('telegram_id')
        self.username = data.get('username', '')
        self.first_name = data.get('first_name', '')
        self.last_name = data.get('last_name', '')
        self.quiz_profile = data.get('quiz_profile', {})
        self.preferences = data.get('preferences', {})
        self.created_at = data.get('created_at')
        self.last_activity = data.get('last_activity')
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'quiz_profile': self.quiz_profile,
            'preferences': self.preferences,
            'created_at': self.created_at,
            'last_activity': self.last_activity
        }

class UserSessionModel:
    """Модель сессии пользователя"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.current_state = data.get('current_state', '')
        self.quiz_answers = data.get('quiz_answers', {})
        self.quiz_step = data.get('quiz_step', 0)
        self.context_data = data.get('context_data', {})
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'current_state': self.current_state,
            'quiz_answers': self.quiz_answers,
            'quiz_step': self.quiz_step,
            'context_data': self.context_data,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class UsageStatModel:
    """Модель статистики использования"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.action_type = data.get('action_type', '')
        self.perfume_article = data.get('perfume_article')
        self.query_text = data.get('query_text', '')
        self.response_length = data.get('response_length', 0)
        self.api_tokens_used = data.get('api_tokens_used', 0)
        self.created_at = data.get('created_at')
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'perfume_article': self.perfume_article,
            'query_text': self.query_text,
            'response_length': self.response_length,
            'api_tokens_used': self.api_tokens_used,
            'created_at': self.created_at
        }