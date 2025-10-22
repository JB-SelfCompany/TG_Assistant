# 🤖 Telegram Personal Assistant Bot

Многофункциональный Telegram-бот на Python для управления повседневными задачами, напоминаниями, отслеживания дней рождений, проверки погоды и конвертации валют.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://telegram.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-blue)](https://docs.aiogram.dev/)

## 📋 Содержание

- [Возможности](#-возможности)
- [Технологический стек](#-технологический-стек)
- [Структура проекта](#-структура-проекта)
- [Установка](#-установка)
- [Настройка](#-настройка)
- [Запуск](#-запуск)
- [Использование](#-использование)
- [Архитектура](#-архитектура)
- [Разработка](#-разработка)
- [Лицензия](#-лицензия)
- [Контрибьюция](#-контрибьюция)

## ✨ Возможности

### 📋 Управление задачами
- Создание задач с напоминаниями
- Автоматические уведомления о приближающихся дедлайнах
- Возможность отложить или завершить задачу
- Отслеживание просроченных задач
- Pagination для удобного просмотра списка задач

### 🎂 Дни рождения
- Добавление и хранение дней рождений
- Автоматические напоминания за день до события
- Расчет возраста и дней до следующего дня рождения
- Управление списком именинников

### 🌤 Погода
- Текущая погода в выбранном городе
- Прогноз погоды на 5 дней
- Интеграция с OpenWeatherMap API
- Настройка города по умолчанию

### 💱 Валютные курсы
- Актуальные курсы валют ЦБ РФ
- Конвертация между различными валютами
- Поддержка всех основных валют
- Автоматическое обновление курсов

### 📍 Поиск мест
- Поиск ближайших аптек, магазинов, кафе
- Интеграция с Nominatim OpenStreetMap API
- Отображение расстояния до объектов
- Настраиваемый радиус поиска

### ⚙️ Настройки пользователя
- Персонализация временной зоны
- Настройка местоположения по умолчанию
- Гибкая конфигурация параметров

## 🛠 Технологический стек

### Core
- **Python 3.12+** - Современные возможности языка
- **aiogram 3.22.0** - Асинхронный фреймворк для Telegram Bot API
- **aiosqlite** - Асинхронная работа с SQLite базой данных
- **APScheduler 3.11** - Планировщик задач для напоминаний

### External APIs
- **OpenWeatherMap API** - Данные о погоде
- **Central Bank of Russia API** - Курсы валют
- **Nominatim OpenStreetMap API** - Геопоиск

### Utilities
- **aiohttp** - Асинхронные HTTP-запросы
- **geopy** - Геокодирование и работа с координатами
- **pydantic & pydantic-settings** - Валидация конфигурации
- **python-dotenv** - Управление переменными окружения

## 📁 Структура проекта

```
TG_Assistant/
├── bot_main.py # Точка входа приложения
├── config.py # Настройки и конфигурация
├── requirements.txt # Зависимости проекта
├── .env.example # Шаблон переменных окружения
│
├── handlers/ # Обработчики команд и сообщений
│ ├── init.py
│ ├── start.py # Команды /start, /help, /menu
│ ├── tasks.py # Управление задачами
│ ├── birthdays.py # Управление днями рождения
│ ├── weather.py # Прогноз погоды
│ ├── currency.py # Валютные операции
│ ├── places.py # Поиск мест поблизости
│ └── settings.py # Настройки пользователя
│
├── database/ # Слой работы с данными
│ ├── init.py
│ ├── database.py # Менеджер подключений
│ └── models.py # Репозитории и модели данных
│
├── services/ # Бизнес-логика и внешние API
│ ├── init.py
│ ├── weather_service.py # Сервис погоды
│ ├── currency_service.py # Сервис валют
│ └── places_service.py # Сервис геопоиска
│
├── keyboards/ # Inline-клавиатуры
│ ├── init.py
│ └── menu.py # Меню навигации
│
├── middlewares/ # Middleware компоненты
│ ├── init.py
│ └── database.py # Database middleware
│
└── utils/ # Вспомогательные утилиты
├── init.py
├── scheduler.py # Планировщик задач
├── logger.py # Настройка логирования
└── user_states.py # FSM состояния
```


## 📦 Установка

### Предварительные требования

- Python 3.12 или выше
- pip (менеджер пакетов Python)
- Telegram Bot Token (получить у [@BotFather](https://t.me/botfather))
- OpenWeatherMap API Key (зарегистрироваться на [openweathermap.org](https://openweathermap.org/api))

### Шаги установки

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/yourusername/telegram-assistant-bot.git
cd telegram-assistant-bot
```


2. **Создайте виртуальное окружение**

Linux
```bash
python -m venv venv
```
Windows

```bash
venv\Scripts\activate
```

Linux/macOS
```bash
source venv/bin/activate
```

3. **Установите зависимости**

```bash
pip install -r requirements.txt
```

## ⚙️ Настройка

1. **Создайте файл `.env` из шаблона**

```bash
cp .env.example .env
```

2. **Заполните переменные окружения**

Откройте файл `.env` и укажите свои данные:

```bash
BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id

# Weather API Configuration
WEATHER_API_KEY=your_openweathermap_api_key
DEFAULT_CITY=YourCity

# Location Settings
DEFAULT_TIMEZONE=Europe/Moscow

# Logging
LOG_LEVEL=INFO

# Database
DATABASE_PATH=./bot_database.db
```

### Получение токенов

**Telegram Bot Token:**
1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и получите токен

**OpenWeatherMap API Key:**
1. Зарегистрируйтесь на [openweathermap.org](https://openweathermap.org/api)
2. Перейдите в раздел API Keys
3. Создайте новый ключ (бесплатный тариф доступен)

**Ваш Telegram User ID:**
1. Откройте [@userinfobot](https://t.me/userinfobot)
2. Отправьте команду `/start`
3. Скопируйте ваш ID

## 🚀 Запуск

### Запуск бота

```bash
python bot_main.py
```

При успешном запуске вы увидите:

```bash
Starting Telegram Bot
Database connected
Scheduler started
Starting polling...
```

### Запуск в фоновом режиме (Linux)

```bash
nohup python bot_main.py > bot.log 2>&1 &
```

### Остановка бота

Нажмите `Ctrl+C` для корректного завершения работы.

## 💬 Использование

### Основные команды

- `/start` - Запустить бота и увидеть приветственное сообщение

### Навигация

Бот использует inline-клавиатуры для удобной навигации между разделами:

1. **Задачи** - Создание и управление задачами с напоминаниями
2. **Дни рождения** - Добавление и отслеживание важных дат
3. **Погода** - Текущая погода и прогноз на 5 дней
4. **Валюты** - Актуальные курсы и конвертация
5. **Места** - Поиск близких объектов
6. **Настройки** - Персонализация параметров

### Примеры использования

**Создание задачи:**
1. Нажмите "📋 Задачи" → "➕ Новая задача"
2. Введите название задачи
3. Добавьте описание (или `-` для пропуска)
4. Укажите дату и время в формате `15.10.2025 14:30`

**Добавление дня рождения:**
1. Нажмите "🎂 Дни рождения" → "➕ Добавить"
2. Введите имя человека
3. Укажите дату рождения в формате `15.03.1990`

**Проверка погоды:**
1. Нажмите "🌤 Погода"
2. Выберите "Текущая погода" или "Прогноз на 5 дней"

## 🏗 Архитектура

### Clean Architecture

Проект следует принципам Clean Architecture с четким разделением слоев:

- **Handlers** - Presentation layer (UI логика)
- **Services** - Business logic layer (внешние API)
- **Database** - Data access layer (работа с БД)
- **Models** - Domain entities (репозитории)

### Асинхронность

Весь код использует async/await паттерны для максимальной производительности:

- Неблокирующие операции ввода-вывода
- Параллельная обработка запросов
- Эффективное использование ресурсов

### База данных

SQLite база данных с четырьмя основными таблицами:

- `tasks` - Задачи и напоминания
- `birthdays` - Дни рождения
- `user_settings` - Пользовательские настройки
- `daily_messages` - Отслеживание ежедневных сообщений

### Планировщик

APScheduler автоматически проверяет:

- Просроченные задачи (каждую минуту)
- Приближающиеся дни рождения (ежедневно в 09:00)
- Напоминания за день до событий

## 🔧 Разработка

### Требования для разработки

```bash
pip install -r requirements.txt
```

### Стиль кода

Проект следует:
- **PEP 8** - Python coding style guide
- **Type hints** - Аннотации типов для всех функций
- **Docstrings** - Документация для всех публичных методов

### Добавление новых функций

1. Создайте новый handler в `handlers/`
2. Зарегистрируйте router в `bot_main.py`
3. Добавьте необходимые сервисы в `services/`
4. Обновите клавиатуры в `keyboards/menu.py`

### Логирование

Бот использует Python logging:

```bash
import logging
logger = logging.getLogger(name)

logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка", exc_info=True)
```

Уровень логирования настраивается через `LOG_LEVEL` в `.env`

## 📝 Лицензия

Этот проект распространяется под лицензией GPLv3. Смотрите файл [LICENSE](LICENSE) для подробностей.

## 🤝 Контрибьюция

Вклад в проект приветствуется! Пожалуйста:

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📧 Контакты

Если у вас есть вопросы или предложения, создайте [Issue](https://github.com/JB-SelfCompany/TG_Assistant/issues).

---

<div align="center">

**Сделано с ❤️ для open-source сообщества**

⭐ Если проект вам помог, поставьте звезду на GitHub!

[Наверх](#-содержание)

</div>