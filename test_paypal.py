#!/usr/bin/env python3
"""
Скрипт для тестирования настройки PayPal
Запустите: python test_paypal.py
"""
import os
import sys
import requests
import base64
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
PAYPAL_API_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"

def test_paypal_connection():
    """Тестирование подключения к PayPal API"""
    print("=" * 60)
    print("ПРОВЕРКА НАСТРОЙКИ PAYPAL")
    print("=" * 60)
    print()
    
    # Проверка переменных окружения
    print("1. Проверка переменных окружения:")
    print(f"   PAYPAL_MODE: {PAYPAL_MODE}")
    print(f"   PAYPAL_API_URL: {PAYPAL_API_URL}")
    print(f"   PAYPAL_CLIENT_ID: {'✅ Настроено' if PAYPAL_CLIENT_ID else '❌ НЕ НАСТРОЕНО'}")
    print(f"   PAYPAL_SECRET: {'✅ Настроено' if PAYPAL_SECRET else '❌ НЕ НАСТРОЕНО'}")
    print()
    
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        print("❌ ОШИБКА: PayPal учетные данные не настроены!")
        print()
        print("Для настройки:")
        print("1. Создайте файл .env в корне проекта")
        print("2. Добавьте следующие строки:")
        print("   PAYPAL_CLIENT_ID=ваш_client_id")
        print("   PAYPAL_SECRET=ваш_secret")
        print("   PAYPAL_MODE=sandbox")
        print()
        print("Подробнее см. файл PAYPAL_SETUP.md")
        sys.exit(1)
    
    # Тестирование получения access token
    print("2. Тестирование получения access token:")
    try:
        auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(
            f"{PAYPAL_API_URL}/v1/oauth2/token",
            headers=headers,
            data="grant_type=client_credentials",
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"   ✅ Access token получен успешно")
            print(f"   Token type: {token_data.get('token_type')}")
            print(f"   Expires in: {token_data.get('expires_in')} seconds")
            return access_token
        else:
            print(f"   ❌ ОШИБКА получения access token!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ ОШИБКА: {str(e)}")
        return None

def test_paypal_products(access_token):
    """Тестирование получения продуктов"""
    print()
    print("3. Проверка продуктов PayPal:")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{PAYPAL_API_URL}/v1/catalogs/products",
            headers=headers,
            params={"page_size": 10, "total_required": "yes"},
            timeout=10
        )
        
        if response.status_code == 200:
            products_data = response.json()
            products = products_data.get("products", [])
            print(f"   ✅ Найдено продуктов: {len(products)}")
            
            onepoweb_found = False
            for product in products:
                if product.get("name") == "OnePoweb":
                    onepoweb_found = True
                    print(f"   ✅ Продукт 'OnePoweb' найден: {product.get('id')}")
                    break
            
            if not onepoweb_found and len(products) > 0:
                print(f"   ⚠️  Продукт 'OnePoweb' не найден, будет создан автоматически")
            elif not onepoweb_found:
                print(f"   ℹ️  Нет продуктов, 'OnePoweb' будет создан автоматически")
        else:
            print(f"   ❌ ОШИБКА получения продуктов!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ ОШИБКА: {str(e)}")

def test_paypal_plans(access_token):
    """Тестирование получения планов"""
    print()
    print("4. Проверка планов подписок:")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{PAYPAL_API_URL}/v1/billing/plans",
            headers=headers,
            params={"page_size": 10},
            timeout=10
        )
        
        if response.status_code == 200:
            plans_data = response.json()
            plans = plans_data.get("plans", [])
            print(f"   ✅ Найдено планов: {len(plans)}")
            
            basic_found = False
            pro_found = False
            
            for plan in plans:
                plan_name = plan.get("name", "")
                if "OnePoweb BASIC" in plan_name:
                    basic_found = True
                    print(f"   ✅ План 'BASIC' найден: {plan.get('id')} (status: {plan.get('status')})")
                elif "OnePoweb PRO" in plan_name:
                    pro_found = True
                    print(f"   ✅ План 'PRO' найден: {plan.get('id')} (status: {plan.get('status')})")
            
            if not basic_found:
                print(f"   ℹ️  План 'BASIC' не найден, будет создан при первой оплате")
            if not pro_found:
                print(f"   ℹ️  План 'PRO' не найден, будет создан при первой оплате")
        else:
            print(f"   ❌ ОШИБКА получения планов!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ ОШИБКА: {str(e)}")

if __name__ == "__main__":
    access_token = test_paypal_connection()
    
    if access_token:
        test_paypal_products(access_token)
        test_paypal_plans(access_token)
        print()
        print("=" * 60)
        print("✅ НАСТРОЙКА PAYPAL УСПЕШНА!")
        print("=" * 60)
        print()
        print("Теперь вы можете протестировать оплату через веб-интерфейс.")
        print("В режиме sandbox используйте тестовые аккаунты PayPal.")
    else:
        print()
        print("=" * 60)
        print("❌ ОШИБКА НАСТРОЙКИ PAYPAL")
        print("=" * 60)
        print()
        print("Проверьте:")
        print("1. Правильность PAYPAL_CLIENT_ID и PAYPAL_SECRET")
        print("2. Соответствие PAYPAL_MODE (sandbox/live) вашим учетным данным")
        print("3. Наличие прав API для вашего приложения на PayPal")
        print()
        print("Подробнее см. файл PAYPAL_SETUP.md")

