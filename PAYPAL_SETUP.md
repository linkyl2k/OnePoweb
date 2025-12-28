# Настройка PayPal для OnePoweb

## Проблема
При нажатии на кнопку оплаты появляется ошибка: "Payment error. Try again or contact us"

## Причина
Переменные окружения PayPal не настроены или настроены неправильно.

## Решение

### 1. Получите учетные данные PayPal

#### Sandbox (Тестовая среда):
1. Перейдите на https://developer.paypal.com/
2. Войдите в свой аккаунт PayPal
3. Перейдите в "Dashboard" → "Apps & Credentials"
4. Выберите режим "Sandbox"
5. Создайте новое приложение или выберите существующее
6. Скопируйте:
   - **Client ID** 
   - **Secret**

#### Live (Продакшн):
1. Перейдите на https://developer.paypal.com/
2. Войдите в свой аккаунт PayPal
3. Перейдите в "Dashboard" → "Apps & Credentials"
4. Выберите режим "Live"
5. Создайте новое приложение или выберите существующее
6. Скопируйте:
   - **Client ID**
   - **Secret**

### 2. Настройте переменные окружения

Создайте файл `.env` в корне проекта (если его нет) или добавьте следующие строки:

```bash
# PayPal Configuration
PAYPAL_CLIENT_ID=your_client_id_here
PAYPAL_SECRET=your_secret_here
PAYPAL_MODE=sandbox  # или "live" для продакшна
```

### 3. Для деплоя на Render.com

1. Откройте свой проект на https://dashboard.render.com/
2. Перейдите в настройки сервиса
3. Найдите раздел "Environment Variables"
4. Добавьте следующие переменные:
   - `PAYPAL_CLIENT_ID` = ваш Client ID
   - `PAYPAL_SECRET` = ваш Secret
   - `PAYPAL_MODE` = `sandbox` или `live`

### 4. Перезапустите приложение

После добавления переменных окружения:
- Локально: перезапустите Flask (`Ctrl+C` и запустите снова)
- Render: автоматически перезапустится после сохранения переменных

### 5. Проверка

После настройки:
1. Откройте страницу оплаты
2. Должна появиться кнопка PayPal
3. При нажатии вы будете перенаправлены на страницу PayPal для оплаты
4. В логах сервера должны появиться сообщения типа:
   ```
   [PayPal] Creating subscription for plan: basic
   [PayPal] Found existing product: PROD-xxx
   [PayPal] Found existing plan: PLAN-xxx
   [PayPal] Creating subscription: ...
   [PayPal] Response status: 201
   ```

### 6. Тестирование в Sandbox

В режиме Sandbox используйте тестовые аккаунты PayPal:
1. Создайте тестовые аккаунты на https://developer.paypal.com/dashboard/accounts
2. Используйте тестовые учетные данные для оплаты

### Дополнительная информация

#### Проверка логов
Если ошибка все еще возникает, проверьте логи:
```bash
# В логах вы увидите:
[PayPal] Failed to get access token  # PayPal credentials не настроены
[PayPal] PAYPAL_CLIENT_ID configured: False
[PayPal] PAYPAL_SECRET configured: False
```

или

```bash
[PayPal] Failed to get access token: 401 - {"error":"..."}  # Неверные credentials
```

#### Настройка в коде уже выполнена:
- ✅ Улучшена обработка ошибок
- ✅ Добавлено подробное логирование
- ✅ Информативные сообщения об ошибках

## Контакты
Если проблема не решается, проверьте:
1. Правильность Client ID и Secret
2. Режим (sandbox/live) соответствует учетным данным
3. Приложение на PayPal имеет включенную функциональность "Subscriptions"

