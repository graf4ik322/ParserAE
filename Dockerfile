FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем директории для данных и логов
RUN mkdir -p /app/data /app/logs

# Устанавливаем права доступа
RUN chmod +x main.py

# Создаем пользователя для запуска приложения (безопасность)
RUN useradd -m -u 1001 botuser && chown -R botuser:botuser /app

# Устанавливаем правильные права на директории данных
RUN chown -R botuser:botuser /app/data /app/logs
RUN chmod 755 /app/data /app/logs

USER botuser

# Переменные окружения по умолчанию
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "main.py"]