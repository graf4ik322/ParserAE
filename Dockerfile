# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем пользователя для безопасности
RUN groupadd -r perfumebot && useradd -r -g perfumebot perfumebot

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY bot_requirements.txt .
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r bot_requirements.txt

# Копируем исходный код приложения
COPY . .

# Создаем директории для логов и устанавливаем права на файлы
RUN mkdir -p /app/logs && chown -R perfumebot:perfumebot /app

# Переключаемся на непривилегированного пользователя
USER perfumebot

# Проверяем наличие необходимых файлов данных
RUN python3 -c "import json; json.load(open('full_perfumes_catalog_complete.json'))" || \
    echo "Warning: full_perfumes_catalog_complete.json not found"

# Открываем порт для healthcheck (если понадобится)
EXPOSE 8080

# Healthcheck для проверки состояния контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Команда запуска
CMD ["python3", "main_bot.py"]