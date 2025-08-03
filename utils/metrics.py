#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class FunctionMetrics:
    """Метрики для одной функции"""
    function_name: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    last_call_time: Optional[datetime] = None
    last_execution_time: Optional[float] = None
    errors: int = 0
    
    @property
    def avg_time(self) -> float:
        """Среднее время выполнения"""
        return self.total_time / self.total_calls if self.total_calls > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """Процент успешных вызовов"""
        total = self.total_calls + self.errors
        return (self.total_calls / total * 100) if total > 0 else 0.0

class MetricsCollector:
    """Сборщик метрик для отслеживания производительности"""
    
    def __init__(self):
        self.metrics: Dict[str, FunctionMetrics] = defaultdict(lambda: FunctionMetrics(""))
        self._lock = asyncio.Lock()
    
    async def track_function(self, function_name: str, func, *args, **kwargs):
        """Отслеживает выполнение функции с метриками"""
        start_time = time.time()
        start_datetime = datetime.now()
        
        try:
            # Выполняем функцию
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Записываем успешную метрику
            execution_time = time.time() - start_time
            await self._record_metric(function_name, execution_time, start_datetime, success=True)
            
            return result
            
        except Exception as e:
            # Записываем метрику ошибки
            execution_time = time.time() - start_time
            await self._record_metric(function_name, execution_time, start_datetime, success=False)
            logger.error(f"Ошибка в функции {function_name}: {e}")
            raise
    
    async def _record_metric(self, function_name: str, execution_time: float, 
                           call_time: datetime, success: bool = True):
        """Записывает метрику выполнения функции"""
        async with self._lock:
            if function_name not in self.metrics:
                self.metrics[function_name] = FunctionMetrics(function_name)
            
            metric = self.metrics[function_name]
            
            if success:
                metric.total_calls += 1
                metric.total_time += execution_time
                metric.min_time = min(metric.min_time, execution_time)
                metric.max_time = max(metric.max_time, execution_time)
            else:
                metric.errors += 1
            
            metric.last_call_time = call_time
            metric.last_execution_time = execution_time
    
    def get_function_metrics(self, function_name: str) -> Optional[FunctionMetrics]:
        """Получает метрики для конкретной функции"""
        return self.metrics.get(function_name)
    
    def get_all_metrics(self) -> Dict[str, FunctionMetrics]:
        """Получает все метрики"""
        return dict(self.metrics)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получает сводку производительности"""
        summary = {
            'total_functions': len(self.metrics),
            'total_calls': sum(m.total_calls for m in self.metrics.values()),
            'total_errors': sum(m.errors for m in self.metrics.values()),
            'functions': {}
        }
        
        for name, metric in self.metrics.items():
            summary['functions'][name] = {
                'total_calls': metric.total_calls,
                'total_time': round(metric.total_time, 3),
                'avg_time': round(metric.avg_time, 3),
                'min_time': round(metric.min_time, 3) if metric.min_time != float('inf') else 0,
                'max_time': round(metric.max_time, 3),
                'success_rate': round(metric.success_rate, 1),
                'errors': metric.errors,
                'last_call': metric.last_call_time.isoformat() if metric.last_call_time else None,
                'last_execution_time': round(metric.last_execution_time, 3) if metric.last_execution_time else None
            }
        
        return summary
    
    def reset_metrics(self):
        """Сбрасывает все метрики"""
        self.metrics.clear()

# Глобальный экземпляр сборщика метрик
metrics_collector = MetricsCollector()

def track_function(function_name: str):
    """Декоратор для отслеживания функции"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            return await metrics_collector.track_function(function_name, func, *args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            return metrics_collector.track_function(function_name, func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator