# Telegram бот для изучения Python 🐍

🤖 Этот телеграм бот предлагает пользователям решать задачи различной сложности: easy, medium и hard. После выбора уровня сложности, пользователь получает задачу, решает её и отправляет своё решение в бот. Бот проверяет код, запускает его на клиентском сервере и возвращает результаты.

## 📜 Функционал
**Выбор уровня сложности**: Пользователь может выбрать из 3 уровней сложности.  
**Проверка решения**: Бот запускает пользовательский код и проверяет его на тестах.  
**Обратная связь**: Если решение верное, бот сообщит, что код прошел 100% тестов. В случае ошибок, бот отобразит информацию о том, сколько тестов прошло успешно и какие произошли ошибки.

## 🔧 Стек технологий

- **FastAPI** — фреймворк для создания асинхронных веб-приложений и API.  
- **aiogram** — библиотека для работы с Telegram Bot API, поддерживающая асинхронное взаимодействие.  
- **Python** — основной язык программирования для разработки бота.  
- **pytest** — фреймворк для тестирования кода пользователя и проверки решений.  
- **asyncpg** — асинхронный драйвер PostgreSQL для работы с базой данных (если требуется хранение задач или решений).  
- **Redis** — хранилище данных в памяти для кэширования и управления состоянием сессий.  
- **SQLAlchemy** — ORM для работы с базой данных при необходимости.  
- **Pydantic** — валидация данных и управление конфигурацией.  


###  📂 Структура проекта
python_learning_bot/  
├── alembic/                          # Миграции базы данных  
├── config/                          # Конфигурации  
│   ├── env.example               # Пример конфигурации среды  
│   ├── logging.conf.yml          # Конфигурация логирования  
│   ├── settings.py               # Настройки Alembic  
├── prometheus/    # Конфигурация Prometheus  
├── scripts/                  # Скрипты  
│   ├── limiteduser_delete.py  # Удаление ограниченного юзера  
│   ├── load_fixture.py  
│   ├── migrate.py  # миграция в БД (для тестов)  
│   ├── restricted_dir_usr_create.py # создание ограниченной директории и пользователя  
│   ├── startup.sh                # Скрипт запуска  
├── consumer/                         # Получатель  
│   ├── api/                          # API потребителя  
│   │   ├── tech/                     # Технические файлы API,  метрики  
│   ├── handlers/                     # Обработчики потребителя  
│   │   ├── task.py # Принимает RabbitMQ messages  
│   ├── schema/                       # Схемы  
│   ├── __main__.py # Файл запуска приложения consumer  
│   ├── app.py  
│   ├── logger.py # Логгер consumer  
│   ├── metrics_init.py # Метрики prometheus  
│   ├── utils.py # Вспомогательные утилиты  
│   ├── web_app.py # Fastapi приложение consumer  
├── db/                               # База данных  
├── src/                              # Исходные файлы проекта  
│   ├── api/                          # API проекта  
│   │   ├── tech/                     # Технические файлы API, метрики  
│   │   ├── tg/                       # Роутер для Webhook  
│   ├── handlers/                 # Обработчики API  
│   │   ├── admin_handlers/       # Обработчики администратора  
│   │   ├── user_handlers/        # Обработчики пользователя  
│   ├── keyboards/                # Клавиатуры (inline-кнопки)  
│   ├── middlewares/              # Middleware  
│   ├── states/                   # Состояния  
│   ├── app.py                    # Основной файл приложения  
│   ├── bg_task.py                # Фоновые задачи (хранение)  
│   ├── bot.py                    # Бот  
│   ├── logger.py                 # Логгер backend  
│   ├── metrics_init.py           # Инициализация метрик prometheus  
│   ├── rabbit_initializer.py     # Инициализатор RabbitMQ  
│   ├── utils.py                  # Утилиты для backend  
│   ├── tests/                        # Тесты  
├── .flake8                           # Конфигурация flake8  
├── .gitignore                        # Игнорируемые файлы  
├── alembic.ini                       # Конфигурация Alembic  
├── docker-compose.yml                # Docker Compose файл  
├── Dockerfile                        # Dockerfile  
├── poetry.lock                       # Lock файл Poetry  
├── pyproject.toml                    # Конфигурация Poetry  
├── README.md                         # Файл с описанием проекта  
├── test_tasks.ddl                    # DDL для тестовых задач  





## 🏃💨 Running
Для начала вставьте свой токен бота в .env.example, а также измените имя этого файла на просто .env  
В config/settings.py вы можете найти строку с env_file, туда вставьте свой путь (написан #)
**1st Teerminal**
```bash
git clone https://github.com/Rubsun/python_learning_bot.git
cd python_learning_bot
python3 -m venv venv
source venv/bin/activate
poetry install
```
В первом терминале мы создали виртуальное окружение, важно в дальнейшем во **всех** терминалах использовать его,
для активации нужно прописывать:
```bash
source venv/bin/activate
```
**2nd Terminal**
```bash
docker compose up
```
**3rd Terminal**
```bash
alembic upgrade head
psql -h localhost -p 5555 -U postgres postgres -f test_tasks.ddl
```

**УРААА, ПОДГОТОВКА К ЗАПУСКУ ПРОШЛА УСПЕШНО!**  
**Дальнейшие шаги выполняются при каждом запуске бота!**  

В следующем терминале будет использование ngrok для поднятия бесплатного сервера в Интернете для webhook
Инструкция по установке доступна на его **официальном сайте**: https://ngrok.com/
**4th Terminal**
```bash
ngrok http 8001
```
После этого в 4 терминале вам покажется одна строчка где написано примерно такое:  
**https://#some_symbols.ngrok-free.app -> http://localhost:8001**  
первую ссылку (c ngrok-free.app) вам нужно скопировать и вставить в .env вместо #YOUR_NGROK_URL  

**5th Terminal**
```bash
pythom -m consumer.__main__
```

**6th Terminal**
```bash
sudo su
```
Вводите пароль для входа в консоль с root правами (нужно для безопасного запуска кодов пользователей)
```bash
source venv/bin/activate
python scripts/restricted_dir_usr_create.py
python -m src.app
```

**ГОТОВО! МОЖЕТЕ ПЕРЕХОДИТЬ НА ВАШЕГО БОТА И РАБОТАТЬ С НИМ!** Также на http://localhost:9090 у вас лежит prometheus,
на котором вы сможете проседить за некоторыми метриками и состоянием приложения!