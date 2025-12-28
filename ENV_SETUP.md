# Пример файла .env для OnePoweb

Создайте файл `.env` в корне проекта со следующим содержимым:

```bash
# ====== PayPal Configuration ======
# Получите эти данные на https://developer.paypal.com/
PAYPAL_CLIENT_ID=your_paypal_client_id_here
PAYPAL_SECRET=your_paypal_secret_here
PAYPAL_MODE=sandbox  # sandbox для тестирования, live для продакшн

# ====== Email Configuration (for notifications) ======
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password_here

# ====== Other settings ======
SECRET_KEY=your_secret_key_for_flask_sessions
```

## Как получить PayPal credentials

1. Перейдите на https://developer.paypal.com/
2. Войдите в аккаунт
3. Dashboard → Apps & Credentials
4. Выберите режим (Sandbox или Live)
5. Создайте приложение или используйте существующее
6. Скопируйте Client ID и Secret

Подробнее см. файл `PAYPAL_SETUP.md`

