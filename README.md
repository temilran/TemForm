# Web Forum

Учебный веб-форум, разработанный в рамках самостоятельной практики.  
Состоит из двух отдельных Flask-сервисов, взаимодействующих через JWT.

## Стек
- **Backend:** Python, Flask, Flask-SQLAlchemy
- **База данных:** PostgreSQL
- **Аутентификация:** JWT (PyJWT), 2FA через email (SMTP)
- **Окружение:** python-dotenv

## Функционал
- Регистрация и вход в аккаунт
- Двухфакторная аутентификация через email
- Ролевая система: owner / admin / user
- Создание, редактирование и удаление постов
- Лайки и комментарии к постам
- Лайки на комментарии

## Архитектура
Проект разделён на два сервиса:
- `auth-service` (порт 5000) — регистрация, вход, 2FA, выдача JWT
- `forum-service` (порт 5001) — посты, комментарии, лайки

## Запуск
1. Создай `.env` файл:

SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://postgres:password@localhost/users
EMAIL_SNR=your_email@gmail.com
EMAIL_PSW=your_app_password

2. Установи зависимости:

pip install -r requirements.txt

3. Запусти оба сервиса:

python auth/app.py
python forum/app.py


## Статус
В разработке 
