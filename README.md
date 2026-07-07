# airDos

Бэкенд-приложение на FastAPI с аутентификацией через Email PIN-код (OTP).

## Структура проекта

```text
airdos/
├── app/
│   ├── core/          # config.py, database.py, security.py
│   ├── models/        # SQLAlchemy модели
│   ├── schemas/       # Pydantic схемы
│   ├── crud/          # Логика работы с БД
│   ├── api/           # Роутеры
│   └── main.py        # Точка входа FastAPI
├── migrations/        # Миграции Alembic
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## Быстрый запуск через Docker Compose

1. Скопируйте переменные окружения:

   ```bash
   cp .env.example .env
   ```

2. Запустите приложение с базой данных:

   ```bash
   docker compose up --build
   ```

   Swagger UI будет доступен по адресу: http://localhost:8000/docs

3. Для локального тестирования почты добавьте сервис MailHog:

   ```bash
   docker compose --profile mailhog up --build
   ```

   Письма будут доступны в веб-интерфейсе MailHog: http://localhost:8025

   При использовании MailHog установите в `.env`:

   ```env
   MAILHOG_ENABLED=true
   MAIL_SERVER=airdos-mailhog
   MAIL_PORT=1025
   MAIL_USERNAME=airdos
   MAIL_PASSWORD=airdos
   MAIL_FROM="noreply@airdos.example.com"
   MAIL_STARTTLS=false
   MAIL_SSL_TLS=false
   ```

## Локальное тестирование с реальным SMTP (Gmail)

Если вы хотите получать реальные письма на Gmail, отредактируйте файл `.env` и замените значения на свои:

```env
MAIL_USERNAME=your-email@gmail.com      # Ваш Gmail адрес
MAIL_PASSWORD=your-app-password         # Пароль приложения Gmail (16 символов, без пробелов)
MAIL_FROM=your-email@gmail.com          # Тот же Gmail адрес
MAIL_PORT=587                           # Порт Gmail для STARTTLS
MAIL_SERVER=smtp.gmail.com            # SMTP-сервер Gmail
MAIL_STARTTLS=true                    # Использовать STARTTLS (безопасное соединение)
MAIL_SSL_TLS=false                    # Не использовать SSL/TLS на 465 порту
```

### Как получить пароль приложения Gmail (App Password)

1. Включите **двухфакторную аутентификацию** (2FA) для аккаунта Google: https://myaccount.google.com/signinoptions/two-step-verification
2. Перейдите на страницу паролей приложений: https://myaccount.google.com/apppasswords
3. Введите название приложения, например `airDos-local`
4. Google покажет 16-значный пароль, например: `abcd efgh ijkl mnop`
5. Скопируйте его **без пробелов** в `.env`:

```env
MAIL_PASSWORD=abcdefghijklmnop
```

**Важно:** используйте именно пароль приложения, а не свой обычный пароль от Gmail. Основной пароль не будет работать с SMTP.

## Эндпоинты API

- `POST /auth/register` — регистрация пользователя
- `POST /auth/verify-code` — проверка 6-значного PIN-кода
- `POST /auth/resend-code` — повторная отправка кода
- `POST /auth/login` — получение JWT-токена (OAuth2PasswordBearer)
- `GET /users/me` — профиль текущего пользователя
- `GET /healthcheck` — проверка работоспособности
