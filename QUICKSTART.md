# ⚡ Быстрый старт - Парфюмерный консультант

Развертывание Telegram-бота за 5 минут с помощью Docker.

## 🚀 Минимальная установка

### Шаг 1: Подготовка сервера
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo reboot
```

### Шаг 2: Клонирование и развертывание
```bash
git clone <your-repo-url>
cd perfume-consultant-bot
./deploy.sh
```

### Шаг 3: Настройка .env
```bash
nano .env
```
Заполните:
- `BOT_TOKEN` - от @BotFather
- `OPENROUTER_API_KEY` - с openrouter.ai  
- `ADMIN_USER_ID` - от @userinfobot

### Шаг 4: Запуск
```bash
./scripts/start.sh
```

## 🎯 Готово!

Ваш бот запущен и готов к работе.

## 📋 Управление

```bash
# Просмотр логов
./scripts/logs.sh

# Остановка
./scripts/stop.sh

# Обновление
./scripts/update.sh
```

## 🆘 Проблемы?

```bash
# Проверка статуса
docker-compose ps

# Перезапуск
docker-compose restart perfume-bot
```

---

**📖 Подробная документация:** [README_DOCKER.md](README_DOCKER.md)