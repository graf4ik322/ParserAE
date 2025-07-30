# 🐳 Docker развертывание парфюмерного консультанта

Быстрое развертывание Telegram-бота парфюмерного консультанта с помощью Docker и Docker Compose.

## 🚀 Быстрый старт

### 1. Предварительные требования

Убедитесь, что на вашем сервере установлены:
- **Docker** (версия 20.10+)
- **Docker Compose** (версия 1.27+)
- **Git** (для клонирования репозитория)

#### Установка Docker на Ubuntu/Debian:
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавляем пользователя в группу docker
sudo usermod -aG docker $USER

# Устанавливаем Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагружаемся для применения изменений
sudo reboot
```

### 2. Клонирование и настройка

```bash
# Клонируем репозиторий
git clone <your-repo-url>
cd perfume-consultant-bot

# Запускаем автоматическое развертывание
./deploy.sh
```

Скрипт автоматически:
- Проверит наличие Docker и Docker Compose
- Создаст `.env` файл из примера
- Проверит наличие файлов данных
- Соберет и запустит контейнеры

### 3. Настройка переменных окружения

Отредактируйте файл `.env`:
```bash
nano .env
```

Заполните обязательные параметры:
```env
# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ

# OpenRouter API Key (получить на openrouter.ai)
OPENROUTER_API_KEY=sk-or-v1-abcdefghijklmnopqrstuvwxyz

# Admin User ID (получить у @userinfobot)
ADMIN_USER_ID=123456789
```

## 🔧 Управление сервисами

### Основные команды

```bash
# Запуск бота
./scripts/start.sh

# Остановка бота
./scripts/stop.sh

# Просмотр логов в реальном времени
./scripts/logs.sh

# Обновление бота (пересборка и перезапуск)
./scripts/update.sh

# Полное развертывание (первоначальная настройка)
./deploy.sh
```

### Docker Compose команды

```bash
# Запуск сервисов
docker-compose up -d

# Остановка сервисов
docker-compose down

# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f perfume-bot

# Перезапуск конкретного сервиса
docker-compose restart perfume-bot

# Пересборка образа
docker-compose build --no-cache
```

## 📊 Мониторинг и логирование

### Просмотр логов

```bash
# Логи в реальном времени
docker-compose logs -f perfume-bot

# Последние 100 строк логов
docker-compose logs --tail=100 perfume-bot

# Логи с временными метками
docker-compose logs -t perfume-bot
```

### Веб-интерфейс для логов (опционально)

Запустите Dozzle для веб-просмотра логов:
```bash
docker-compose --profile monitoring up -d
```

Откройте в браузере: `http://your-server:8080`

### Автоматические обновления (опционально)

Включите Watchtower для автоматического обновления:
```bash
docker-compose --profile auto-update up -d
```

## 🔍 Диагностика проблем

### Проверка состояния контейнера

```bash
# Статус всех сервисов
docker-compose ps

# Детальная информация о контейнере
docker inspect perfume-consultant-bot

# Проверка здоровья контейнера
docker-compose exec perfume-bot python3 -c "print('Bot is healthy!')"
```

### Распространенные проблемы

#### 1. Контейнер не запускается
```bash
# Проверяем логи
docker-compose logs perfume-bot

# Проверяем .env файл
cat .env

# Проверяем наличие файлов данных
ls -la *.json
```

#### 2. Бот не отвечает
```bash
# Проверяем подключение к Telegram API
docker-compose exec perfume-bot curl -s https://api.telegram.org/bot$BOT_TOKEN/getMe

# Перезапускаем бота
docker-compose restart perfume-bot
```

#### 3. Ошибки OpenRouter API
```bash
# Проверяем API ключ
docker-compose exec perfume-bot curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/auth/key
```

## 📁 Структура проекта

```
perfume-consultant-bot/
├── Dockerfile                 # Описание Docker образа
├── docker-compose.yml         # Оркестрация сервисов
├── .dockerignore              # Исключения для Docker
├── deploy.sh                  # Скрипт развертывания
├── scripts/                   # Скрипты управления
│   ├── start.sh              # Запуск
│   ├── stop.sh               # Остановка
│   ├── logs.sh               # Просмотр логов
│   └── update.sh             # Обновление
├── logs/                      # Логи (создается автоматически)
├── .env                       # Переменные окружения
└── ... (остальные файлы проекта)
```

## 🔐 Безопасность

### Рекомендации по безопасности

1. **Защита .env файла**:
```bash
chmod 600 .env
```

2. **Регулярные обновления**:
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Обновление Docker образов
docker-compose pull
docker-compose up -d
```

3. **Мониторинг логов**:
```bash
# Настройка ротации логов
echo '{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}' | sudo tee /etc/docker/daemon.json

sudo systemctl restart docker
```

4. **Файрвол**:
```bash
# Закрываем ненужные порты
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8080  # Только если используете веб-мониторинг
```

## 🚀 Производственное развертывание

### Системный сервис (systemd)

Создайте systemd сервис для автозапуска:

```bash
sudo nano /etc/systemd/system/perfume-bot.service
```

```ini
[Unit]
Description=Perfume Consultant Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/perfume-consultant-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Включаем сервис
sudo systemctl enable perfume-bot.service
sudo systemctl start perfume-bot.service

# Проверяем статус
sudo systemctl status perfume-bot.service
```

### Резервное копирование

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/perfume-bot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Создаем архив
tar -czf $BACKUP_DIR/perfume-bot-$DATE.tar.gz \
  --exclude=logs \
  --exclude=.git \
  .

# Сохраняем только последние 7 резервных копий
find $BACKUP_DIR -name "perfume-bot-*.tar.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_DIR/perfume-bot-$DATE.tar.gz"
```

## 📈 Масштабирование

### Горизонтальное масштабирование

Для высокой нагрузки можно запустить несколько экземпляров:

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  perfume-bot:
    build: .
    deploy:
      replicas: 3
    # ... остальная конфигурация
```

```bash
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale perfume-bot=3
```

### Мониторинг ресурсов

```bash
# Использование ресурсов
docker stats perfume-consultant-bot

# Размер образов
docker images | grep perfume

# Использование места
docker system df
```

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `./scripts/logs.sh`
2. Проверьте статус: `docker-compose ps`
3. Перезапустите: `./scripts/update.sh`
4. Создайте issue в GitHub с логами

---

**Создано с ❤️ для простого развертывания парфюмерного консультанта**