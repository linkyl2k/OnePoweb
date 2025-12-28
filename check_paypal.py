"""
Простой тест PayPal настройки
"""
import os

print("=" * 60)
print("ПРОВЕРКА НАСТРОЙКИ PAYPAL")
print("=" * 60)
print()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")

print("Переменные окружения:")
print(f"  PAYPAL_CLIENT_ID: {'Настроено (' + str(len(PAYPAL_CLIENT_ID)) + ' символов)' if PAYPAL_CLIENT_ID else 'НЕ НАСТРОЕНО'}")
print(f"  PAYPAL_SECRET: {'Настроено (' + str(len(PAYPAL_SECRET)) + ' символов)' if PAYPAL_SECRET else 'НЕ НАСТРОЕНО'}")
print(f"  PAYPAL_MODE: {PAYPAL_MODE}")
print()

if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
    print("❌ ОШИБКА: PayPal не настроен!")
    print()
    print("Для настройки см. файл: ИСПРАВЛЕНИЕ_ОПЛАТЫ.md")
else:
    print("✅ PayPal учетные данные настроены")
    print()
    print("Для полного теста запустите: python test_paypal.py")

