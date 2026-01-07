# -*- coding: utf-8 -*-
import io
import json
import string
import secrets
import base64
import gzip
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

# ====== Email Configuration ======
CONTACT_EMAIL = "onepoweb@gmail.com"  # כתובת לקבלת הודעות מהטופס
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")  # Gmail address
SMTP_PASS = os.getenv("SMTP_PASS", "")  # App password (not regular password!)

# ====== PayPal Configuration ======
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
PAYPAL_API_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"


# Prices in USD
PLAN_PRICES = {
    "basic": {"usd": 15},
    "pro": {"usd": 20}
}

# Список доступных валют (упорядочены по популярности)
AVAILABLE_CURRENCIES = {
    # Основные мировые валюты
    "USD": {"symbol": "$", "name": "USD", "code": "USD", "display": "$", "label_he": "דולר", "label_en": "Dollar", "label_ru": "Доллар", "flag": "🇺🇸"},
    "EUR": {"symbol": "€", "name": "EUR", "code": "EUR", "display": "€", "label_he": "אירו", "label_en": "Euro", "label_ru": "Евро", "flag": "🇪🇺"},
    "GBP": {"symbol": "£", "name": "GBP", "code": "GBP", "display": "£", "label_he": "פאונד", "label_en": "Pound", "label_ru": "Фунт", "flag": "🇬🇧"},
    "JPY": {"symbol": "¥", "name": "JPY", "code": "JPY", "display": "¥", "label_he": "ין", "label_en": "Yen", "label_ru": "Йена", "flag": "🇯🇵"},
    "CNY": {"symbol": "¥", "name": "CNY", "code": "CNY", "display": "¥", "label_he": "יואן", "label_en": "Yuan", "label_ru": "Юань", "flag": "🇨🇳"},
    "INR": {"symbol": "₹", "name": "INR", "code": "INR", "display": "₹", "label_he": "רופי", "label_en": "Rupee", "label_ru": "Рупия", "flag": "🇮🇳"},
    "CAD": {"symbol": "C$", "name": "CAD", "code": "CAD", "display": "C$", "label_he": "דולר קנדי", "label_en": "Canadian Dollar", "label_ru": "Канадский доллар", "flag": "🇨🇦"},
    "AUD": {"symbol": "A$", "name": "AUD", "code": "AUD", "display": "A$", "label_he": "דולר אוסטרלי", "label_en": "Australian Dollar", "label_ru": "Австралийский доллар", "flag": "🇦🇺"},
    "CHF": {"symbol": "CHF", "name": "CHF", "code": "CHF", "display": "CHF", "label_he": "פרנק שוויצרי", "label_en": "Swiss Franc", "label_ru": "Швейцарский франк", "flag": "🇨🇭"},
    "ILS": {"symbol": "₪", "name": "ILS", "code": "ILS", "display": "₪", "label_he": "שקל", "label_en": "Shekel", "label_ru": "Шекель", "flag": "🇮🇱"},
    "RUB": {"symbol": "₽", "name": "RUB", "code": "RUB", "display": "₽", "label_he": "רובל", "label_en": "Ruble", "label_ru": "Рубль", "flag": "🇷🇺"},
    # Европейские валюты
    "PLN": {"symbol": "zł", "name": "PLN", "code": "PLN", "display": "zł", "label_he": "זלוטי", "label_en": "Zloty", "label_ru": "Злотый", "flag": "🇵🇱"},
    "SEK": {"symbol": "kr", "name": "SEK", "code": "SEK", "display": "kr", "label_he": "כתר שוודי", "label_en": "Swedish Krona", "label_ru": "Шведская крона", "flag": "🇸🇪"},
    "NOK": {"symbol": "kr", "name": "NOK", "code": "NOK", "display": "kr", "label_he": "כתר נורווגי", "label_en": "Norwegian Krone", "label_ru": "Норвежская крона", "flag": "🇳🇴"},
    "DKK": {"symbol": "kr", "name": "DKK", "code": "DKK", "display": "kr", "label_he": "כתר דני", "label_en": "Danish Krone", "label_ru": "Датская крона", "flag": "🇩🇰"},
    "CZK": {"symbol": "Kč", "name": "CZK", "code": "CZK", "display": "Kč", "label_he": "קורונה צ'כית", "label_en": "Czech Koruna", "label_ru": "Чешская крона", "flag": "🇨🇿"},
    "HUF": {"symbol": "Ft", "name": "HUF", "code": "HUF", "display": "Ft", "label_he": "פורינט", "label_en": "Forint", "label_ru": "Форинт", "flag": "🇭🇺"},
    # Валюты СНГ
    "UAH": {"symbol": "₴", "name": "UAH", "code": "UAH", "display": "₴", "label_he": "גריבנה", "label_en": "Hryvnia", "label_ru": "Гривна", "flag": "🇺🇦"},
    "KZT": {"symbol": "₸", "name": "KZT", "code": "KZT", "display": "₸", "label_he": "טנגה", "label_en": "Tenge", "label_ru": "Тенге", "flag": "🇰🇿"},
    "KGS": {"symbol": "сом", "name": "KGS", "code": "KGS", "display": "сом", "label_he": "סום", "label_en": "Som", "label_ru": "Сом", "flag": "🇰🇬"},
}

def get_currency(lang: str = None) -> dict:
    """
    Возвращает информацию о валюте пользователя.
    Сначала проверяет выбор пользователя в сессии, затем язык по умолчанию.
    Returns: {"symbol": "₪", "name": "ILS", "code": "ILS"}
    """
    from flask import session
    
    # Проверяем выбор пользователя в сессии
    user_currency = session.get("currency")
    if user_currency and user_currency in AVAILABLE_CURRENCIES:
        return AVAILABLE_CURRENCIES[user_currency]
    
    # Если язык не передан, получаем из сессии
    if lang is None:
        lang = get_language()
    
    # Валюты по умолчанию в зависимости от языка
    default_currencies = {
        "he": "ILS",  # Шекели для иврита
        "ru": "RUB",  # Рубли для русского (можно изменить на другую валюту СНГ)
        "en": "USD"   # Доллары для английского
    }
    
    default_code = default_currencies.get(lang, "USD")
    return AVAILABLE_CURRENCIES.get(default_code, AVAILABLE_CURRENCIES["USD"])

def get_currency_by_code(currency_code: str) -> dict:
    """
    Возвращает информацию о валюте по коду.
    Returns: {"symbol": "₪", "name": "ILS", "code": "ILS"}
    """
    if currency_code and currency_code in AVAILABLE_CURRENCIES:
        return AVAILABLE_CURRENCIES[currency_code]
    return AVAILABLE_CURRENCIES.get("USD", {"symbol": "$", "name": "USD", "code": "USD"})

def send_contact_email(name: str, email: str, message: str, subject: str = "general"):
    """שליחת הודעת צור קשר למייל"""
    
    # מיפוי נושאים
    subject_labels = {
        "general": "שאלה כללית",
        "support": "תמיכה טכנית",
        "billing": "חיוב ותשלומים",
        "feature": "בקשת פיצ'ר",
        "bug": "דיווח על באג",
        "partnership": "שיתוף פעולה"
    }
    subject_label = subject_labels.get(subject, subject)
    
    # אם אין הגדרות SMTP - רק מדפיסים ללוג
    if not SMTP_USER or not SMTP_PASS:
        print(f"📧 [Contact Form] From: {name} <{email}>")
        print(f"📧 Subject: {subject_label}")
        print(f"📧 Message: {message}")
        print("⚠️ SMTP not configured - email not sent (add SMTP_USER and SMTP_PASS to .env)")
        return
    
    # יצירת הודעה
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = CONTACT_EMAIL
    msg['Subject'] = f"📩 [{subject_label}] הודעה מ-{name}"
    msg['Reply-To'] = email
    
    body = f"""
🔔 הודעה חדשה מטופס צור קשר

━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 שם: {name}
✉️ אימייל: {email}
📋 נושא: {subject_label}
━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 הודעה:
{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━
נשלח מ-OnePoweb Contact Form
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # שליחה
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    
    print(f"✅ Email sent to {CONTACT_EMAIL} from {name} <{email}>")
FORCE_AI = os.getenv("FORCE_AI", "1") == "1"  # פותח AI לכל החבילות בזמן פיתוח
import pandas as pd
import numpy as np
from flask import Flask, g
import os, sqlite3
import re

# --- הצפנה מאובטחת של נתונים ---
try:
    from cryptography.fernet import Fernet
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    if not ENCRYPTION_KEY:
        # יצירת מפתח חדש אם לא קיים (שמור את זה ב-.env בפרודקשן!)
        ENCRYPTION_KEY = Fernet.generate_key().decode()
        print(f"⚠️ חסר ENCRYPTION_KEY ב-.env! מפתח זמני: {ENCRYPTION_KEY}")
    _fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
    ENCRYPTION_AVAILABLE = True
except Exception as e:
    print(f"⚠️ הצפנה לא זמינה: {e}")
    ENCRYPTION_AVAILABLE = False
    _fernet = None

def encrypt_data(data: bytes) -> bytes:
    """הצפנת נתונים עם Fernet + דחיסה"""
    if not ENCRYPTION_AVAILABLE or not _fernet:
        return base64.b64encode(gzip.compress(data))
    compressed = gzip.compress(data)
    return _fernet.encrypt(compressed)

def decrypt_data(encrypted: bytes) -> bytes:
    """פענוח נתונים"""
    if not ENCRYPTION_AVAILABLE or not _fernet:
        return gzip.decompress(base64.b64decode(encrypted))
    decrypted = _fernet.decrypt(encrypted)
    return gzip.decompress(decrypted)

# --- היפוך תווים "קשוח" + החלפת סוגריים ---
# --- היפוך תווים "קשוח" + החלפת סוגריים, בלי להפוך סדר שורות ---
_PARENS_SWAP = str.maketrans("()[]{}", ")(][}{")

def flip_text_strict(s: str) -> str:
    """
    הופך תווים לכל שורה בנפרד (כולל החלפת סוגריים),
    אבל משאיר את סדר השורות *בדיוק* כמו בקלט.
    """
    if not s:
        return ""
    lines = str(s).split('\n')  # שומר סדר
    flipped = [(ln.translate(_PARENS_SWAP))[::-1] for ln in lines]
    return '\n'.join(flipped)   # אותו סדר שורות





# --- OpenAI init (פעם אחת בלבד) ---
import os, json, time, traceback
from openai import OpenAI

OPENAI_KEY   = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
USE_AI_ENV   = os.getenv("USE_AI", "1") == "1"      # 1=מופעל
FORCE_AI     = os.getenv("FORCE_AI", "0") == "1"    # 1=לפתוח לכולם בזמן פיתוח

_openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None




app = Flask(__name__)  # <<< כאן Flask נוצר

# =============================================================================
# 🌍 Система переводов (i18n)
# =============================================================================

# Словари переводов
TRANSLATIONS = {
    "he": {  # Иврит (по умолчанию)
        # Навигация
        "nav_home": "ניתוח",
        "nav_plans": "תוכניות ומחירים",
        "nav_about": "למה OnePoweb",
        "nav_contact": "צור קשר",
        "nav_login": "התחברות",
        "nav_signup": "הרשמה",
        "nav_profile": "הפרופיל שלי",
        "nav_dashboard": "לוח בקרה",
        "nav_logout": "התנתקות",
        
        # Главная страница
        "hero_new": "חדש",
        "hero_title": "נתח את הנתונים שלך",
        "hero_title_gradient": "בלחיצה אחת",
        "hero_subtitle": "העלה דוח קופה ותקבל גרפים מקצועיים, תובנות AI והשוואת תקופות",
        "upload_file": "העלאת קובץ",
        "drag_drop": "גרור קובץ או לחץ לבחירה",
        "select_file": "בחר קובץ",
        "analyze": "נתח דוח",
        
        # Планы
        "plan_free": "חינם",
        "plan_basic": "Basic",
        "plan_pro": "Pro",
        "upgrade": "שדרג",
        "current_plan": "התוכנית הנוכחית",
        
        # Общие
        "loading": "טוען...",
        "error": "שגיאה",
        "success": "הצלחה",
        "save": "שמור",
        "cancel": "ביטול",
        "delete": "מחק",
        "edit": "ערוך",
        "close": "סגור",
        "back": "חזור",
        "next": "הבא",
        "previous": "הקודם",
        "submit": "שלח",
        "download": "הורד",
        "upload": "העלה",
        
        # Форма загрузки
        "select_graphs": "בחירת גרפים",
        "select_graphs_desc": "סמן את הגרפים שברצונך לייצר",
        "time_trends": "זמנים ומגמות",
        "sales_by_hour": "מכירות לפי שעה",
        "sales_by_weekday": "מכירות לפי יום בשבוע",
        "heatmap": "מפת חום (שעה×יום)",
        "daily_sales": "מכירות יומיות",
        "products": "מכירות ומוצרים",
        "top_quantity": "Top 10 כמות",
        "top_revenue": "Top 10 הכנסות",
        "payment_methods": "אמצעי תשלום",
        "advanced": "מתקדם",
        "avg_ticket": "ממוצע קנייה לפי שעה",
        "weekend_compare": "סופ\"ש מול ימי חול",
        "period_type": "סוג תקופה",
        "month": "חודש",
        "week": "שבוע",
        "day": "יום",
        "custom": "מותאם אישית",
        "period_name": "שם תקופה (אופציונלי)",
        "hour_range": "טווח שעות",
        "to": "עד",
        "analyze_button": "נתח דוח",
        "popular": "פופולרי",
        "new": "חדש",
        
        # Авторизация
        "login_title": "התחברות",
        "login_email": "אימייל או שם משתמש",
        "login_password": "סיסמה",
        "login_button": "התחבר",
        "login_forgot": "שכחת סיסמה?",
        "login_no_account": "אין לך חשבון?",
        "signup_title": "הרשמה",
        "signup_email": "אימייל",
        "signup_username": "שם משתמש",
        "signup_password": "סיסמה",
        "signup_confirm": "אימות סיסמה",
        "signup_terms": "אני מסכים לתנאי השימוש",
        "signup_button": "הירשם",
        "signup_have_account": "יש לך כבר חשבון?",
        "password_requirements": "דרישות סיסמה:",
        "password_length": "8-32 תווים",
        "password_english": "אותיות אנגליות בלבד",
        "password_upper": "אות גדולה (A-Z)",
        "password_digit": "ספרה (0-9)",
        "security_note": "החיבור מאובטח ומוצפן",
        
        # Профиль
        "profile_title": "הפרופיל שלי",
        "profile_email": "אימייל",
        "profile_username": "שם משתמש",
        "profile_plan": "תוכנית",
        "profile_edit": "ערוך פרופיל",
        "profile_change_password": "שנה סיסמה",
        "profile_current_status": "סטטוס נוכחי",
        "profile_active": "פעיל",
        "profile_cancelled": "בוטל",
        "profile_no_subscription": "אין מנוי",
        "profile_trial_available": "נסה PRO חינם ל-2 ימים!",
        "profile_trial_desc": "קבל גישה מלאה לכל הפיצ'רים של Pro ל-2 ימים. אחר כך תתחיל מנוי PRO. בלי כרטיס אשראי",
        "profile_start_trial": "התחל תקופת ניסיון",
        
        # Profile Edit
        "profile_edit_title": "עריכת פרופיל",
        "profile_personal_details": "פרטים אישיים",
        "profile_first_name": "שם פרטי",
        "profile_last_name": "שם משפחה",
        "profile_username_label": "שם משתמש (לכניסה מהירה)",
        "profile_username_hint": "4-20 תווים: אותיות אנגליות וספרות בלבד",
        "profile_password_section": "שינוי סיסמה",
        "profile_password_optional": "השאר ריק אם לא רוצה לשנות",
        "profile_new_password": "סיסמה חדשה",
        "profile_confirm_password": "אימות סיסמה",
        "profile_password_requirements": "דרישות סיסמה:",
        "profile_password_length": "8-32 תווים",
        "profile_password_english": "אותיות אנגליות בלבד",
        "profile_password_upper": "אות גדולה (A-Z)",
        "profile_password_digit": "ספרה (0-9)",
        "profile_passwords_match": "הסיסמאות תואמות",
        "profile_passwords_no_match": "הסיסמאות לא תואמות",
        "profile_email_verified": "אימייל מאומת",
        "profile_email_not_verified": "אימייל לא מאומת",
        "profile_resend_verification": "שלח שוב",
        "profile_save_changes": "שמור שינויים",
        "profile_cancel": "ביטול",
        "profile_registered": "נרשמת",
        "profile_data_protected": "הנתונים שלך מוגנים ומוצפנים",
        
        # Flash сообщения
        "msg_login_required": "יש להתחבר קודם",
        "msg_login_success": "התחברת בהצלחה!",
        "msg_login_failed": "אימייל/סיסמה שגויים",
        "msg_signup_success": "נרשמת בהצלחה! בדוק את האימייל שלך לאימות",
        "msg_signup_failed": "שגיאה בהרשמה",
        "msg_logout": "התנתקת בהצלחה",
        "msg_file_uploaded": "קובץ הועלה בהצלחה",
        "msg_file_error": "שגיאה בהעלאת קובץ",
        "msg_trial_started": "תקופת ניסיון הופעלה! 2 ימים חינם - אחר כך תהיה מנוי PRO",
        "msg_trial_used": "כבר ניצלת את תקופת הניסיון",
        "msg_subscription_active": "המנוי הופעל בהצלחה!",
        "msg_subscription_cancelled": "המנוי בוטל",
        "msg_profile_updated": "הפרופיל עודכן בהצלחה",
        "msg_fill_name": "נא למלא שם ושם משפחה",
        "msg_username_required": "שם משתמש הוא שדה חובה",
        "msg_username_length": "שם משתמש חייב להיות בין 4-20 תווים",
        "msg_username_format": "שם משתמש יכול להכיל רק אותיות אנגליות וספרות",
        "msg_username_taken": "שם משתמש זה כבר תפוס",
        "msg_password_mismatch": "האימות לא תואם את הסיסמה החדשה",
        
        # Ошибки
        "error_404": "דף לא נמצא",
        "error_403": "אין הרשאה",
        "error_500": "שגיאת שרת",
        "error_generic": "משהו השתבש",
        
        # Results
        "results_title": "תוצאות הניתוח",
        "results_upload_new": "העלה דוח חדש",
        "results_download_pdf": "הורדת PDF",
        "results_no_graphs": "אין גרפים להצגה. חזור לעמוד הראשי והעלה דוח חדש.",
        "results_no_graphs_reload": "גרפים לא נמצאו. מפנים ללוח הבקרה שם תוכל לראות דוחות שמורים.",
        "results_summary": "סיכום הניתוח",
        "results_summary_desc": "תובנות מפתח מהדוח שלך",
        "results_upgrade_banner": "רוצה לראות גרפים וניתוח מתקדם?",
        "results_upgrade_desc": "שדרג לתוכנית Basic או Pro לראות את כל הגרפים והנתונים",
        "results_basic_graphs": "Basic - רק גרפים",
        "results_pro_ai": "Pro - כולל AI",
        "results_try_free": "נסה 2 ימים חינם - אחר כך מנוי PRO",
        "results_action_plan": "תוכנית פעולה מומלצת",
        "results_action_desc": "פעולות ספציפיות על סמך הניתוח שלך",
        "results_how_to": "איך לעשות זאת?",
        "results_roi_potential": "פוטנציאל שיפור",
        "results_roi_monthly": "רווח חודשי פוטנציאלי",
        "results_roi_theoretical": "ROI תיאורטי",
        "results_roi_estimate": "הערכה בלבד",
        "results_roi_depends": "תלוי בפעולות שלך",
        "results_more_recommendations": "עוד {count} המלצות",
        "results_ai_insights": "יש לנו {count} המלצות AI עבורך!",
        "results_upgrade_for_ai": "שדרג לתוכנית Pro לקבלת תוכנית פעולה מותאמת אישית",
        "results_upgrade_to_pro": "שדרג ל-Pro",
        "results_download_image": "הורד תמונה",
        
        # Checkout
        "checkout_order_summary": "סיכום ההזמנה",
        
        # Get Started / Onboarding
        "nav_get_started": "התחל",
        "get_started_title": "להכיר אותך...",
        "get_started_subtitle": "עזור לנו להתאים את החוויה שלך",
        "get_started_q1_title": "כמה סניפים יש לעסק שלך?",
        "get_started_q1_desc": "זה עוזר לנו להתאים תובנות במיוחד לקנה המידה של העסק שלך",
        "get_started_location_single": "יחיד",
        "get_started_q2_title": "באיזו תעשייה אתה?",
        "get_started_q2_desc": "נספק המלצות ספציפיות לתעשייה",
        "get_started_q3_title": "מה המטרה העיקרית שלך?",
        "get_started_q3_desc": "בואו נתמקד במה שהכי חשוב לך",
        "get_started_industry_restaurant": "מסעדה/קפה",
        "get_started_industry_retail": "קמעונאות",
        "get_started_industry_services": "שירותים",
        "get_started_industry_ecommerce": "מסחר אלקטרוני",
        "get_started_industry_healthcare": "בריאות",
        "get_started_industry_other": "אחר",
        "get_started_goal_revenue": "הגברת הכנסות",
        "get_started_goal_revenue_desc": "הגדל את המכירות וההכנסות שלך",
        "get_started_goal_operations": "אופטימיזציה של פעולות",
        "get_started_goal_operations_desc": "שיפור יעילות והפחתת עלויות",
        "get_started_goal_customers": "הבנת לקוחות",
        "get_started_goal_customers_desc": "קבל תובנות על התנהגות קונים",
        "get_started_goal_performance": "מעקב ביצועים",
        "get_started_goal_performance_desc": "ניטור מדדי KPI ומטריקות",
        "get_started_skip": "דלג לעת עתה →",
        "get_started_back": "חזור",
        "get_started_next": "הבא",
        "get_started_continue": "המשך",
        
        # Contact
        "contact_sent": "ההודעה נשלחה בהצלחה! נחזור אליך בהקדם. 📧",
        "contact_sent_received": "ההודעה התקבלה! נחזור אליך בהקדם.",
        
        # Chart titles (Hebrew - same as original)
        "chart_sales_by_hour": "מכירות לפי שעה",
        "chart_sales_by_weekday": "מכירות לפי יום בשבוע",
        "chart_daily_sales": "מכירות יומיות",
        "chart_top_quantity": "Top 10 כמות",
        "chart_top_revenue": "Top 10 הכנסות",
        "chart_payment_methods": "אמצעי תשלום",
        "chart_avg_ticket": "ממוצע קנייה לפי שעה",
        "chart_heatmap": "מפת חום מכירות",
        "chart_weekend_compare": "השוואת סופ״ש לימי חול",
        "chart_note_sales_by_hour": "סכום המכירות לכל שעה בטווח שנבחר",
        "chart_note_sales_by_weekday": "איזה ימים חזקים/חלשים",
        "chart_note_daily_sales": "תנודות יום־יומיות",
        "chart_note_top_quantity": "המוצרים הנמכרים בכמות הגבוהה ביותר",
        "chart_note_top_revenue": "המוצרים שמכניסים הכי הרבה כסף",
        "chart_note_payment_methods": "התפלגות לפי אמצעי תשלום",
        
        # Chart axis labels (Hebrew - same as original)
        "chart_axis_hour": "שעה",
        "chart_axis_day": "יום בשבוע",
        "chart_axis_total": "סה\"כ (₪)",
        "chart_axis_quantity": "כמות",
        "chart_axis_avg_ticket": "ממוצע צ'ק (₪)",
        "chart_axis_sales": "מכירות",
        "chart_axis_currency": "₪",
        
        # Summary labels (Hebrew - same as original)
        "summary_total_sales": "סה\"כ מכירות",
        "summary_days_in_report": "ימים בדוח",
        "summary_daily_avg": "ממוצע יומי",
        "summary_transactions": "עסקאות",
        "summary_avg_per_transaction": "ממוצע לעסקה",
        "summary_best_day": "היום הכי טוב",
        "summary_weakest_day": "היום הכי חלש",
        
        # About page translations
        "about_ai_badge": "✨ אנליטיקה מונעת AI",
        "about_hero_title": "הפוך את נתוני העסק שלך ל",
        "about_hero_title_gradient": "תובנות מעשיות",
        "about_hero_desc": "OnePoweb מנתח את נתוני המכירות שלך תוך שניות ומספק המלצות מונעות AI להגברת רווחים, אופטימיזציה של פעולות והבנה טובה יותר של הלקוחות שלך.",
        "about_btn_dashboard": "עבור ללוח הבקרה",
        "about_btn_upload": "התחל ניתוח",
        "about_btn_get_started": "התחל בחינם",
        "about_btn_learn_more": "למד עוד",
        "about_no_card": "ללא כרטיס אשראי",
        "about_trial": "2 ימים חינם - אחר כך מנוי PRO",
        "about_smart_analytics": "אנליטיקה חכמה",
        "about_ai_insights": "תובנות AI",
        "about_roi_boost": "עליית ROI",
        "about_section_examples": "ראה זאת בפעולה",
        "about_section_examples_desc": "דוגמאות אמיתיות של תובנות ודוחות מ-OnePoweb",
        "about_visual_analytics": "אנליטיקה חזותית",
        "about_visual_analytics_desc": "גרפים יפים המציגים מגמות מכירות, שעות שיא ודפוסי התנהגות לקוחות",
        "about_ai_powered": "תובנות מונעות AI",
        "about_ai_powered_desc": "המלצות חכמות המבוססות על הנתונים שלך להגברת רווחים ואופטימיזציה של פעולות",
        "about_roi_estimation": "הערכת ROI",
        "about_roi_estimation_desc": "חשב רווח חודשי פוטנציאלי עם המלצות מעשיות",
        "about_try_demo_title": "נסה עם נתונים אמיתיים",
        "about_try_demo_desc": "הורד את דוח בית הקפה לדוגמה שלנו ונתח אותו מיידית. אין צורך בהרשמה!",
        "about_download_sample": "הורד דוח לדוגמה",
        "about_analyze_sample": "נתח דוח לדוגמה",
        "about_signin_to_try": "התחבר עם Google כדי לנסות את הדמו",
        "about_signin_btn": "התחבר לנסות דמו",
        "about_why_choose": "למה לבחור ב-OnePoweb?",
        "about_why_choose_desc": "כל מה שאתה צריך לקבלת החלטות מבוססות נתונים",
        "about_instant_analysis": "ניתוח מיידי",
        "about_instant_analysis_desc": "העלה את נתוני המכירות שלך וקבל תובנות מקיפות תוך שניות. אין צורך בעבודה ידנית.",
        "about_ai_recommendations": "המלצות מונעות AI",
        "about_ai_recommendations_desc": "קבל תוכניות פעולה מותאמות אישית המבוססות על דפוסי עסקים ופרקטיקות מובילות בתעשייה.",
        "about_roi_calculator": "מחשבון ROI",
        "about_roi_calculator_desc": "גלה הזדמנויות נסתרות להגברת רווחים ב-20-30% עם ניתוח ROI המתקדם שלנו.",
        "about_professional_reports": "דוחות מקצועיים",
        "about_professional_reports_desc": "ייצא דוחות PDF יפים עם גרפים ותובנות לשיתוף עם הצוות שלך.",
        "about_secure_private": "מאובטח ופרטי",
        "about_secure_private_desc": "הנתונים שלך מוצפנים ונשמרים בצורה מאובטחת. לעולם לא נשתף את המידע שלך עם צדדים שלישיים.",
        "about_multi_language": "תמיכה בשפות מרובות",
        "about_multi_language_desc": "זמין בעברית, אנגלית ורוסית עם תמיכה במטבעות מרובים.",
        "about_cta_logged_in_title": "התחל לנתח את הנתונים שלך",
        "about_cta_logged_in_desc": "העלה את נתוני המכירות שלך וקבל תובנות מיידיות",
        "about_cta_logged_in_btn": "העלה נתונים עכשיו",
        "about_cta_guest_title": "מוכן להפוך את העסק שלך?",
        "about_cta_guest_desc": "הצטרף לאלפי עסקים המקבלים החלטות חכמות יותר עם OnePoweb",
        "about_cta_guest_btn": "התחל - זה בחינם",
    },
    "en": {  # English
        # Navigation
        "nav_home": "Analysis",
        "nav_plans": "Plans & Pricing",
        "nav_about": "Why OnePoweb",
        "nav_contact": "Contact",
        "nav_login": "Login",
        "nav_signup": "Sign Up",
        "nav_profile": "My Profile",
        "nav_dashboard": "Dashboard",
        "nav_logout": "Logout",
        
        # Home page
        "hero_new": "New",
        "hero_title": "Analyze Your Data",
        "hero_title_gradient": "With One Click",
        "hero_subtitle": "Upload a POS report and get professional graphs, AI insights, and period comparisons",
        "upload_file": "Upload File",
        "drag_drop": "Drag file or click to select",
        "select_file": "Select File",
        "analyze": "Analyze Report",
        
        # Plans
        "plan_free": "Free",
        "plan_basic": "Basic",
        "plan_pro": "Pro",
        "upgrade": "Upgrade",
        "current_plan": "Current Plan",
        
        # General
        "loading": "Loading...",
        "error": "Error",
        "success": "Success",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "close": "Close",
        
        # Upload form
        "select_graphs": "Select Graphs",
        "select_graphs_desc": "Mark the graphs you want to generate",
        "time_trends": "Time & Trends",
        "sales_by_hour": "Sales by Hour",
        "sales_by_weekday": "Sales by Day of Week",
        "heatmap": "Heat Map (Hour×Day)",
        "daily_sales": "Daily Sales",
        "products": "Products",
        "top_quantity": "Top 10 Quantity",
        "top_revenue": "Top 10 Revenue",
        "payment_methods": "Payment Methods",
        "advanced": "Advanced",
        "avg_ticket": "Average Ticket",
        "weekend_compare": "Weekend vs Weekdays",
        "period_type": "Period Type",
        "month": "Month",
        "week": "Week",
        "day": "Day",
        "custom": "Custom",
        "period_name": "Period Name (optional)",
        "hour_range": "Hour Range",
        "to": "to",
        "analyze_button": "Analyze Report",
        "popular": "Popular",
        "new": "New",
        "back": "Back",
        "next": "Next",
        "previous": "Previous",
        "submit": "Submit",
        "download": "Download",
        "upload": "Upload",
        
        # Authentication
        "login_title": "Login",
        "login_email": "Email or Username",
        "login_password": "Password",
        "login_button": "Login",
        "login_forgot": "Forgot Password?",
        "login_no_account": "Don't have an account?",
        "signup_title": "Sign Up",
        "signup_email": "Email",
        "signup_username": "Username",
        "signup_password": "Password",
        "signup_confirm": "Confirm Password",
        "signup_terms": "I agree to the Terms of Service",
        "signup_button": "Sign Up",
        "signup_have_account": "Already have an account?",
        "password_requirements": "Password Requirements:",
        "password_length": "8-32 characters",
        "password_english": "English letters only",
        "password_upper": "Uppercase letter (A-Z)",
        "password_digit": "Digit (0-9)",
        "security_note": "Connection is secure and encrypted",
        
        # Profile
        "profile_title": "My Profile",
        "profile_email": "Email",
        "profile_username": "Username",
        "profile_plan": "Plan",
        "profile_edit": "Edit Profile",
        "profile_change_password": "Change Password",
        "profile_current_status": "Current Status",
        "profile_active": "Active",
        "profile_cancelled": "Cancelled",
        "profile_no_subscription": "No Subscription",
        "profile_trial_available": "Try PRO free for 2 days!",
        "profile_trial_desc": "Get full access to all Pro features for 2 days. After that, PRO subscription will start. No credit card",
        "profile_start_trial": "Start trial period",
        
        # Profile Edit
        "profile_edit_title": "Edit Profile",
        "profile_personal_details": "Personal Details",
        "profile_first_name": "First Name",
        "profile_last_name": "Last Name",
        "profile_username_label": "Username (for quick login)",
        "profile_username_hint": "4-20 characters: English letters and numbers only",
        "profile_password_section": "Change Password",
        "profile_password_optional": "Leave blank if you don't want to change",
        "profile_new_password": "New Password",
        "profile_confirm_password": "Confirm Password",
        "profile_password_requirements": "Password Requirements:",
        "profile_password_length": "8-32 characters",
        "profile_password_english": "English letters only",
        "profile_password_upper": "Uppercase letter (A-Z)",
        "profile_password_digit": "Digit (0-9)",
        "profile_passwords_match": "Passwords match",
        "profile_passwords_no_match": "Passwords do not match",
        "profile_email_verified": "Email Verified",
        "profile_email_not_verified": "Email Not Verified",
        "profile_resend_verification": "Resend",
        "profile_save_changes": "Save Changes",
        "profile_cancel": "Cancel",
        "profile_registered": "Registered",
        "profile_data_protected": "Your data is protected and encrypted",
        
        # Flash messages
        "msg_login_required": "Please login first",
        "msg_login_success": "Logged in successfully!",
        "msg_login_failed": "Invalid email/password",
        "msg_signup_success": "Signed up successfully! Check your email for verification",
        "msg_signup_failed": "Signup error",
        "msg_logout": "Logged out successfully",
        "msg_file_uploaded": "File uploaded successfully",
        "msg_file_error": "File upload error",
        "msg_trial_started": "Trial period activated! 2 days free - then PRO subscription",
        "msg_trial_used": "Trial period already used",
        "msg_subscription_active": "Subscription activated successfully!",
        "msg_subscription_cancelled": "Subscription cancelled",
        "msg_profile_updated": "Profile updated successfully",
        "msg_fill_name": "Please fill in first and last name",
        "msg_username_required": "Username is required",
        "msg_username_length": "Username must be between 4-20 characters",
        "msg_username_format": "Username can only contain English letters and numbers",
        "msg_username_taken": "This username is already taken",
        "msg_password_mismatch": "Password confirmation does not match the new password",
        
        # Errors
        "error_404": "Page Not Found",
        "error_403": "Forbidden",
        "error_500": "Server Error",
        "error_generic": "Something went wrong",
        
        # Results
        "results_title": "Analysis results",
        "results_upload_new": "Upload new report",
        "results_download_pdf": "Download PDF",
        "results_no_graphs": "No charts to display. Go back to the main page and upload a new report.",
        "results_no_graphs_reload": "Graphs not found. Redirecting to dashboard where you can view saved reports.",
        "results_summary": "Analysis Summary",
        "results_summary_desc": "Key insights from your report",
        "results_upgrade_banner": "Want to see charts and advanced analysis?",
        "results_upgrade_desc": "Upgrade to Basic or Pro plan to see all charts and data",
        "results_basic_graphs": "Basic - charts only",
        "results_pro_ai": "Pro - including AI",
        "results_try_free": "Try 2 days free - then PRO subscription",
        "results_action_plan": "Recommended Action Plan",
        "results_action_desc": "Specific actions based on your analysis",
        "results_how_to": "How to do it?",
        "results_roi_potential": "Improvement Potential",
        "results_roi_monthly": "Potential Monthly",
        "results_roi_theoretical": "Theoretical ROI",
        "results_roi_estimate": "Estimate only",
        "results_roi_depends": "Depends on your actions",
        "results_more_recommendations": "More {count} recommendations",
        "results_ai_insights": "We have {count} AI recommendations for you!",
        "results_upgrade_for_ai": "Upgrade to Pro plan to get a personalized action plan",
        "results_upgrade_to_pro": "Upgrade to Pro",
        "results_download_image": "Download Image",
        
        # Checkout
        "checkout_order_summary": "Order Summary",
        
        # Get Started / Onboarding
        "nav_get_started": "Get Started",
        "get_started_title": "Getting to know you...",
        "get_started_subtitle": "Help us personalize your experience",
        "get_started_q1_title": "How many locations does your business have?",
        "get_started_q1_desc": "This helps us tailor insights specifically for your business scale",
        "get_started_location_single": "Single",
        "get_started_q2_title": "What industry are you in?",
        "get_started_q2_desc": "We'll provide industry-specific recommendations",
        "get_started_q3_title": "What's your primary goal?",
        "get_started_q3_desc": "Let's focus on what matters most to you",
        "get_started_industry_restaurant": "Restaurant/Cafe",
        "get_started_industry_retail": "Retail",
        "get_started_industry_services": "Services",
        "get_started_industry_ecommerce": "E-commerce",
        "get_started_industry_healthcare": "Healthcare",
        "get_started_industry_other": "Other",
        "get_started_goal_revenue": "Increase Revenue",
        "get_started_goal_revenue_desc": "Boost your sales and income",
        "get_started_goal_operations": "Optimize Operations",
        "get_started_goal_operations_desc": "Improve efficiency and reduce costs",
        "get_started_goal_customers": "Understand Customers",
        "get_started_goal_customers_desc": "Gain insights into buyer behavior",
        "get_started_goal_performance": "Track Performance",
        "get_started_goal_performance_desc": "Monitor KPIs and metrics",
        "get_started_skip": "Skip for now →",
        "get_started_back": "Back",
        "get_started_next": "Next",
        "get_started_continue": "Continue",
        
        # Contact
        "contact_sent": "Message sent successfully! We will get back to you shortly. 📧",
        "contact_sent_received": "Message received! We will get back to you shortly.",
        
        # About page translations
        "about_ai_badge": "✨ AI-Powered Analytics",
        "about_hero_title": "Transform Your Business Data Into",
        "about_hero_title_gradient": "Actionable Insights",
        "about_hero_desc": "OnePoweb analyzes your sales data in seconds and provides AI-driven recommendations to boost revenue, optimize operations, and understand your customers better.",
        "about_btn_dashboard": "Go to Dashboard",
        "about_btn_upload": "Start Analysis",
        "about_btn_get_started": "Get Started Free",
        "about_btn_learn_more": "Learn More",
        "about_no_card": "No credit card required",
        "about_trial": "2 days free - then PRO subscription",
        "about_smart_analytics": "Smart Analytics",
        "about_ai_insights": "AI Insights",
        "about_roi_boost": "ROI Boost",
        "about_section_examples": "See It In Action",
        "about_section_examples_desc": "Real examples of insights and reports from OnePoweb",
        "about_visual_analytics": "Visual Analytics",
        "about_visual_analytics_desc": "Beautiful charts showing sales trends, peak hours, and customer behavior patterns",
        "about_ai_powered": "AI-Powered Insights",
        "about_ai_powered_desc": "Smart recommendations based on your data to increase revenue and optimize operations",
        "about_roi_estimation": "ROI Estimation",
        "about_roi_estimation_desc": "Calculate potential monthly gains with actionable recommendations",
        "about_try_demo_title": "Try It With Real Data",
        "about_try_demo_desc": "Download our sample cafe report and analyze it instantly. No signup required!",
        "about_download_sample": "Download Sample Report",
        "about_analyze_sample": "Analyze Sample Report",
        "about_signin_to_try": "Sign in with Google to try the demo",
        "about_signin_btn": "Sign In to Try Demo",
        "about_why_choose": "Why Choose OnePoweb?",
        "about_why_choose_desc": "Everything you need to make data-driven decisions",
        "about_instant_analysis": "Instant Analysis",
        "about_instant_analysis_desc": "Upload your sales data and get comprehensive insights in seconds. No manual work required.",
        "about_ai_recommendations": "AI-Powered Recommendations",
        "about_ai_recommendations_desc": "Get personalized action plans based on your business patterns and industry best practices.",
        "about_roi_calculator": "ROI Calculator",
        "about_roi_calculator_desc": "Discover hidden opportunities to increase revenue by 20-30% with our advanced ROI analysis.",
        "about_professional_reports": "Professional Reports",
        "about_professional_reports_desc": "Export beautiful PDF reports with charts and insights to share with your team.",
        "about_secure_private": "Secure & Private",
        "about_secure_private_desc": "Your data is encrypted and stored securely. We never share your information with third parties.",
        "about_multi_language": "Multi-Language Support",
        "about_multi_language_desc": "Available in Hebrew, English, and Russian with multi-currency support.",
        "about_cta_logged_in_title": "Start Analyzing Your Data",
        "about_cta_logged_in_desc": "Upload your sales data and get instant insights",
        "about_cta_logged_in_btn": "Upload Data Now",
        "about_cta_guest_title": "Ready to Transform Your Business?",
        "about_cta_guest_desc": "Join thousands of businesses making smarter decisions with OnePoweb",
        "about_cta_guest_btn": "Get Started - It's Free",
        
        # Chart titles
        "chart_sales_by_hour": "Sales by Hour",
        "chart_sales_by_weekday": "Sales by Day of Week",
        "chart_daily_sales": "Daily Sales",
        "chart_top_quantity": "Top 10 Quantity",
        "chart_top_revenue": "Top 10 Revenue",
        "chart_payment_methods": "Payment Methods",
        "chart_avg_ticket": "Average Ticket by Hour",
        "chart_heatmap": "Sales Heat Map",
        "chart_weekend_compare": "Weekend vs Weekdays",
        "chart_note_sales_by_hour": "Total sales for each hour in the selected range",
        "chart_note_sales_by_weekday": "Which days are strong/weak",
        "chart_note_daily_sales": "Daily fluctuations",
        "chart_note_top_quantity": "Products sold in the highest quantity",
        "chart_note_top_revenue": "Products that bring in the most money",
        "chart_note_payment_methods": "Distribution by payment method",
        
        # Chart axis labels
        "chart_axis_hour": "Hour",
        "chart_axis_day": "Day of Week",
        "chart_axis_total": "Total ($)",
        "chart_axis_quantity": "Quantity",
        "chart_axis_avg_ticket": "Average Ticket ($)",
        "chart_axis_sales": "Sales",
        "chart_axis_currency": "$",
        
        # Summary labels
        "summary_total_sales": "Total Sales",
        "summary_days_in_report": "Days in Report",
        "summary_daily_avg": "Daily Average",
        "summary_transactions": "Transactions",
        "summary_avg_per_transaction": "Average per Transaction",
        "summary_best_day": "Best Day",
        "summary_weakest_day": "Weakest Day",
    },
    "ru": {  # Русский
        # Навигация
        "nav_home": "Анализ",
        "nav_plans": "Тарифы",
        "nav_about": "О OnePoweb",
        "nav_contact": "Контакты",
        "nav_login": "Вход",
        "nav_signup": "Регистрация",
        "nav_profile": "Мой профиль",
        "nav_dashboard": "Панель управления",
        "nav_logout": "Выход",
        
        # Главная страница
        "hero_new": "Новое",
        "hero_title": "Анализируйте свои данные",
        "hero_title_gradient": "В один клик",
        "hero_subtitle": "Загрузите отчет кассы и получите профессиональные графики, AI-инсайты и сравнение периодов",
        "upload_file": "Загрузить файл",
        "drag_drop": "Перетащите файл или нажмите для выбора",
        "select_file": "Выбрать файл",
        "analyze": "Анализировать отчет",
        
        # Планы
        "plan_free": "Бесплатно",
        "plan_basic": "Basic",
        "plan_pro": "Pro",
        "upgrade": "Обновить",
        "current_plan": "Текущий план",
        
        # Общие
        "loading": "Загрузка...",
        "error": "Ошибка",
        "success": "Успешно",
        "save": "Сохранить",
        "cancel": "Отмена",
        "delete": "Удалить",
        "edit": "Редактировать",
        "close": "Закрыть",
        
        # Форма загрузки
        "select_graphs": "Выбор графиков",
        "select_graphs_desc": "Отметьте графики, которые хотите создать",
        "time_trends": "Время и тренды",
        "sales_by_hour": "Продажи по часам",
        "sales_by_weekday": "Продажи по дням недели",
        "heatmap": "Тепловая карта (Час×День)",
        "daily_sales": "Ежедневные продажи",
        "products": "Продукты",
        "top_quantity": "Топ 10 по количеству",
        "top_revenue": "Топ 10 по выручке",
        "payment_methods": "Способы оплаты",
        "advanced": "Дополнительно",
        "avg_ticket": "Средний чек",
        "weekend_compare": "Выходные vs Будни",
        "period_type": "Тип периода",
        "month": "Месяц",
        "week": "Неделя",
        "day": "День",
        "custom": "Произвольный",
        "period_name": "Название периода (необязательно)",
        "hour_range": "Диапазон часов",
        "to": "до",
        "analyze_button": "Анализировать отчет",
        "popular": "Популярно",
        "new": "Новое",
        "back": "Назад",
        "next": "Далее",
        "previous": "Назад",
        "submit": "Отправить",
        "download": "Скачать",
        "upload": "Загрузить",
        
        # Авторизация
        "login_title": "Вход",
        "login_email": "Email или имя пользователя",
        "login_password": "Пароль",
        "login_button": "Войти",
        "login_forgot": "Забыли пароль?",
        "login_no_account": "Нет аккаунта?",
        "signup_title": "Регистрация",
        "signup_email": "Email",
        "signup_username": "Имя пользователя",
        "signup_password": "Пароль",
        "signup_confirm": "Подтвердите пароль",
        "signup_terms": "Я согласен с условиями использования",
        "signup_button": "Зарегистрироваться",
        "signup_have_account": "Уже есть аккаунт?",
        
        # Профиль
        "profile_title": "Мой профиль",
        "profile_email": "Email",
        "profile_username": "Имя пользователя",
        "profile_plan": "План",
        "profile_edit": "Редактировать профиль",
        "profile_change_password": "Изменить пароль",
        
        # Profile Edit
        "profile_edit_title": "Редактировать профиль",
        "profile_personal_details": "Личные данные",
        "profile_first_name": "Имя",
        "profile_last_name": "Фамилия",
        "profile_username_label": "Имя пользователя (для быстрого входа)",
        "profile_username_hint": "4-20 символов: только английские буквы и цифры",
        "profile_password_section": "Изменить пароль",
        "profile_password_optional": "Оставьте пустым, если не хотите изменять",
        "profile_new_password": "Новый пароль",
        "profile_confirm_password": "Подтвердите пароль",
        "profile_password_requirements": "Требования к паролю:",
        "profile_password_length": "8-32 символа",
        "profile_password_english": "Только английские буквы",
        "profile_password_upper": "Заглавная буква (A-Z)",
        "profile_password_digit": "Цифра (0-9)",
        "profile_passwords_match": "Пароли совпадают",
        "profile_passwords_no_match": "Пароли не совпадают",
        "profile_email_verified": "Email подтвержден",
        "profile_email_not_verified": "Email не подтвержден",
        "profile_resend_verification": "Отправить снова",
        "profile_save_changes": "Сохранить изменения",
        "profile_cancel": "Отмена",
        "profile_registered": "Зарегистрирован",
        "profile_data_protected": "Ваши данные защищены и зашифрованы",
        
        # Flash сообщения
        "msg_login_required": "Сначала войдите в систему",
        "msg_login_success": "Вход выполнен успешно!",
        "msg_login_failed": "Неверный email/пароль",
        "msg_signup_success": "Регистрация успешна! Проверьте email для подтверждения",
        "msg_signup_failed": "Ошибка регистрации",
        "msg_logout": "Выход выполнен успешно",
        "msg_file_uploaded": "Файл загружен успешно",
        "msg_file_error": "Ошибка загрузки файла",
        "msg_trial_started": "Пробный период активирован! 2 дня бесплатно - затем подписка PRO",
        "msg_trial_used": "Пробный период уже использован",
        "msg_subscription_active": "Подписка активирована успешно!",
        "msg_subscription_cancelled": "Подписка отменена",
        "msg_profile_updated": "Профиль успешно обновлен",
        "msg_fill_name": "Пожалуйста, заполните имя и фамилию",
        "msg_username_required": "Имя пользователя обязательно",
        "msg_username_length": "Имя пользователя должно быть от 4 до 20 символов",
        "msg_username_format": "Имя пользователя может содержать только английские буквы и цифры",
        "msg_username_taken": "Это имя пользователя уже занято",
        "msg_password_mismatch": "Подтверждение пароля не совпадает с новым паролем",
        
        # Ошибки
        "error_404": "Страница не найдена",
        "error_403": "Доступ запрещен",
        "error_500": "Ошибка сервера",
        "error_generic": "Что-то пошло не так",
        
        # Dashboard
        "dashboard_title": "Панель управления",
        "dashboard_subtitle": "Сравнение периодов и анализ трендов",
        "dashboard_upload_new": "Загрузить новый отчет",
        "dashboard_total_sales": "Общие продажи",
        "dashboard_saved_reports": "Сохраненные отчеты",
        "dashboard_avg_daily": "Средний дневной (последний)",
        "dashboard_plan": "План",
        "dashboard_no_reports": "Нет сохраненных отчетов",
        "dashboard_upload_first": "Загрузите первый отчет, чтобы начать",
        "dashboard_period_type": "Тип периода",
        "dashboard_period": "Период",
        "dashboard_actions": "Действия",
        "dashboard_view": "Просмотр",
        "dashboard_compare": "Сравнить",
        "dashboard_delete": "Удалить",
        
        # Results
        "results_title": "Результаты анализа",
        "results_upload_new": "Загрузить новый отчет",
        "results_download_pdf": "Скачать PDF",
        "results_no_graphs": "Нет графиков для отображения. Вернитесь на главную страницу и загрузите новый отчет.",
        "results_no_graphs_reload": "Графики не найдены. Перенаправляем на панель управления, где вы можете просмотреть сохраненные отчеты.",
        "results_summary": "Сводка анализа",
        "results_summary_desc": "Основные выводы из вашего отчета",
        "results_upgrade_banner": "Хотите увидеть графики и продвинутый анализ?",
        "results_upgrade_desc": "Обновитесь до плана Basic или Pro, чтобы увидеть все графики и данные",
        "results_basic_graphs": "Basic - только графики",
        "results_pro_ai": "Pro - включая AI",
        "results_try_free": "Попробуйте 2 дня бесплатно - затем подписка PRO",
        "results_action_plan": "Рекомендуемый план действий",
        "results_action_desc": "Конкретные действия на основе вашего анализа",
        "results_how_to": "Как это сделать?",
        "results_roi_potential": "Потенциал улучшения",
        "results_roi_monthly": "Потенциальный месячный",
        "results_roi_theoretical": "Теоретический ROI",
        "results_roi_estimate": "Только оценка",
        "results_roi_depends": "Зависит от ваших действий",
        "results_more_recommendations": "Еще {count} рекомендаций",
        "results_ai_insights": "У нас есть {count} AI-рекомендаций для вас!",
        "results_upgrade_for_ai": "Обновитесь до плана Pro, чтобы получить персонализированный план действий",
        "results_upgrade_to_pro": "Обновить до Pro",
        "results_download_image": "Скачать изображение",
        
        # Chart titles
        "chart_sales_by_hour": "Продажи по часам",
        "chart_sales_by_weekday": "Продажи по дням недели",
        "chart_daily_sales": "Ежедневные продажи",
        "chart_top_quantity": "Топ 10 по количеству",
        "chart_top_revenue": "Топ 10 по выручке",
        "chart_payment_methods": "Способы оплаты",
        "chart_avg_ticket": "Средний чек по часам",
        "chart_heatmap": "Тепловая карта продаж",
        "chart_weekend_compare": "Сравнение выходных и будних",
        "chart_note_sales_by_hour": "Сумма продаж за каждый час в выбранном диапазоне",
        "chart_note_sales_by_weekday": "Какие дни сильные/слабые",
        "chart_note_daily_sales": "Ежедневные колебания",
        "chart_note_top_quantity": "Продукты, продаваемые в наибольшем количестве",
        "chart_note_top_revenue": "Продукты, приносящие больше всего денег",
        "chart_note_payment_methods": "Распределение по способам оплаты",
        
        # Chart axis labels
        "chart_axis_hour": "Час",
        "chart_axis_day": "День недели",
        "chart_axis_total": "Всего (₽)",
        "chart_axis_quantity": "Количество",
        "chart_axis_avg_ticket": "Средний чек (₽)",
        "chart_axis_sales": "Продажи",
        "chart_axis_currency": "₽",
        
        # Summary labels
        "summary_total_sales": "Общие продажи",
        "summary_days_in_report": "Дней в отчете",
        "summary_daily_avg": "Средний дневной",
        "summary_transactions": "Транзакции",
        "summary_avg_per_transaction": "Средний за транзакцию",
        "summary_best_day": "Лучший день",
        "summary_weakest_day": "Слабый день",
        
        # Pricing
        "pricing_title": "Выберите подходящий план",
        "pricing_subtitle": "Все планы включают базовый анализ. Обновитесь, чтобы получить больше инсайтов и расти быстрее.",
        "pricing_current": "Ваш текущий план:",
        "pricing_your_plan": "Ваш план",
        "pricing_trial": "Пробный период",
        "pricing_free": "Бесплатно",
        "pricing_free_desc": "Базовые графики без AI",
        "pricing_free_features": "Базовые графики",
        "pricing_free_price": "$0",
        "pricing_basic": "Basic",
        "pricing_basic_desc": "Графики без AI",
        "pricing_basic_price": "$15/месяц",
        "pricing_basic_features": "Все графики, без AI",
        "pricing_pro": "Pro",
        "pricing_pro_desc": "Графики + AI-инсайты",
        "pricing_pro_price": "$20/месяц",
        "pricing_pro_features": "Все графики + AI-рекомендации",
        "pricing_try_trial": "Попробуйте 2 дня бесплатно - затем подписка PRO",
        "pricing_no_credit_card": "Без кредитной карты",
        "pricing_cancel_anytime": "Отмена в любое время",
        "pricing_choose_plan": "Выбрать план",
        "pricing_current_badge": "Текущий план",
        
        # Profile
        "profile_subscription": "Управление подпиской",
        "profile_current_status": "Текущий статус",
        "profile_active": "Активна",
        "profile_cancelled": "Отменена",
        "profile_no_subscription": "Без подписки",
        "profile_trial_available": "Попробуйте PRO бесплатно на 2 дня!",
        "profile_trial_desc": "Получите полный доступ ко всем функциям Pro на 2 дня. После этого будет подписка PRO. Без кредитной карты",
        "profile_start_trial": "Начать пробный период",
        "profile_manage_subscription": "Управление подпиской",
        "profile_cancel_subscription": "Отменить подписку",
        "profile_cancel_warning": "Ваша подписка будет отменена в конце текущего периода",
        "profile_saved_reports": "Сохраненные отчеты",
        "profile_no_saved_reports": "Нет сохраненных отчетов",
        "profile_load_report": "Загрузить отчет",
        
        # Account settings
        "change_password_title": "Изменить пароль",
        "change_email_title": "Изменить email",
        "saved_reports_title": "Сохраненные отчеты",
        "delete_account_title": "Удалить аккаунт",
        "current_password": "Текущий пароль",
        "new_password": "Новый пароль",
        "confirm_password": "Подтвердите пароль",
        "current_password_incorrect": "Неверный текущий пароль",
        "passwords_dont_match": "Пароли не совпадают",
        "password_changed_success": "Пароль успешно изменен",
        "password_incorrect": "Неверный пароль",
        "invalid_email": "Неверный формат email",
        "email_already_exists": "Этот email уже используется",
        "email_changed_success": "Email успешно изменен",
        "confirmation_text_incorrect": "Неверный текст подтверждения",
        "account_deleted_success": "Аккаунт успешно удален",
        "save_changes": "Сохранить изменения",
        "cancel": "Отмена",
        
        # Contact
        "contact_title": "Свяжитесь с нами",
        "contact_subtitle": "Мы здесь, чтобы помочь",
        "contact_name": "Имя",
        "contact_email": "Email",
        "contact_subject": "Тема",
        "contact_message": "Сообщение",
        "contact_send": "Отправить",
        "contact_sent": "Сообщение отправлено успешно! Мы свяжемся с вами в ближайшее время.",
        "contact_sent_received": "Сообщение получено! Мы свяжемся с вами в ближайшее время.",
        
        # About
        "about_title": "Почему OnePoweb?",
        "about_why": "Почему выбирают нас",
        "about_features": "Функции",
        "about_testimonials": "Отзывы",
        
        # About page translations
        "about_ai_badge": "✨ Аналитика на основе AI",
        "about_hero_title": "Превратите данные вашего бизнеса в",
        "about_hero_title_gradient": "Практические инсайты",
        "about_hero_desc": "OnePoweb анализирует ваши данные о продажах за секунды и предоставляет рекомендации на основе AI для увеличения доходов, оптимизации операций и лучшего понимания клиентов.",
        "about_btn_dashboard": "Перейти в панель управления",
        "about_btn_upload": "Начать анализ",
        "about_btn_get_started": "Начать бесплатно",
        "about_btn_learn_more": "Узнать больше",
        "about_no_card": "Без кредитной карты",
        "about_trial": "2 дня бесплатно - затем подписка PRO",
        "about_smart_analytics": "Умная аналитика",
        "about_ai_insights": "AI-инсайты",
        "about_roi_boost": "Рост ROI",
        "about_section_examples": "Посмотрите в действии",
        "about_section_examples_desc": "Реальные примеры инсайтов и отчетов от OnePoweb",
        "about_visual_analytics": "Визуальная аналитика",
        "about_visual_analytics_desc": "Красивые графики, показывающие тренды продаж, часы пик и паттерны поведения клиентов",
        "about_ai_powered": "Инсайты на основе AI",
        "about_ai_powered_desc": "Умные рекомендации на основе ваших данных для увеличения доходов и оптимизации операций",
        "about_roi_estimation": "Оценка ROI",
        "about_roi_estimation_desc": "Рассчитайте потенциальную месячную прибыль с практическими рекомендациями",
        "about_try_demo_title": "Попробуйте с реальными данными",
        "about_try_demo_desc": "Скачайте наш пример отчета кафе и проанализируйте его мгновенно. Регистрация не требуется!",
        "about_download_sample": "Скачать пример отчета",
        "about_analyze_sample": "Проанализировать пример отчета",
        "about_signin_to_try": "Войдите через Google, чтобы попробовать демо",
        "about_signin_btn": "Войти для демо",
        "about_why_choose": "Почему выбирают OnePoweb?",
        "about_why_choose_desc": "Все, что нужно для принятия решений на основе данных",
        "about_instant_analysis": "Мгновенный анализ",
        "about_instant_analysis_desc": "Загрузите данные о продажах и получите комплексные инсайты за секунды. Ручная работа не требуется.",
        "about_ai_recommendations": "Рекомендации на основе AI",
        "about_ai_recommendations_desc": "Получите персонализированные планы действий на основе бизнес-паттернов и лучших практик индустрии.",
        "about_roi_calculator": "Калькулятор ROI",
        "about_roi_calculator_desc": "Обнаружьте скрытые возможности для увеличения доходов на 20-30% с помощью нашего продвинутого анализа ROI.",
        "about_professional_reports": "Профессиональные отчеты",
        "about_professional_reports_desc": "Экспортируйте красивые PDF-отчеты с графиками и инсайтами для обмена с командой.",
        "about_secure_private": "Безопасно и конфиденциально",
        "about_secure_private_desc": "Ваши данные зашифрованы и надежно хранятся. Мы никогда не делимся вашей информацией с третьими лицами.",
        "about_multi_language": "Поддержка нескольких языков",
        "about_multi_language_desc": "Доступно на иврите, английском и русском с поддержкой нескольких валют.",
        "about_cta_logged_in_title": "Начните анализировать свои данные",
        "about_cta_logged_in_desc": "Загрузите данные о продажах и получите мгновенные инсайты",
        "about_cta_logged_in_btn": "Загрузить данные сейчас",
        "about_cta_guest_title": "Готовы преобразить свой бизнес?",
        "about_cta_guest_desc": "Присоединяйтесь к тысячам бизнесов, принимающих более умные решения с OnePoweb",
        "about_cta_guest_btn": "Начать - это бесплатно",
        
        # Forgot/Reset Password
        "forgot_title": "Забыли пароль?",
        "forgot_desc": "Введите ваш email, и мы отправим ссылку для сброса пароля",
        "forgot_send": "Отправить ссылку",
        "forgot_back_login": "Вернуться к входу",
        "reset_title": "Сброс пароля",
        "reset_new_password": "Новый пароль",
        "reset_confirm": "Подтвердите пароль",
        "reset_button": "Сбросить пароль",
        
        # Checkout
        "checkout_title": "Оформление заказа",
        "checkout_order_summary": "Сводка заказа",
        
        # Get Started / Onboarding
        "nav_get_started": "Начать",
        "get_started_title": "Давайте познакомимся...",
        "get_started_subtitle": "Помогите нам персонализировать ваш опыт",
        "get_started_q1_title": "Сколько локаций у вашего бизнеса?",
        "get_started_q1_desc": "Это помогает нам адаптировать аналитику специально под масштаб вашего бизнеса",
        "get_started_location_single": "Одна",
        "get_started_q2_title": "В какой отрасли вы работаете?",
        "get_started_q2_desc": "Мы предоставим рекомендации, специфичные для вашей отрасли",
        "get_started_q3_title": "Какова ваша основная цель?",
        "get_started_q3_desc": "Давайте сосредоточимся на том, что для вас важнее всего",
        "get_started_industry_restaurant": "Ресторан/Кафе",
        "get_started_industry_retail": "Розничная торговля",
        "get_started_industry_services": "Услуги",
        "get_started_industry_ecommerce": "Интернет-магазин",
        "get_started_industry_healthcare": "Здравоохранение",
        "get_started_industry_other": "Другое",
        "get_started_goal_revenue": "Увеличить доходы",
        "get_started_goal_revenue_desc": "Повысьте ваши продажи и доходы",
        "get_started_goal_operations": "Оптимизировать операции",
        "get_started_goal_operations_desc": "Повысьте эффективность и снизьте затраты",
        "get_started_goal_customers": "Понять клиентов",
        "get_started_goal_customers_desc": "Получите инсайты о поведении покупателей",
        "get_started_goal_performance": "Отслеживать производительность",
        "get_started_goal_performance_desc": "Мониторинг KPI и метрик",
        "get_started_skip": "Пропустить сейчас →",
        "get_started_back": "Назад",
        "get_started_next": "Далее",
        "get_started_continue": "Продолжить",
        "checkout_plan": "План",
        "checkout_price": "Цена",
        "checkout_discount": "Реферальная скидка",
        "checkout_total": "Итого",
        "checkout_paypal": "Оплатить через PayPal",
        
        # Upgrade Required
        "upgrade_title": "Требуется обновление",
        "upgrade_feature": "Эта функция доступна только для планов",
        "upgrade_upgrade_now": "Обновить сейчас",
        
        # Thanks pages
        "thanks_title": "Спасибо!",
        "thanks_message": "Ваше сообщение отправлено",
        
        # Common
        "or": "или",
        "view_example": "Посмотреть пример — без загрузки файла",
        "security_note": "Соединение защищено и зашифровано",
        "password_requirements": "Требования к паролю:",
        "password_length": "8-32 символа",
        "password_english": "Только английские буквы",
        "password_upper": "Заглавная буква (A-Z)",
        "password_digit": "Цифра (0-9)",
        "password_match": "Пароли совпадают",
        "password_no_match": "Пароли не совпадают",
        "benefits_trial": "2 дня пробного периода бесплатно - затем подписка PRO",
        "benefits_no_card": "Без кредитной карты",
        "benefits_cancel": "Отмена в любое время",
    }
}

def get_language():
    """Получить текущий язык из сессии, по умолчанию 'en'"""
    from flask import session
    lang = session.get("language", "en")
    print(f"🔍 get_language() called, returning: {lang}, session.get('language') = {session.get('language')}")
    return lang

def t(key, lang=None):
    """Перевести ключ на указанный язык или текущий язык из сессии"""
    if lang is None:
        lang = get_language()
    
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return translations.get(key, key)  # Возвращаем ключ, если перевод не найден

# Context processor для шаблонов
@app.context_processor
def inject_translations():
    """Добавляет функцию t() и текущий язык во все шаблоны"""
    from flask import session
    current_lang = get_language()
    currency = get_currency(current_lang)
    
    # Подготовка списка валют для выбора (в порядке популярности)
    currencies_list = []
    user_currency_code = session.get("currency")
    current_currency_code = currency["code"]
    
    # Добавляем функцию для получения валюты по коду
    def get_currency_by_code_helper(code):
        return get_currency_by_code(code)
    
    # Порядок валют по популярности
    currency_order = ["USD", "EUR", "GBP", "JPY", "CNY", "INR", "CAD", "AUD", "CHF", "ILS", "RUB", 
                      "PLN", "SEK", "NOK", "DKK", "CZK", "HUF", "UAH", "KZT", "KGS"]
    
    for code in currency_order:
        if code in AVAILABLE_CURRENCIES:
            info = AVAILABLE_CURRENCIES[code]
            label_key = f"label_{current_lang}"
            label = info.get(label_key, info["name"])
            is_selected = (user_currency_code == code) if user_currency_code else (current_currency_code == code)
            currencies_list.append({
                "code": code,
                "symbol": info["symbol"],
                "name": info["name"],
                "label": label,
                "flag": info.get("flag", ""),
                "is_selected": is_selected
            })
    
    # Helper function for templates to get currency by code
    def get_currency_by_code_helper(code):
        return get_currency_by_code(code)
    
    return {
        "t": t,
        "current_lang": current_lang,
        "currency": currency,
        "currency_symbol": currency["symbol"],
        "currency_display": currency["display"],
        "available_currencies": currencies_list,
        "get_currency_by_code": get_currency_by_code_helper,
        "AVAILABLE_CURRENCIES": AVAILABLE_CURRENCIES,
        "languages": {
            "he": "עברית",
            "en": "English", 
            "ru": "Русский"
        }
    }

# Функция для перевода flash сообщений
def flash_t(key, category="message"):
    """Flash сообщение с автоматическим переводом"""
    from flask import flash
    message = t(key)
    flash(message, category)

# === Production vs Local paths ===
# Render uses /data for persistent storage
BASE_DIR = os.path.dirname(__file__)
IS_PRODUCTION = os.path.exists("/data")  # True on Render

if IS_PRODUCTION:
    DATA_DIR = "/data"
    DB_PATH = "/data/app.db"
    UPLOAD_DIR = "/data/uploads"
    # Create uploads directory if not exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
else:
    DATA_DIR = BASE_DIR
    DB_PATH = os.path.join(BASE_DIR, "app.db")
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


import secrets, datetime as dt
from flask import request, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash

# ========= FORGOT PASSWORD =========

# ---- imports שנדרשים למעלה בקובץ (אם עדיין לא קיימים) ----
import secrets
import datetime as dt
from flask import request, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash
# get_db חייב להיות מוגדר אצלך (הפונקציה שמחזירה חיבור ל-SQLite עם row_factory=sqlite3.Row)

# ---------- Password Reset Email ----------
def send_password_reset_email(email: str, reset_link: str) -> bool:
    """שולח מייל עם קישור לאיפוס סיסמה"""
    if not SMTP_USER or not SMTP_PASS:
        print(f"⚠️ SMTP not configured - reset email not sent")
        print(f"📧 Reset link for {email}: {reset_link}")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = email
    msg['Subject'] = "🔑 איפוס סיסמה - OnePoweb"
    
    body = f"""
שלום! 👋

קיבלנו בקשה לאיפוס הסיסמה שלך ב-OnePoweb.

👉 לחץ על הקישור הבא לאיפוס הסיסמה:
{reset_link}

⏰ הקישור תקף לשעה אחת בלבד.

אם לא ביקשת לאפס את הסיסמה, אפשר להתעלם מהודעה זו.
הסיסמה שלך לא תשתנה עד שתלחץ על הקישור ותגדיר סיסמה חדשה.

━━━━━━━━━━━━━━━━━━━━━━━━━━
OnePoweb - ניתוח מכירות חכם לעסקים
"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"✅ Password reset email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send reset email: {e}")
        return False


# ---------- Forgot password ----------
@app.route("/forgot", methods=["GET", "POST"], endpoint="forgot_password")
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if not email:
            flash("נא להזין אימייל.", "warning")
            return render_template("forgot.html", title="איפוס סיסמה")

        db = get_db()
        user = db.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()

        # לא חושפים אם קיים/לא קיים – לנוחיות, רק מייצרים טוקן אם קיים
        if user:
            import secrets, datetime as dt
            token = secrets.token_urlsafe(32)
            expires_at = (dt.datetime.utcnow() + dt.timedelta(hours=1)).isoformat(" ")
            db.execute("""
                INSERT INTO password_resets (user_id, token, expires_at, used)
                VALUES (?, ?, ?, 0)
            """, (user["id"], token, expires_at))
            db.commit()

            reset_link = url_for("reset_password", token=token, _external=True)
            send_password_reset_email(email, reset_link)

        flash("אם האימייל קיים במערכת, נשלח אליו קישור לאיפוס סיסמה.", "info")
        return redirect(url_for("forgot_password"))

    return render_template("forgot.html", title="איפוס סיסמה")



# ---------- Password Validation ----------
def validate_password(password: str, lang: str = "en") -> tuple:
    """
    Password validation:
    - 8-32 characters
    - Only English letters and numbers
    - At least one uppercase letter
    - At least one digit
    Returns (is_valid, error_message)
    """
    import re
    if lang == "he":
        if len(password) < 8:
            return False, "הסיסמה חייבת להכיל לפחות 8 תווים"
        if len(password) > 32:
            return False, "הסיסמה יכולה להכיל עד 32 תווים"
        if not re.match(r'^[A-Za-z0-9]+$', password):
            return False, "הסיסמה יכולה להכיל רק אותיות אנגליות (A-Z, a-z) וספרות (0-9)"
        if not any(c.isupper() for c in password):
            return False, "הסיסמה חייבת להכיל לפחות אות גדולה אחת (A-Z)"
        if not any(c.isdigit() for c in password):
            return False, "הסיסמה חייבת להכיל לפחות ספרה אחת (0-9)"
    elif lang == "ru":
        if len(password) < 8:
            return False, "Пароль должен содержать не менее 8 символов"
        if len(password) > 32:
            return False, "Пароль может содержать до 32 символов"
        if not re.match(r'^[A-Za-z0-9]+$', password):
            return False, "Пароль может содержать только английские буквы (A-Z, a-z) и цифры (0-9)"
        if not any(c.isupper() for c in password):
            return False, "Пароль должен содержать хотя бы одну заглавную букву (A-Z)"
        if not any(c.isdigit() for c in password):
            return False, "Пароль должен содержать хотя бы одну цифру (0-9)"
    else:  # en
        if len(password) < 8:
            return False, "Password must contain at least 8 characters"
        if len(password) > 32:
            return False, "Password can contain up to 32 characters"
        if not re.match(r'^[A-Za-z0-9]+$', password):
            return False, "Password can only contain English letters (A-Z, a-z) and numbers (0-9)"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter (A-Z)"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit (0-9)"
    return True, ""


# ---------- Reset password ----------
@app.route("/reset/<token>", methods=["GET", "POST"], endpoint="reset_password")
def reset_password(token):
    import datetime as dt
    db = get_db()
    row = db.execute("""
        SELECT id, user_id, expires_at, used
        FROM password_resets
        WHERE token=? LIMIT 1
    """, (token,)).fetchone()

    if not row or row["used"]:
        flash("קישור לא תקף.", "danger")
        return redirect(url_for("login"))

    try:
        expires = dt.datetime.fromisoformat(row["expires_at"])
    except Exception:
        expires = dt.datetime.utcnow() - dt.timedelta(days=1)

    if dt.datetime.utcnow() > expires:
        flash("הקישור פג תוקף.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        p1 = request.form.get("password") or ""
        p2 = request.form.get("confirm_password") or ""
        if p1 != p2:
            flash("הסיסמאות אינן תואמות.", "warning")
        else:
            # בדיקת תקינות סיסמה
            current_lang = get_language()
            is_valid, error_msg = validate_password(p1, current_lang)
            if not is_valid:
                flash(error_msg, "warning")
            else:
                pw_hash = generate_password_hash(p1)
                db.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, row["user_id"]))
                db.execute("UPDATE password_resets SET used=1 WHERE id=?", (row["id"],))
                db.commit()
                flash("הסיסמה עודכנה! אפשר להתחבר.", "success")
                return redirect(url_for("login"))

    return render_template("reset.html", title="איפוס סיסמה", token=token)


# ---------- Debug: list all routes (זמני) ----------
@app.route("/_debug/routes")
def _debug_routes():
    return "<pre>" + "\n".join(
        f"{r.endpoint:25s} -> {r.rule}" for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule)
    ) + "</pre>"



def ensure_subscription_columns():
    """מוודאת שבטבלת users קיימות עמודות למנוי ואימות מייל."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # יצירת טבלת users אם לא קיימת
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agreed_terms INTEGER DEFAULT 0,
            agreed_at TIMESTAMP
        )
    """)
    
    # יצירת טבלת password_resets
    c.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # יצירת טבלת reports
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            period_type TEXT DEFAULT 'month',
            period_start DATE,
            period_end DATE,
            encrypted_data BLOB NOT NULL,
            summary_json TEXT,
            currency TEXT DEFAULT 'USD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()

    # השג רשימת עמודות קיימות
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]

    # עמודות מנוי
    if "plan" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
    if "subscription_status" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'inactive'")
    if "canceled_at" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN canceled_at TIMESTAMP")
    
    # עמודות אימות מייל
    if "email_verified" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0")
        # מסמנים משתמשים קיימים כמאומתים
        c.execute("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL OR email_verified = 0")
    if "verification_token" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN verification_token TEXT NULL")
    
    # עמודות שם
    if "first_name" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN first_name TEXT NULL")
    if "last_name" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN last_name TEXT NULL")
    
    # שם משתמש (username)
    if "username" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN username TEXT NULL")
    
    # עמודות ניסיון (trial)
    if "trial_until" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN trial_until TEXT NULL")
    if "trial_used" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN trial_used INTEGER DEFAULT 0")
    
    # עמודות onboarding
    if "onboarding_completed" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN onboarding_completed INTEGER DEFAULT 0")
    if "business_locations" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN business_locations TEXT NULL")
    if "business_industry" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN business_industry TEXT NULL")
    if "primary_goal" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN primary_goal TEXT NULL")

    conn.commit()
    conn.close()


# Flask
from flask import (
    Flask, render_template, request, send_file,
    session, redirect, url_for, flash, g, jsonify
)

# סיסמאות מאובטחות
from werkzeug.security import generate_password_hash, check_password_hash

# Matplotlib ללא GUI (חייבים להגדיר לפני pyplot)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams["font.family"] = "DejaVu Sans"
rcParams["axes.unicode_minus"] = False

# ==== RTL helpers (עברית תקינה ב-matplotlib) ====
# מנסים להשתמש ב-python-bidi אם הותקן; אם לא — לא שוברים כלום.
try:
    from bidi.algorithm import get_display as _bidi_get_display
except Exception:
    _bidi_get_display = None

def rtl(s: str) -> str:
    """נסה להפוך טקסט RTL כראוי אם bidi זמין; אחרת החזר כמו שהוא."""
    if _bidi_get_display:
        try:
            return _bidi_get_display(s)
        except Exception:
            return s
    return s

def _rtl(s: str) -> str:
    """עטיפה נוחה לשימוש בקוד הגרפים."""
    return rtl(s)
# ================================================



# --- Jinja2 filters ---
@app.template_filter('fromjson')
def fromjson_filter(value):
    """המרת JSON string ל-dict"""
    try:
        return json.loads(value) if value else {}
    except:
        return {}

# יצירת/בדיקת העמודות של מנוי בהפעלת השרת
with app.app_context():
    ensure_subscription_columns()

# הגבלות בסיסיות לפרודקשן
app.config.update(
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,  # העלאה עד 20MB
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,           # בפרוד על HTTPS
)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-" + os.urandom(16).hex())

# --- תיקים קבועים ---
STATIC_DIR = "static"
PLOTS_DIR  = os.path.join(STATIC_DIR, "plots")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR,  exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- שמות עמודות סטנדרטיים בעברית ---
COL_DATE = "תאריך"
COL_TIME = "שעה"
COL_TXN  = "מס' עסקה"
COL_ITEM = "מוצר"
COL_QTY  = "כמות"
COL_SUM  = "סכום (₪)"
COL_PAY  = "אמצעי תשלום"
COL_UNIT = "מחיר ליחידה (₪)"
HOUR_COL = "שעה עגולה"

COLUMN_MAP = {
    # תאריך - כל הווריאציות הנפוצות
    "תאריך": COL_DATE,
    "date": COL_DATE,
    "תאריף": COL_DATE,
    "תארים": COL_DATE,
    "datetime": COL_DATE,
    "תאריך עסקה": COL_DATE,
    "תאריך מכירה": COL_DATE,
    "transaction date": COL_DATE,
    "sale date": COL_DATE,
    # Русские варианты
    "дата": COL_DATE,
    "Дата": COL_DATE,
    "ДАТА": COL_DATE,

    # שעה - כל הווריאציות
    "שעה": COL_TIME,
    "time": COL_TIME,
    "זמן": COL_TIME,
    "hour": COL_TIME,
    "שעת עסקה": COL_TIME,
    "שעת מכירה": COL_TIME,
    "transaction time": COL_TIME,
    # Русские варианты
    "время": COL_TIME,
    "Время": COL_TIME,
    "ВРЕМЯ": COL_TIME,
    "время транзакции": COL_TIME,

    # סכום (מחיר כולל) - כל הווריאציות הנפוצות בקופות ישראליות
    "סכום": COL_SUM,
    "סהכ": COL_SUM,
    "סה\"כ": COL_SUM,
    "סה״כ": COL_SUM,
    "סכום (₪)": COL_SUM,
    "סכום עסקה": COL_SUM,
    "סכום כולל": COL_SUM,
    "סכום לתשלום": COL_SUM,
    "סה\"כ לתשלום": COL_SUM,
    "total": COL_SUM,
    "amount": COL_SUM,
    "sum": COL_SUM,
    "total amount": COL_SUM,
    "grand total": COL_SUM,
    # Русские варианты
    "сумма": COL_SUM,
    "Сумма": COL_SUM,
    "СУММА": COL_SUM,
    "сумма транзакции": COL_SUM,
    "итого": COL_SUM,
    "Итого": COL_SUM,
    "ИТОГО": COL_SUM,
    # Варианты с символами валют
    "Итого_₽": COL_SUM,
    "Итого ₽": COL_SUM,
    "итого_₽": COL_SUM,
    "Сумма_₽": COL_SUM,
    "Сумма ₽": COL_SUM,
    "סכום (₪)": COL_SUM,
    "סכום_₪": COL_SUM,
    "total ($)": COL_SUM,
    "total_$": COL_SUM,

    # מחיר ליחידה
    "מחיר": COL_UNIT,
    "מחיר ליחידה": COL_UNIT,
    "מחיר ליחידה (₪)": COL_UNIT,
    "מחיר יחידה": COL_UNIT,
    "price": COL_UNIT,
    "unit price": COL_UNIT,
    "unit_price": COL_UNIT,
    # Русские варианты
    "цена": COL_UNIT,
    "Цена": COL_UNIT,
    "ЦЕНА": COL_UNIT,
    "цена за единицу": COL_UNIT,
    "Цена_за_единицу": COL_UNIT,
    "цена за единицу": COL_UNIT,

    # כמות
    "כמות": COL_QTY,
    "qty": COL_QTY,
    "quantity": COL_QTY,
    "יחידות": COL_QTY,
    "כמות שנמכרה": COL_QTY,
    "units": COL_QTY,
    # Русские варианты
    "количество": COL_QTY,
    "Количество": COL_QTY,
    "КОЛИЧЕСТВО": COL_QTY,
    "кол-во": COL_QTY,
    "Кол-во": COL_QTY,
    "Кол-во": COL_QTY,
    "количество товара": COL_QTY,

    # מוצר / פריט
    "מוצר": COL_ITEM,
    "פריט": COL_ITEM,
    "item": COL_ITEM,
    "product": COL_ITEM,
    "שם מוצר": COL_ITEM,
    "שם פריט": COL_ITEM,
    "תיאור": COL_ITEM,
    "description": COL_ITEM,
    "product name": COL_ITEM,
    "item name": COL_ITEM,
    # Русские варианты
    "товар": COL_ITEM,
    "Товар": COL_ITEM,
    "ТОВАР": COL_ITEM,
    "название товара": COL_ITEM,
    "продукт": COL_ITEM,
    "Продукт": COL_ITEM,
    "наименование": COL_ITEM,

    # מספר עסקה
    "מס' עסקה": COL_TXN,
    "מס עסקה": COL_TXN,
    "מספר עסקה": COL_TXN,
    "עסקה": COL_TXN,
    "transaction": COL_TXN,
    "transaction id": COL_TXN,
    "txn": COL_TXN,
    "receipt": COL_TXN,
    "קבלה": COL_TXN,
    "מס' קבלה": COL_TXN,
    # Русские варианты
    "транзакция": COL_TXN,
    "Транзакция": COL_TXN,
    "ТРАНЗАКЦИЯ": COL_TXN,
    "номер транзакции": COL_TXN,
    "№_транзакции": COL_TXN,
    "№ транзакции": COL_TXN,
    "номер": COL_TXN,
    "№": COL_TXN,

    # אמצעי תשלום
    "אמצעי תשלום": COL_PAY,
    "תשלום": COL_PAY,
    "אמצעי_תשלום": COL_PAY,
    "סוג תשלום": COL_PAY,
    "payment": COL_PAY,
    "payment method": COL_PAY,
    "payment_method": COL_PAY,
    "payment type": COL_PAY,
    # Русские варианты
    "способ оплаты": COL_PAY,
    "Способ_оплаты": COL_PAY,
    "Способ оплаты": COL_PAY,
    "способ оплаты": COL_PAY,
    "оплата": COL_PAY,
    "Оплата": COL_PAY,
    "тип оплаты": COL_PAY,
}


# מיפויים שכיחים -> לשם הסטנדרטי (deprecated - use COLUMN_MAP instead)
COLUMN_RENAMES = {
    "סכום": COL_SUM,
    "סכום כולל": COL_SUM,
    "סכום עסקה": COL_SUM,
    "Amount": COL_SUM,
    "price": COL_UNIT,
    "Price": COL_UNIT,
    "unit_price": COL_UNIT,
    "מחיר ליחידה": COL_UNIT,
    "מחיר ליחידה (₪)": COL_UNIT,
    "datetime": COL_TIME,
}

# ====== Normalize Columns Helper ======
def _normalize_columns(df):
    """נרמול שמות עמודות לפי COLUMN_MAP"""
    def _normalize_col_name(s):
        s = str(s).strip().lower()
        s = s.replace("_", " ").replace("-", " ")
        s = re.sub(r'[₪$€\(\)\[\]]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    
    # בונה מפה מנורמלת
    normalized_map = {}
    for key, val in COLUMN_MAP.items():
        normalized_map[_normalize_col_name(key)] = val
    
    renamed = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col]
            continue
        norm = _normalize_col_name(col)
        if norm in normalized_map:
            renamed[col] = normalized_map[norm]
            continue
        for key, val in COLUMN_MAP.items():
            if key in col or col in key:
                renamed[col] = val
                break
    
    df.rename(columns=renamed, inplace=True)
    return df

# ====== AI (אופציונלי) ======
USE_AI = True
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
_openai_client = None
try:
    from openai import OpenAI
    _openai_client = OpenAI()  # מצפה ל-OPENAI_API_KEY בסביבה
except Exception:
    USE_AI = False

def ensure_subscription_columns():
    """
    מוסיף לטבלת users עמודות מנוי אם חסרות:
    plan, subscription_status, active_until, canceled_at
    (משתמש ב-get_db הקיים אצלך)
    """
    db = get_db()
    cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}

    if "plan" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
    if "subscription_status" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'none'")
    if "active_until" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN active_until TEXT NULL")
    if "canceled_at" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN canceled_at TEXT NULL")
    if "trial_until" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN trial_until TEXT NULL")
    if "trial_used" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN trial_used INTEGER DEFAULT 0")
    # Demo report usage tracking
    if "demo_used" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN demo_used INTEGER DEFAULT 0")
    # Email verification columns
    if "email_verified" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0")
    if "verification_token" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN verification_token TEXT NULL")
    # Username column
    if "username" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN username TEXT NULL")
    # PayPal subscription ID for recurring billing
    if "paypal_subscription_id" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN paypal_subscription_id TEXT NULL")

    db.commit()


def generate_verification_token():
    """יוצר טוקן אימות ייחודי"""
    import secrets
    return secrets.token_urlsafe(32)


def send_verification_email(email: str, token: str):
    """שולח מייל אימות למשתמש חדש"""
    if not SMTP_USER or not SMTP_PASS:
        print(f"⚠️ SMTP not configured - verification email not sent")
        print(f"📧 Verification link: {url_for('verify_email', token=token, _external=True)}")
        return False
    
    verify_link = url_for('verify_email', token=token, _external=True)
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = email
    msg['Subject'] = "🔐 אימות כתובת האימייל שלך - OnePoweb"
    
    body = f"""
שלום! 👋

תודה שנרשמת ל-OnePoweb!

כדי להשלים את ההרשמה ולהתחיל להשתמש במערכת, יש לאמת את כתובת האימייל שלך.

👉 לחץ על הקישור הבא לאימות:
{verify_link}

הקישור תקף ל-24 שעות.

אם לא נרשמת לאתר שלנו, אפשר להתעלם מהודעה זו.

━━━━━━━━━━━━━━━━━━━━━━━━━━
OnePoweb - ניתוח מכירות חכם לעסקים
"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"✅ Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send verification email: {e}")
        return False


def is_trial_active(user) -> bool:
    """בודק אם יש למשתמש תקופת ניסיון פעילה"""
    if not user:
        return False
    try:
        from datetime import datetime
        # sqlite3.Row לא תומך ב-.get(), לכן נבדוק אם העמודה קיימת
        keys = user.keys() if hasattr(user, 'keys') else []
        if "trial_until" not in keys:
            return False
        trial_until = user["trial_until"]
        if not trial_until:
            return False
        trial_date = datetime.strptime(trial_until, "%Y-%m-%d").date()
        return trial_date >= datetime.now().date()
    except:
        return False


def get_trial_days_left(user) -> int:
    """מחזיר כמה ימים נשארו בתקופת הניסיון"""
    if not user:
        return 0
    try:
        from datetime import datetime
        keys = user.keys() if hasattr(user, 'keys') else []
        if "trial_until" not in keys:
            return 0
        trial_until = user["trial_until"]
        if not trial_until:
            return 0
        trial_date = datetime.strptime(trial_until, "%Y-%m-%d").date()
        today = datetime.now().date()
        if trial_date < today:
            return 0
        return (trial_date - today).days
    except:
        return 0


def get_trial_end_timestamp(user) -> str:
    """מחזיר את תאריך סיום הניסיון כ-ISO timestamp"""
    if not user:
        return ""
    try:
        keys = user.keys() if hasattr(user, 'keys') else []
        if "trial_until" not in keys:
            return ""
        trial_until = user["trial_until"]
        if not trial_until:
            return ""
        # Return as ISO date with time at end of day
        return f"{trial_until}T23:59:59"
    except:
        return ""


def get_effective_plan(user) -> str:
    """מחזיר את התוכנית הפעילה (כולל התחשבות בתקופת ניסיון)"""
    if not user:
        return "free"
    # אם יש תקופת ניסיון פעילה - מחזיר pro
    if is_trial_active(user):
        return "pro"
    try:
        keys = user.keys() if hasattr(user, 'keys') else []
        if "plan" in keys:
            return user["plan"] or "free"
        return "free"
    except:
        return "free"


def ai_enabled_for_user() -> bool:
    """בודק אם מותר להציג טקסט AI למשתמש הנוכחי (PRO, TRIAL או FORCE_AI בפיתוח)."""
    if not (_openai_client and USE_AI_ENV):
        return False
    if FORCE_AI:
        return True
    u = current_user()
    effective_plan = get_effective_plan(u)
    return effective_plan == "pro"

def ai_explain(title: str, brief: dict, lang: str = "he") -> str:
    """
    2–3 משפטים בעברית/אנגלית/רוסית + המלצה. מנסה כמה מסלולים:
    1) chat.completions עם max_completion_tokens
    2) chat.completions בלי שום max_*
    3) responses.create עם max_output_tokens
    אם הכל נכשל – מחזיר ריק (לא מפיל את הדף).
    """
    try:
        if not USE_AI or not OPENAI_KEY or _openai_client is None:
            return ""

        # קומפקט בריף
        compact = {}
        if isinstance(brief, dict):
            for i, (k, v) in enumerate(brief.items()):
                if i >= 30:
                    break
                try:
                    compact[k] = round(float(v), 3)
                except Exception:
                    compact[k] = v

        payload = json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
        
        # Определяем язык для промпта
        lang_instructions = {
            "he": {
                "write_in": "עברית",
                "example": "בעברית פשוטה וברורה",
                "focus": "התמקד בתובנה העיקרית אחת",
                "give": "תן המלצה מעשית אחת",
                "length": "2-3 משפטים בלבד",
                "dont": "אל תחזור על מספרים",
                "combo_instruction": "הצע ליצור קומבו/חבילה של המוצר המוביל עם מוצר שפחות נמכר",
                "weak_instruction": "התמקד בימים/שעות החלשים ביותר - אלה הזדמנות למשוך לקוחות חדשים",
            },
            "en": {
                "write_in": "English",
                "example": "in simple and clear English",
                "focus": "Focus on the one main insight",
                "give": "Give one practical recommendation",
                "length": "2-3 sentences only",
                "dont": "Don't repeat numbers",
                "combo_instruction": "Suggest creating a combo/package of the leading product with a less popular product",
                "weak_instruction": "Focus on the weakest days/hours - these are opportunities to attract new customers",
            },
            "ru": {
                "write_in": "русском",
                "example": "простым и понятным русским языком",
                "focus": "Сосредоточься на одной главной идее",
                "give": "Дай одну практическую рекомендацию",
                "length": "только 2-3 предложения",
                "dont": "Не повторяй числа",
                "combo_instruction": "Предложи создать комбо/пакет из лидирующего продукта с менее популярным продуктом",
                "weak_instruction": "Сосредоточься на самых слабых днях/часах - это возможности привлечь новых клиентов",
            }
        }
        
        lang_dict = lang_instructions.get(lang, lang_instructions["he"])
        
        # הוספת הוראות ספציפיות לפי סוג הגרף
        specific_instructions = ""
        
        # Top 10 הכנסות - הצע קומבו עם מוצר לא נמכר
        if "הכנסות" in title or "Top 10" in title or "מוצרים" in title or "Revenue" in title or "Products" in title or "Выручка" in title or "Продукты" in title:
            bottom_items_text = ""
            if isinstance(compact, dict) and "bottom_items" in compact:
                bottom_items = compact.get("bottom_items", {})
                if bottom_items:
                    items_list = list(bottom_items.keys())[:3]  # Top 3 פחות נמכרים
                    bottom_items_text = f"\n• מוצרים פחות נמכרים (לשימוש בקומבו): {', '.join(items_list)}\n"
            
            if lang == "he":
                specific_instructions = (
                    "\n⚠️ הוראה מיוחדת לגרף זה:\n"
                    "• אם יש מוצר מוביל (הכי מכניס), אל תציע רק לקדם אותו עוד יותר\n"
                    f"• במקום זה, {lang_dict['combo_instruction']} (ראה bottom_items בנתונים)\n"
                    "• המטרה: להגדיל מכירות של המוצר החלש תוך ניצול הפופולריות של המוצר החזק\n"
                    f"{bottom_items_text}"
                    "• דוגמה: '[מוצר מוביל] הוא המוצר הכי מכניס שלך. שקול להציע חבילה: [מוצר מוביל] + [אחד מהמוצרים הפחות נמכרים] במחיר מיוחד'\n"
                )
            elif lang == "en":
                specific_instructions = (
                    "\n⚠️ Special instruction for this chart:\n"
                    "• If there is a leading product (highest revenue), don't just suggest promoting it more\n"
                    f"• Instead, {lang_dict['combo_instruction']} (see bottom_items in data)\n"
                    "• Goal: increase sales of weak product while leveraging popularity of strong product\n"
                    f"{bottom_items_text}"
                    "• Example: '[Leading product] is your top revenue product. Consider offering a package: [Leading product] + [one of less popular products] at a special price'\n"
                )
            else:  # ru
                specific_instructions = (
                    "\n⚠️ Специальная инструкция для этого графика:\n"
                    "• Если есть лидирующий продукт (самый прибыльный), не просто предлагай продвигать его больше\n"
                    f"• Вместо этого, {lang_dict['combo_instruction']} (см. bottom_items в данных)\n"
                    "• Цель: увеличить продажи слабого продукта, используя популярность сильного продукта\n"
                    f"{bottom_items_text}"
                    "• Пример: '[Лидирующий продукт] - ваш самый прибыльный продукт. Рассмотрите предложение пакета: [Лидирующий продукт] + [один из менее популярных продуктов] по специальной цене'\n"
                )
        
        # מכירות לפי יום/שעה - התמקד בימים/שעות חלשים
        if "יום" in title or "שעה" in title or "שבוע" in title or "Day" in title or "Hour" in title or "Week" in title or "День" in title or "Час" in title or "Неделя" in title:
            weak_info = ""
            if isinstance(compact, dict):
                if "weak_day" in compact:
                    weak_day = compact.get("weak_day")
                    weak_sum = compact.get("weak_day_sum", 0)
                    currency_info = get_currency(lang)
                    currency_symbol = currency_info["symbol"]
                    if lang == "he":
                        weak_info = f"\n• היום החלש ביותר: {weak_day} ({currency_symbol}{weak_sum:.0f}) - זה הזמן למשוך לקוחות חדשים!\n"
                    elif lang == "en":
                        weak_info = f"\n• Weakest day: {weak_day} ({currency_symbol}{weak_sum:.0f}) - this is the time to attract new customers!\n"
                    else:  # ru
                        weak_info = f"\n• Самый слабый день: {weak_day} ({currency_symbol}{weak_sum:.0f}) - это время привлечь новых клиентов!\n"
                elif "weak_hour" in compact:
                    weak_hour = compact.get("weak_hour")
                    if lang == "he":
                        weak_info = f"\n• השעה החלשה ביותר: {weak_hour} - זה הזמן למשוך לקוחות חדשים!\n"
                    elif lang == "en":
                        weak_info = f"\n• Weakest hour: {weak_hour} - this is the time to attract new customers!\n"
                    else:  # ru
                        weak_info = f"\n• Самый слабый час: {weak_hour} - это время привлечь новых клиентов!\n"
            
            if lang == "he":
                specific_instructions = (
                    "\n⚠️ הוראה מיוחדת לגרף זה:\n"
                    "• אל תציע למשוך לקוחות בימים/שעות החזקים ביותר (יש כבר ביקוש גבוה)\n"
                    f"• במקום זה, {lang_dict['weak_instruction']}\n"
                    "• המטרה: למלא את הזמנים הריקים ולהגיע ללקוחות חדשים שלא מגיעים בשעות העמוסות\n"
                    f"{weak_info}"
                    "• דוגמה: '[יום/שעה חלש] הוא החלש ביותר. שקול להפעיל מבצע מיוחד ב[יום/שעה חלש] כדי למשוך לקוחות חדשים שלא מגיעים ב[ימים/שעות] החזקים'\n"
                )
            elif lang == "en":
                specific_instructions = (
                    "\n⚠️ Special instruction for this chart:\n"
                    "• Don't suggest attracting customers during the strongest days/hours (there's already high demand)\n"
                    f"• Instead, {lang_dict['weak_instruction']}\n"
                    "• Goal: fill empty times and reach new customers who don't come during busy hours\n"
                    f"{weak_info}"
                    "• Example: '[Weak day/hour] is the weakest. Consider running a special promotion on [weak day/hour] to attract new customers who don't come during [strong days/hours]'\n"
                )
            else:  # ru
                specific_instructions = (
                    "\n⚠️ Специальная инструкция для этого графика:\n"
                    "• Не предлагай привлекать клиентов в самые сильные дни/часы (уже есть высокий спрос)\n"
                    f"• Вместо этого, {lang_dict['weak_instruction']}\n"
                    "• Цель: заполнить пустые времена и привлечь новых клиентов, которые не приходят в загруженные часы\n"
                    f"{weak_info}"
                    "• Пример: '[Слабый день/час] - самый слабый. Рассмотрите запуск специальной акции в [слабый день/час], чтобы привлечь новых клиентов, которые не приходят в [сильные дни/часы]'\n"
                )
        
        # Создаем промпט + system‑сообщение на нужном языке
        if lang == "he":
            system_msg = "ענה תמיד אך ורק בעברית. אל תשתמש בשום שפה אחרת."
            prompt = (
                "אתה יועץ עסקי מומחה לחנויות קמעונאיות ומסעדות בישראל. "
                "תפקידך לעזור לבעל העסק להבין את הנתונים ולקבל החלטות חכמות.\n\n"
                "כללים:\n"
                f"• כתוב {lang_dict['example']}, כאילו אתה מדבר עם בעל מכולת או בית קפה\n"
                f"• {lang_dict['focus']} — מה הכי חשוב לדעת מהגרף הזה?\n"
                f"• {lang_dict['give']} שאפשר ליישם מחר בבוקר (לא תיאוריה!)\n"
                f"• אורך: {lang_dict['length']}\n"
                f"• {lang_dict['dont']} שכבר מופיעים בגרף — תן פרשנות\n"
                f"{specific_instructions}\n"
                f"כותרת הגרף: {title}\n"
                f"נתונים: {payload}"
            )
        elif lang == "en":
            system_msg = "Always respond strictly in English."
            prompt = (
                "You are a business consultant specializing in retail stores and restaurants in Israel. "
                "Your role is to help the business owner understand the data and make smart decisions.\n\n"
                "Rules:\n"
                f"• Write {lang_dict['example']}, as if you're talking to a grocery store or cafe owner\n"
                f"• {lang_dict['focus']} — what's the most important thing to know from this chart?\n"
                f"• {lang_dict['give']} that can be implemented tomorrow morning (not theory!)\n"
                f"• Length: {lang_dict['length']}\n"
                f"• {lang_dict['dont']} that already appear in the chart — provide interpretation\n"
                f"{specific_instructions}\n"
                f"Chart title: {title}\n"
                f"Data: {payload}"
            )
        else:  # ru
            system_msg = "Отвечай строго на русском языке. Не используй другие языки."
            prompt = (
                "Ты бизнес-консультант, специализирующийся на розничных магазинах и ресторанах в Израиле. "
                "Твоя роль - помочь владельцу бизнеса понять данные и принимать умные решения.\n\n"
                "Правила:\n"
                f"• Пиши {lang_dict['example']}, как будто разговариваешь с владельцем магазина или кафе\n"
                f"• {lang_dict['focus']} — что самое важное нужно знать из этого графика?\n"
                f"• {lang_dict['give']}, которую можно реализовать завтра утром (не теорию!)\n"
                f"• Длина: {lang_dict['length']}\n"
                f"• {lang_dict['dont']}, которые уже есть в графике — дай интерпретацию\n"
                f"{specific_instructions}\n"
                f"Название графика: {title}\n"
                f"Данные: {payload}"
            )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ]

        # ---- נסיון A1: Chat Completions עם max_completion_tokens ----
        try:
            print(f"📤 Chat.Completions call → {OPENAI_MODEL} | {title} | A1")
            r = _openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=180
            )
            txt = (r.choices[0].message.content or "").strip()
            if txt:
                return txt[:1200]
        except Exception as e:
            print("A1 failed:", e)

        # ---- נסיון A2: Chat Completions בלי max_* בכלל ----
        try:
            print(f"📤 Chat.Completions call → {OPENAI_MODEL} | {title} | A2")
            r = _openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages
            )
            txt = (r.choices[0].message.content or "").strip()
            if txt:
                return txt[:1200]
        except Exception as e:
            print("A2 failed:", e)

        # ---- נסיון B1: Responses API עם max_output_tokens ----
        try:
            print(f"📤 Responses.create → {OPENAI_MODEL} | {title} | B1")
            r = _openai_client.responses.create(
                model=OPENAI_MODEL,
                input=prompt,
                max_output_tokens=180
            )
            txt = getattr(r, "output_text", None)
            if not txt:
                try:
                    txt = (r.output[0].content[0].text or "").strip()
                except Exception:
                    txt = ""
            if txt:
                return txt[:1200]
        except Exception as e:
            print("B1 failed:", e)

        # ---- נסיון אחרון: Responses API בלי max_output_tokens ----
        try:
            print(f"📤 Responses.create → {OPENAI_MODEL} | {title} | B2")
            r = _openai_client.responses.create(model=OPENAI_MODEL, input=prompt)
            txt = getattr(r, "output_text", None)
            if not txt:
                try:
                    txt = (r.output[0].content[0].text or "").strip()
                except Exception:
                    txt = ""
            if txt:
                return txt[:1200]
        except Exception as e:
            print("B2 failed:", e)

        # אם כל הניסיונות נכשלים
        return ""
    except Exception as e:
        print("AI error (hard):", e)
        return ""



        print(f"📤 Calling OpenAI model={OPENAI_MODEL} for: {title}")
        # חשוב: ב-responses.create אין temperature בחלק מהדגמים → לא שולחים אותו
        r = _openai_client.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
            max_output_tokens=180,
        )
        text = (getattr(r, "output_text", "") or "").strip()
        if not text:
            print("ℹ️ Empty AI text, returning fallback ''")
            return ""
        return text[:1200]
    except Exception as e:
        # לא שוברים את הזרימה אם AI נפל
        print("AI error (soft):", e)
        return ""



from dataclasses import dataclass
from typing import Optional, Dict, Any
import math

@dataclass
class ROIParams:
    service_cost: float = 69.0           # עלות השירות PRO (₪69/חודש)
    month_days_assumption: float = 30.0  # להשלכה לחודש (אם טווח הדוח קצר)
    evening_hours: tuple = (17, 20)      # שעות ערב לבחינת פוטנציאל
    midday_hours: tuple = (11, 14)       # שעות חזקות להשוואה
    evening_target_ratio: float = 0.25   # יעד מציאותי: 25% מעוצמת הצהריים (לא 50%)
    weak_day_target: str = "median"      # bring weak day to 'median' of other days
    weak_day_achievable: float = 0.3     # רק 30% מהפער ניתן לסגירה ריאלית
    tail_boost_ratio: float = 0.05       # קידום זנב מוצרים: +5% (מציאותי יותר)
    tail_share_cutoff: float = 0.50      # “זנב” = המוצרים התחתונים שמהווים ~50% מההכנסות

def _days_in_df(df) -> int:
    if COL_DATE in df.columns:
        d = pd.to_datetime(df[COL_DATE], errors="coerce")
        return int(d.dt.normalize().nunique())
    return 0

def _month_multiplier(df, month_days_assumption):
    d = _days_in_df(df)
    return (month_days_assumption / d) if d > 0 else 1.0

def estimate_roi(df, params: ROIParams = ROIParams(), lang: str = "he") -> Dict[str, Any]:
    """
    מחשב ROI משוער מהדוח:
    - העלאת יום חלש לרמת הימים הרגילים
    - ניצול שעות ערב חלשות
    - קידום מוצרים חלשים (זנב)
    מחזיר פירוט סכומים חודשיים + ROI%.
    """
    # Получаем валюту из текущей сессии
    currency_info = get_currency(lang)
    currency_symbol = currency_info["symbol"]
    
    out = {"components": {}, "monthly_gain": 0.0, "service_cost": params.service_cost, "roi_percent": 0.0}

    # ננרמל סכומים
    safe_sum = pd.to_numeric(df.get(COL_SUM), errors="coerce").fillna(0.0)
    df2 = df.copy()
    df2[COL_SUM] = safe_sum

    # ---------- (א) יום חלש -> רמת הימים הרגילים ----------
        # ---------- (א) יום חלש -> רמת הימים הרגילים ----------
    gain_weakday = 0.0
    if COL_DATE in df2.columns:
        # נבנה day-of-week בעברית
        ser_date = pd.to_datetime(df2[COL_DATE], errors="coerce")
        by_day = df2.copy()
        by_day["__dow"] = ser_date.dt.dayofweek
        map_he = {0:"ראשון",1:"שני",2:"שלישי",3:"רביעי",4:"חמישי",5:"שישי",6:"שבת"}
        by_day["__dow_name"] = by_day["__dow"].map(map_he)

        if by_day["__dow_name"].notna().any():
            agg = (by_day.groupby("__dow_name", dropna=False)[COL_SUM]
                         .sum(numeric_only=True)
                         .astype(float)
                         .sort_values())
            if len(agg) >= 2:
                weak_day_name = agg.index[0]
                weak_val = float(agg.iloc[0])
                if params.weak_day_target == "median":
                    target = float(agg.median())
                else:
                    # ממוצע של השאר (לא כולל החלש ביותר)
                    target = float(agg.iloc[1:].mean()) if len(agg) > 1 else float(agg.mean())
                full_gap = max(0.0, target - weak_val)
                # רק חלק מהפער ניתן לסגירה באופן ריאלי (30%)
                achievable_factor = getattr(params, 'weak_day_achievable', 0.3)
                uplift_per_occurrence = full_gap * achievable_factor
                occurrences_per_month = 4.3  # ממוצע
                gain_weakday = uplift_per_occurrence * occurrences_per_month
                out["components"]["weak_day"] = {
                    "day": str(weak_day_name),
                    "current": weak_val,
                    "target": target,
                    "achievable_percent": int(achievable_factor * 100),
                    "occurrences_per_month": occurrences_per_month,
                    "monthly_gain": gain_weakday,
                    "note": f"פוטנציאל: סגירת ~{int(achievable_factor*100)}% מהפער לימים רגילים"
                }

            # אם אין יום־בשבוע, נדלג בשקט
    # ---------- (ב) שעות ערב חלשות ----------
    gain_evening = 0.0
    if COL_TIME in df2.columns:
        # נוסיף עמודת שעה אם חסרה
        if "שעה" not in df2.columns:
            try:
                df2["שעה"] = pd.to_datetime(df2[COL_TIME].astype(str), errors="coerce").dt.hour
            except Exception:
                df2["שעה"] = pd.to_numeric(df2[COL_TIME], errors="coerce")
        h = df2.dropna(subset=["שעה"]).copy()
        h["שעה"] = pd.to_numeric(h["שעה"], errors="coerce")
        st_m, en_m = params.midday_hours
        st_e, en_e = params.evening_hours
        mid = h[(h["שעה"] >= st_m) & (h["שעה"] <= en_m)][COL_SUM].sum()
        eve = h[(h["שעה"] >= st_e) & (h["שעה"] <= en_e)][COL_SUM].sum()
        # יעד: ערב יגיע ליחס כלשהו מהצהריים (למשל 50%)
        target_evening = (mid / max(1.0, (en_m - st_m + 1))) * (en_e - st_e + 1) * params.evening_target_ratio
        uplift_day = max(0.0, target_evening - eve)
        # לכפול במס׳ ימי פעילות בחודש (על בסיס הדוח)
        mult = _month_multiplier(df2, params.month_days_assumption)
        gain_evening = uplift_day * max(1.0, _days_in_df(df2)) * mult
        out["components"]["evening_hours"] = {
            "midday_sum": float(mid),
            "evening_sum": float(eve),
            "target_evening_per_day": float(target_evening),
            "uplift_per_day": float(uplift_day),
            "days_in_month_factor": float(max(1.0, _days_in_df(df2))*mult),
            "monthly_gain": float(gain_evening),
            "note": f"ניצול שעות {st_e}:00–{en_e}:00 לרמה של ~{int(params.evening_target_ratio*100)}% מעוצמת הצהריים"
        }

    # ---------- (ג) קידום “זנב מוצרים” ----------
    gain_tail = 0.0
    if COL_ITEM in df2.columns:
        rev = (df2.groupby(COL_ITEM, dropna=False)[COL_SUM].sum().reset_index()
                 .sort_values(COL_SUM, ascending=False))
        if not rev.empty:
            total_rev = rev[COL_SUM].sum()
            rev["cum_share"] = rev[COL_SUM].cumsum() / max(1.0, total_rev)
            # “זנב” = כל מה שמעבר ל־(1 - tail_share_cutoff) מהכנסות—כלומר התחתית
            # נבחר מוצרים שמרכיבים את ה־tail_share_cutoff התחתון של ההכנסות
            rev_sorted_asc = rev.sort_values(COL_SUM, ascending=True)
            rev_sorted_asc["cum_share_asc"] = rev_sorted_asc[COL_SUM].cumsum() / max(1.0, total_rev)
            tail = rev_sorted_asc[rev_sorted_asc["cum_share_asc"] <= params.tail_share_cutoff]
            tail_rev = tail[COL_SUM].sum() if not tail.empty else 0.0
            gain_tail = tail_rev * params.tail_boost_ratio * _month_multiplier(df2, params.month_days_assumption)
            out["components"]["tail_products"] = {
                "tail_share_cutoff": params.tail_share_cutoff,
                "tail_revenue_month_base": float(tail_rev * _month_multiplier(df2, params.month_days_assumption)),
                "boost_ratio": params.tail_boost_ratio,
                "monthly_gain": float(gain_tail),
                "note": "קידום מוצרים חלשים (זנב) בתוספת ~10%"
            }

    # ---------- סכימה ו-ROI ----------
    total_gain = float(gain_weakday + gain_evening + gain_tail)
    
    # 3 режима оценок: Conservative (0.6), Base (1.0), Optimistic (1.4)
    out["monthly_gain_base"] = total_gain
    out["monthly_gain_conservative"] = total_gain * 0.6
    out["monthly_gain_optimistic"] = total_gain * 1.4
    out["monthly_gain"] = total_gain  # Base по умолчанию для обратной совместимости
    out["roi_percent"] = (total_gain / max(1e-9, params.service_cost)) * 100.0
    out["roi_percent_conservative"] = (total_gain * 0.6 / max(1e-9, params.service_cost)) * 100.0
    out["roi_percent_optimistic"] = (total_gain * 1.4 / max(1e-9, params.service_cost)) * 100.0

    # Переводим текст в зависимости от языка
    # Маппинг дней недели с иврита на другие языки
    day_translation = {
        "he": {"ראשון": "ראשון", "שני": "שני", "שלישי": "שלישי", "רביעי": "רביעי", 
               "חמישי": "חמישי", "שישי": "שישי", "שבת": "שבת"},
        "en": {"ראשון": "Sunday", "שני": "Monday", "שלישי": "Tuesday", "רביעי": "Wednesday",
               "חמישי": "Thursday", "שישי": "Friday", "שבת": "Saturday"},
        "ru": {"ראשון": "Воскресенье", "שני": "Понедельник", "שלישי": "Вторник", "רביעי": "Среда",
               "חמישי": "Четверг", "שישי": "Пятница", "שבת": "Суббота"}
    }
    
    parts = []
    if "weak_day" in out["components"]:
        c = out["components"]["weak_day"]
        # Переводим день недели
        day_name_he = c['day']
        day_name = day_translation.get(lang, day_translation["he"]).get(day_name_he, day_name_he)
        
        if lang == "he":
            parts.append(f"יום חלש ('{day_name}') יעלה לרמת הימים הרגילים: +{c['monthly_gain']:,.0f} {currency_symbol}/חודש.")
        elif lang == "en":
            parts.append(f"Weak day ('{day_name}') raised to regular days level: +{currency_symbol}{c['monthly_gain']:,.0f}/month.")
        else:  # ru
            parts.append(f"Слабый день ('{day_name}') поднят до уровня обычных дней: +{currency_symbol}{c['monthly_gain']:,.0f}/месяц.")
    if "evening_hours" in out["components"]:
        c = out["components"]["evening_hours"]
        if lang == "he":
            parts.append(f"שעות ערב חלשות → יעד חדש: +{c['uplift_per_day']:,.0f} {currency_symbol} ליום × {int(c['days_in_month_factor']):d} ימים ≈ +{c['monthly_gain']:,.0f} {currency_symbol}/חודש.")
        elif lang == "en":
            parts.append(f"Weak evening hours → new target: +{currency_symbol}{c['uplift_per_day']:,.0f} per day × {int(c['days_in_month_factor']):d} days ≈ +{currency_symbol}{c['monthly_gain']:,.0f}/month.")
        else:  # ru
            parts.append(f"Слабые вечерние часы → новая цель: +{currency_symbol}{c['uplift_per_day']:,.0f} в день × {int(c['days_in_month_factor']):d} дней ≈ +{currency_symbol}{c['monthly_gain']:,.0f}/месяц.")
    if "tail_products" in out["components"]:
        c = out["components"]["tail_products"]
        if lang == "he":
            parts.append(f"קידום 'זנב מוצרים' (≈{int(params.tail_share_cutoff*100)}% מההכנסות) ב+{int(params.tail_boost_ratio*100)}% → +{c['monthly_gain']:,.0f} {currency_symbol}/חודש.")
        elif lang == "en":
            parts.append(f"Promoting 'tail products' (≈{int(params.tail_share_cutoff*100)}% of revenue) by +{int(params.tail_boost_ratio*100)}% → +{currency_symbol}{c['monthly_gain']:,.0f}/month.")
        else:  # ru
            parts.append(f"Продвижение 'хвоста продуктов' (≈{int(params.tail_share_cutoff*100)}% от выручки) на +{int(params.tail_boost_ratio*100)}% → +{currency_symbol}{c['monthly_gain']:,.0f}/месяц.")

    # Текстовый итог ROI по языкам
    # Стоимость услуги всегда $20 (в долларах)
    service_cost_display = "$20"
    
    if lang == "he":
        summary_text = (
            f"פוטנציאל שיפור חודשי (בתנאי שפועלים על התובנות): ~{total_gain:,.0f} {currency_symbol}. "
            f"עלות השירות: {service_cost_display}. "
            f"ROI תיאורטי: {out['roi_percent']:,.0f}%."
        )
        disclaimer = "⚠️ הערכה זו מבוססת על ניתוח הנתונים בלבד. התוצאות בפועל תלויות בפעולות שתנקטו."
    elif lang == "en":
        summary_text = (
            f"Monthly improvement potential (if you act on insights): ~{currency_symbol}{total_gain:,.0f}. "
            f"Service cost: {service_cost_display}. "
            f"Theoretical ROI: {out['roi_percent']:,.0f}%."
        )
        disclaimer = "⚠️ This estimate is based on data analysis only. Actual results depend on actions taken."
    else:  # ru
        summary_text = (
            f"Потенциал улучшения в месяц (при условии действий на основе инсайтов): ~{currency_symbol}{total_gain:,.0f}. "
            f"Стоимость услуги: {service_cost_display}. "
            f"Теоретический ROI: {out['roi_percent']:,.0f}%."
        )
        disclaimer = "⚠️ Эта оценка основана только на анализе данных. Фактические результаты зависят от предпринятых действий."

    out["text"] = " • ".join(parts + [summary_text, disclaimer])
    return out


def diagnose_traffic_vs_check(df, roi_data: dict, lang: str = "he") -> Dict[str, Any]:
    """
    Диагностика: слабый день/час из-за низкого трафика или низкого среднего чека?
    Возвращает инсайты и данные для визуализации.
    """
    insights = []
    chart_data = {}
    
    comps = roi_data.get("components", {})
    
    # 1. Диагностика слабого дня
    if "weak_day" in comps:
        weak = comps["weak_day"]
        day_name = weak.get("day", "")
        
        if COL_DATE in df.columns and COL_SUM in df.columns:
            ser_date = pd.to_datetime(df[COL_DATE], errors="coerce")
            df2 = df.copy()
            df2["__dow"] = ser_date.dt.dayofweek
            map_he = {0:"ראשון",1:"שני",2:"שלישי",3:"רביעי",4:"חמישי",5:"שישי",6:"שבת"}
            df2["__dow_name"] = df2["__dow"].map(map_he)
            
            # Находим слабый день
            weak_day_mask = df2["__dow_name"] == day_name
            weak_day_data = df2[weak_day_mask]
            
            # Находим средний день (медиана остальных)
            other_days = df2[~weak_day_mask]
            
            if not weak_day_data.empty and not other_days.empty:
                weak_transactions = len(weak_day_data)
                weak_revenue = weak_day_data[COL_SUM].sum()
                weak_avg_check = weak_revenue / max(1, weak_transactions)
                
                other_transactions = len(other_days)
                other_revenue = other_days[COL_SUM].sum()
                other_avg_check = other_revenue / max(1, other_transactions)
                
                # Сравнение
                traffic_ratio = weak_transactions / max(1, other_transactions / max(1, len(other_days["__dow_name"].unique())))
                check_ratio = weak_avg_check / max(1e-9, other_avg_check)
                
                chart_data["weak_day"] = {
                    "day": day_name,
                    "weak_transactions": int(weak_transactions),
                    "weak_avg_check": float(weak_avg_check),
                    "other_avg_transactions": float(other_transactions / max(1, len(other_days["__dow_name"].unique()))),
                    "other_avg_check": float(other_avg_check),
                    "traffic_ratio": float(traffic_ratio),
                    "check_ratio": float(check_ratio)
                }
                
                # Генерируем инсайты
                if traffic_ratio < 0.7 and check_ratio > 0.9:
                    # Низкий трафик, но чек нормальный
                    if lang == "he":
                        insights.append({
                            "type": "traffic",
                            "title": f"יום {day_name}: בעיית תנועה",
                            "text": f"מספר העסקאות נמוך ב-{int((1-traffic_ratio)*100)}% לעומת ימים אחרים, אך הממוצע לעסקה תקין. התמקדו במשיכת יותר לקוחות."
                        })
                    elif lang == "en":
                        insights.append({
                            "type": "traffic",
                            "title": f"{day_name}: Traffic Issue",
                            "text": f"Transaction count is {int((1-traffic_ratio)*100)}% lower than other days, but average check is normal. Focus on attracting more customers."
                        })
                    else:  # ru
                        insights.append({
                            "type": "traffic",
                            "title": f"{day_name}: Проблема с трафиком",
                            "text": f"Количество транзакций на {int((1-traffic_ratio)*100)}% ниже, чем в другие дни, но средний чек нормальный. Сосредоточьтесь на привлечении большего количества клиентов."
                        })
                elif check_ratio < 0.7 and traffic_ratio > 0.9:
                    # Низкий чек, но трафик нормальный
                    if lang == "he":
                        insights.append({
                            "type": "check",
                            "title": f"יום {day_name}: בעיית ממוצע",
                            "text": f"הממוצע לעסקה נמוך ב-{int((1-check_ratio)*100)}% לעומת ימים אחרים, אך מספר העסקאות תקין. התמקדו בהגדלת ערך העסקה."
                        })
                    elif lang == "en":
                        insights.append({
                            "type": "check",
                            "title": f"{day_name}: Average Check Issue",
                            "text": f"Average check is {int((1-check_ratio)*100)}% lower than other days, but transaction count is normal. Focus on increasing transaction value."
                        })
                    else:  # ru
                        insights.append({
                            "type": "check",
                            "title": f"{day_name}: Проблема со средним чеком",
                            "text": f"Средний чек на {int((1-check_ratio)*100)}% ниже, чем в другие дни, но количество транзакций нормальное. Сосредоточьтесь на увеличении стоимости транзакции."
                        })
                else:
                    # Обе проблемы
                    if lang == "he":
                        insights.append({
                            "type": "both",
                            "title": f"יום {day_name}: בעיות כפולות",
                            "text": f"גם מספר העסקאות וגם הממוצע לעסקה נמוכים. נדרש טיפול מקיף: משיכת לקוחות + הגדלת ערך."
                        })
                    elif lang == "en":
                        insights.append({
                            "type": "both",
                            "title": f"{day_name}: Dual Issues",
                            "text": f"Both transaction count and average check are low. Comprehensive approach needed: attract customers + increase value."
                        })
                    else:  # ru
                        insights.append({
                            "type": "both",
                            "title": f"{day_name}: Двойная проблема",
                            "text": f"И количество транзакций, и средний чек низкие. Требуется комплексный подход: привлечение клиентов + увеличение стоимости."
                        })
    
    # 2. Диагностика вечерних часов
    if "evening_hours" in comps and COL_TIME in df.columns:
        evening = comps["evening_hours"]
        st_e, en_e = 17, 20  # evening_hours по умолчанию
        
        try:
            df2 = df.copy()
            if "שעה" not in df2.columns:
                df2["שעה"] = pd.to_datetime(df2[COL_TIME].astype(str), errors="coerce").dt.hour
            df2["שעה"] = pd.to_numeric(df2["שעה"], errors="coerce")
            
            evening_data = df2[(df2["שעה"] >= st_e) & (df2["שעה"] <= en_e)]
            midday_data = df2[(df2["שעה"] >= 11) & (df2["שעה"] <= 14)]
            
            if not evening_data.empty and not midday_data.empty:
                eve_transactions = len(evening_data)
                eve_revenue = evening_data[COL_SUM].sum()
                eve_avg_check = eve_revenue / max(1, eve_transactions)
                
                mid_transactions = len(midday_data)
                mid_revenue = midday_data[COL_SUM].sum()
                mid_avg_check = mid_revenue / max(1, mid_transactions)
                
                traffic_ratio_eve = eve_transactions / max(1, mid_transactions)
                check_ratio_eve = eve_avg_check / max(1e-9, mid_avg_check)
                
                chart_data["evening_hours"] = {
                    "evening_transactions": int(eve_transactions),
                    "evening_avg_check": float(eve_avg_check),
                    "midday_transactions": int(mid_transactions),
                    "midday_avg_check": float(mid_avg_check),
                    "traffic_ratio": float(traffic_ratio_eve),
                    "check_ratio": float(check_ratio_eve)
                }
                
                if traffic_ratio_eve < 0.5:
                    if lang == "he":
                        insights.append({
                            "type": "traffic",
                            "title": "שעות ערב: תנועה נמוכה",
                            "text": f"מספר העסקאות בערב נמוך ב-{int((1-traffic_ratio_eve)*100)}% לעומת הצהריים. נדרש קידום פעילות ערב."
                        })
                    elif lang == "en":
                        insights.append({
                            "type": "traffic",
                            "title": "Evening Hours: Low Traffic",
                            "text": f"Evening transaction count is {int((1-traffic_ratio_eve)*100)}% lower than midday. Evening activity promotion needed."
                        })
                    else:  # ru
                        insights.append({
                            "type": "traffic",
                            "title": "Вечерние часы: Низкий трафик",
                            "text": f"Количество транзакций вечером на {int((1-traffic_ratio_eve)*100)}% ниже, чем днем. Требуется продвижение вечерней активности."
                        })
                elif check_ratio_eve < 0.7:
                    if lang == "he":
                        insights.append({
                            "type": "check",
                            "title": "שעות ערב: ממוצע נמוך",
                            "text": f"הממוצע לעסקה בערב נמוך ב-{int((1-check_ratio_eve)*100)}% לעומת הצהריים. נדרש שיפור ערך העסקה."
                        })
                    elif lang == "en":
                        insights.append({
                            "type": "check",
                            "title": "Evening Hours: Low Average",
                            "text": f"Evening average check is {int((1-check_ratio_eve)*100)}% lower than midday. Transaction value improvement needed."
                        })
                    else:  # ru
                        insights.append({
                            "type": "check",
                            "title": "Вечерние часы: Низкий средний чек",
                            "text": f"Средний чек вечером на {int((1-check_ratio_eve)*100)}% ниже, чем днем. Требуется улучшение стоимости транзакции."
                        })
        except Exception as e:
            print(f"Diagnosis evening hours error: {e}")
    
    return {"insights": insights, "chart_data": chart_data}


def generate_7day_action_plan(df, roi_data: dict, lang: str = "he") -> Dict[str, Any]:
    """
    Генерирует конкретный план действий на 7 дней для каждой найденной возможности.
    Возвращает план с метриками для отслеживания.
    """
    plans = []
    comps = roi_data.get("components", {})
    currency_info = get_currency(lang)
    currency_symbol = currency_info["symbol"]
    
    # Маппинг дней недели на разные языки
    day_translation = {
        "he": {"ראשון": "ראשון", "שני": "שני", "שלישי": "שלישי", "רביעי": "רביעי", 
               "חמישי": "חמישי", "שישי": "שישי", "שבת": "שבת"},
        "en": {"ראשון": "Sunday", "שני": "Monday", "שלישי": "Tuesday", "רביעי": "Wednesday",
               "חמישי": "Thursday", "שישי": "Friday", "שבת": "Saturday"},
        "ru": {"ראשון": "Воскресенье", "שני": "Понедельник", "שלישי": "Вторник", "רביעי": "Среда",
               "חמישי": "Четверг", "שישי": "Пятница", "שבת": "Суббота"}
    }
    
    # 1. План для слабого дня
    if "weak_day" in comps:
        weak = comps["weak_day"]
        day_name_he = weak.get("day", "")  # Исходное имя на иврите
        day_name = day_translation.get(lang, day_translation["he"]).get(day_name_he, day_name_he)  # Переводим на нужный язык
        current_revenue = weak.get("current", 0)
        target_revenue = weak.get("target", 0)
        
        if lang == "he":
            plan = {
                "category": f"יום {day_name}",
                "goal": f"העלאת מכירות ביום {day_name} ב-{int((target_revenue - current_revenue) * 0.3)} {currency_symbol}",
                "days": [
                    {"day": 1, "action": f"פרסם בפייסבוק/אינסטגרם על מבצע מיוחד ביום {day_name}", "measure": "מספר צפיות/לייקים", "check": "יום 2"},
                    {"day": 2, "action": "הכן חומרי פרסום (פוסטר, סטורי)", "measure": "חומרים מוכנים", "check": "יום 3"},
                    {"day": 3, "action": f"הפעל מבצע: הנחה 15% ביום {day_name}", "measure": "מספר לקוחות", "check": "יום 4"},
                    {"day": 4, "action": "עקוב אחר מספר העסקאות וההכנסה", "measure": "הכנסה יומית", "check": "יום 5"},
                    {"day": 5, "action": "בצע התאמות אם נדרש (שינוי הנחה/שעות)", "measure": "הכנסה יומית", "check": "יום 6"},
                    {"day": 6, "action": "המשך עם המבצע", "measure": "הכנסה יומית", "check": "יום 7"},
                    {"day": 7, "action": "סיכום: השווה הכנסה ליום {day_name} לפני ואחרי", "measure": "הכנסה שבועית", "check": "יום 8"}
                ],
                "metrics": {
                    "daily_revenue": f"מעקב יומי: {current_revenue:,.0f} → יעד: {target_revenue * 0.3 + current_revenue:,.0f} {currency_symbol}",
                    "transactions": "מספר עסקאות ביום",
                    "avg_check": "ממוצע לעסקה"
                }
            }
        elif lang == "en":
            plan = {
                "category": f"{day_name} Day",
                "goal": f"Increase {day_name} sales by {currency_symbol}{int((target_revenue - current_revenue) * 0.3):,.0f}",
                "days": [
                    {"day": 1, "action": f"Post on Facebook/Instagram about special promotion on {day_name}", "measure": "Views/likes count", "check": "Day 2"},
                    {"day": 2, "action": "Prepare marketing materials (poster, story)", "measure": "Materials ready", "check": "Day 3"},
                    {"day": 3, "action": f"Launch promotion: 15% discount on {day_name}", "measure": "Customer count", "check": "Day 4"},
                    {"day": 4, "action": "Track transaction count and revenue", "measure": "Daily revenue", "check": "Day 5"},
                    {"day": 5, "action": "Make adjustments if needed (change discount/hours)", "measure": "Daily revenue", "check": "Day 6"},
                    {"day": 6, "action": "Continue with promotion", "measure": "Daily revenue", "check": "Day 7"},
                    {"day": 7, "action": f"Summary: Compare {day_name} revenue before and after", "measure": "Weekly revenue", "check": "Day 8"}
                ],
                "metrics": {
                    "daily_revenue": f"Daily tracking: {currency_symbol}{current_revenue:,.0f} → target: {currency_symbol}{target_revenue * 0.3 + current_revenue:,.0f}",
                    "transactions": "Transaction count per day",
                    "avg_check": "Average per transaction"
                }
            }
        else:  # ru
            plan = {
                "category": f"День {day_name}",
                "goal": f"Увеличить продажи в {day_name} на {currency_symbol}{int((target_revenue - current_revenue) * 0.3):,.0f}",
                "days": [
                    {"day": 1, "action": f"Опубликуйте в Facebook/Instagram о специальной акции в {day_name}", "measure": "Количество просмотров/лайков", "check": "День 2"},
                    {"day": 2, "action": "Подготовьте рекламные материалы (постер, сторис)", "measure": "Материалы готовы", "check": "День 3"},
                    {"day": 3, "action": f"Запустите акцию: скидка 15% в {day_name}", "measure": "Количество клиентов", "check": "День 4"},
                    {"day": 4, "action": "Отслеживайте количество транзакций и выручку", "measure": "Дневная выручка", "check": "День 5"},
                    {"day": 5, "action": "Внесите корректировки при необходимости (измените скидку/часы)", "measure": "Дневная выручка", "check": "День 6"},
                    {"day": 6, "action": "Продолжайте акцию", "measure": "Дневная выручка", "check": "День 7"},
                    {"day": 7, "action": f"Итог: Сравните выручку {day_name} до и после", "measure": "Недельная выручка", "check": "День 8"}
                ],
                "metrics": {
                    "daily_revenue": f"Ежедневное отслеживание: {currency_symbol}{current_revenue:,.0f} → цель: {currency_symbol}{target_revenue * 0.3 + current_revenue:,.0f}",
                    "transactions": "Количество транзакций в день",
                    "avg_check": "Средний чек"
                }
            }
        plans.append(plan)
    
    # 2. План для вечерних часов
    if "evening_hours" in comps:
        evening = comps["evening_hours"]
        uplift_per_day = evening.get("uplift_per_day", 0)
        
        if lang == "he":
            plan = {
                "category": "שעות ערב (17:00-20:00)",
                "goal": f"הגברת פעילות ערב ב-{uplift_per_day:,.0f} {currency_symbol} ליום",
                "days": [
                    {"day": 1, "action": "הכרז על Happy Hour 17:00-19:00 (הנחה 20% על משקאות)", "measure": "מספר לקוחות בערב", "check": "יום 2"},
                    {"day": 2, "action": "פרסם בסטורי אינסטגרם על מבצע הערב", "measure": "צפיות בסטורי", "check": "יום 3"},
                    {"day": 3, "action": "הפעל מבצע 'After Work' לעובדי משרדים", "measure": "הכנסה ערב", "check": "יום 4"},
                    {"day": 4, "action": "עקוב אחר מספר העסקאות בשעות 17-20", "measure": "הכנסה ערב", "check": "יום 5"},
                    {"day": 5, "action": "התאם שעות/הנחה לפי התוצאות", "measure": "הכנסה ערב", "check": "יום 6"},
                    {"day": 6, "action": "המשך עם מבצע הערב", "measure": "הכנסה ערב", "check": "יום 7"},
                    {"day": 7, "action": "סיכום: השווה הכנסה ערב לפני ואחרי", "measure": "הכנסה שבועית ערב", "check": "יום 8"}
                ],
                "metrics": {
                    "daily_revenue": f"מעקב יומי ערב: יעד +{uplift_per_day:,.0f} {currency_symbol}",
                    "transactions": "מספר עסקאות בשעות 17-20",
                    "avg_check": "ממוצע לעסקה בערב"
                }
            }
        elif lang == "en":
            plan = {
                "category": "Evening Hours (17:00-20:00)",
                "goal": f"Increase evening activity by ${uplift_per_day:,.0f} per day",
                "days": [
                    {"day": 1, "action": "Announce Happy Hour 17:00-19:00 (20% discount on drinks)", "measure": "Evening customer count", "check": "Day 2"},
                    {"day": 2, "action": "Post Instagram story about evening promotion", "measure": "Story views", "check": "Day 3"},
                    {"day": 3, "action": "Launch 'After Work' promotion for office workers", "measure": "Evening revenue", "check": "Day 4"},
                    {"day": 4, "action": "Track transaction count during 17-20", "measure": "Evening revenue", "check": "Day 5"},
                    {"day": 5, "action": "Adjust hours/discount based on results", "measure": "Evening revenue", "check": "Day 6"},
                    {"day": 6, "action": "Continue evening promotion", "measure": "Evening revenue", "check": "Day 7"},
                    {"day": 7, "action": "Summary: Compare evening revenue before and after", "measure": "Weekly evening revenue", "check": "Day 8"}
                ],
                "metrics": {
                    "daily_revenue": f"Daily evening tracking: target +${uplift_per_day:,.0f}",
                    "transactions": "Transaction count during 17-20",
                    "avg_check": "Average per transaction (evening)"
                }
            }
        else:  # ru
            plan = {
                "category": "Вечерние часы (17:00-20:00)",
                "goal": f"Увеличить вечернюю активность на {currency_symbol}{uplift_per_day:,.0f} в день",
                "days": [
                    {"day": 1, "action": "Объявите Happy Hour 17:00-19:00 (скидка 20% на напитки)", "measure": "Количество клиентов вечером", "check": "День 2"},
                    {"day": 2, "action": "Опубликуйте Instagram story о вечерней акции", "measure": "Просмотры сторис", "check": "День 3"},
                    {"day": 3, "action": "Запустите акцию 'After Work' для офисных работников", "measure": "Вечерняя выручка", "check": "День 4"},
                    {"day": 4, "action": "Отслеживайте количество транзакций в 17-20", "measure": "Вечерняя выручка", "check": "День 5"},
                    {"day": 5, "action": "Скорректируйте часы/скидку по результатам", "measure": "Вечерняя выручка", "check": "День 6"},
                    {"day": 6, "action": "Продолжайте вечернюю акцию", "measure": "Вечерняя выручка", "check": "День 7"},
                    {"day": 7, "action": "Итог: Сравните вечернюю выручку до и после", "measure": "Недельная вечерняя выручка", "check": "День 8"}
                ],
                "metrics": {
                    "daily_revenue": f"Ежедневное отслеживание вечера: цель +{currency_symbol}{uplift_per_day:,.0f}",
                    "transactions": "Количество транзакций в 17-20",
                    "avg_check": "Средний чек (вечер)"
                }
            }
        plans.append(plan)
    
    # 3. План для товаров-аутсайдеров
    if "tail_products" in comps:
        tail = comps["tail_products"]
        monthly_gain = tail.get("monthly_gain", 0)
        
        if lang == "he":
            plan = {
                "category": "מוצרים חלשים",
                "goal": f"הגברת מכירות מוצרים חלשים ב-{monthly_gain:,.0f} {currency_symbol} לחודש",
                "days": [
                    {"day": 1, "action": "זהה 5-10 מוצרים עם מכירות נמוכות", "measure": "רשימת מוצרים", "check": "יום 2"},
                    {"day": 2, "action": "צור חבילות: מוצר חזק + מוצר חלש במחיר מיוחד", "measure": "מספר חבילות", "check": "יום 3"},
                    {"day": 3, "action": "הצג חבילות במיקום בולט (קופה/תפריט)", "measure": "מספר חבילות נמכרות", "check": "יום 4"},
                    {"day": 4, "action": "עקוב אחר מכירות החבילות", "measure": "מכירות חבילות", "check": "יום 5"},
                    {"day": 5, "action": "התאם מחירים/הרכב חבילות לפי תוצאות", "measure": "מכירות חבילות", "check": "יום 6"},
                    {"day": 6, "action": "המשך עם חבילות", "measure": "מכירות חבילות", "check": "יום 7"},
                    {"day": 7, "action": "סיכום: השווה מכירות מוצרים חלשים לפני ואחרי", "measure": "מכירות חבילות שבועיות", "check": "יום 8"}
                ],
                "metrics": {
                    "daily_revenue": f"מעקב יומי: מכירות מוצרים חלשים",
                    "transactions": "מספר חבילות נמכרות",
                    "avg_check": "ממוצע ערך חבילה"
                }
            }
        elif lang == "en":
            plan = {
                "category": "Weak Products",
                "goal": f"Increase weak product sales by ${monthly_gain:,.0f} per month",
                "days": [
                    {"day": 1, "action": "Identify 5-10 products with low sales", "measure": "Product list", "check": "Day 2"},
                    {"day": 2, "action": "Create packages: strong product + weak product at special price", "measure": "Number of packages", "check": "Day 3"},
                    {"day": 3, "action": "Display packages in prominent location (counter/menu)", "measure": "Packages sold", "check": "Day 4"},
                    {"day": 4, "action": "Track package sales", "measure": "Package sales", "check": "Day 5"},
                    {"day": 5, "action": "Adjust prices/package composition based on results", "measure": "Package sales", "check": "Day 6"},
                    {"day": 6, "action": "Continue with packages", "measure": "Package sales", "check": "Day 7"},
                    {"day": 7, "action": "Summary: Compare weak product sales before and after", "measure": "Weekly package sales", "check": "Day 8"}
                ],
                "metrics": {
                    "daily_revenue": "Daily tracking: weak product sales",
                    "transactions": "Number of packages sold",
                    "avg_check": "Average package value"
                }
            }
        else:  # ru
            plan = {
                "category": "Слабые товары",
                "goal": f"Увеличить продажи слабых товаров на {currency_symbol}{monthly_gain:,.0f} в месяц",
                "days": [
                    {"day": 1, "action": "Определите 5-10 товаров с низкими продажами", "measure": "Список товаров", "check": "День 2"},
                    {"day": 2, "action": "Создайте пакеты: сильный товар + слабый товар по специальной цене", "measure": "Количество пакетов", "check": "День 3"},
                    {"day": 3, "action": "Разместите пакеты на видном месте (касса/меню)", "measure": "Проданные пакеты", "check": "День 4"},
                    {"day": 4, "action": "Отслеживайте продажи пакетов", "measure": "Продажи пакетов", "check": "День 5"},
                    {"day": 5, "action": "Скорректируйте цены/состав пакетов по результатам", "measure": "Продажи пакетов", "check": "День 6"},
                    {"day": 6, "action": "Продолжайте с пакетами", "measure": "Продажи пакетов", "check": "День 7"},
                    {"day": 7, "action": "Итог: Сравните продажи слабых товаров до и после", "measure": "Недельные продажи пакетов", "check": "День 8"}
                ],
                "metrics": {
                    "daily_revenue": "Ежедневное отслеживание: продажи слабых товаров",
                    "transactions": "Количество проданных пакетов",
                    "avg_check": "Средняя стоимость пакета"
                }
            }
        plans.append(plan)
    
    return {"plans": plans}


def generate_action_items(df, roi_data: dict, lang: str = "he") -> list:
    """
    יוצר רשימת פעולות קונקרטיות ומעשיות על בסיס ניתוח הנתונים.
    מחזיר רשימה של dicts: [{priority, category, action, impact, how_to}]
    """
    # Получаем символ валюты
    currency_info = get_currency(lang)
    currency_symbol = currency_info["symbol"]
    
    # Маппинг дней недели на разные языки
    day_translation = {
        "he": {"ראשון": "ראשון", "שני": "שני", "שלישי": "שלישי", "רביעי": "רביעי", 
               "חמישי": "חמישי", "שישי": "שישי", "שבת": "שבת"},
        "en": {"ראשון": "Sunday", "שני": "Monday", "שלישי": "Tuesday", "רביעי": "Wednesday",
               "חמישי": "Thursday", "שישי": "Friday", "שבת": "Saturday"},
        "ru": {"ראשון": "Воскресенье", "שני": "Понедельник", "שלישי": "Вторник", "רביעי": "Среда",
               "חמישי": "Четверг", "שישי": "Пятница", "שבת": "Суббота"}
    }
    
    actions = []
    comps = roi_data.get("components", {})
    
    # 1. יום חלש - המלצה ספציפית
    if "weak_day" in comps:
        weak = comps["weak_day"]
        day_name_he = weak.get("day", "")  # Исходное имя на иврите
        day_name = day_translation.get(lang, day_translation["he"]).get(day_name_he, day_name_he)  # Переводим на нужный язык
        current = weak.get("current", 0)
        target = weak.get("target", 0)
        gap_pct = int((1 - current / max(1, target)) * 100) if target > 0 else 0
        
        # Переводим рекомендации в зависимости от языка
        if lang == "he":
            day_actions = {
                "ראשון": "הפעל מבצע 'פתיחת שבוע' - קפה + מאפה במחיר מיוחד",
                "שני": "יום Happy Hour מוקדם (11:00-14:00) - הנחה 15% על ארוחות",
                "שלישי": "יום נאמנות - כפל נקודות למועדון",
                "רביעי": "מבצע 'באמצע השבוע' - מנה שנייה ב-50%",
                "חמישי": "הכנה לסופ\"ש - מבצע משפחות",
                "שישי": "מבצע בוקר מוקדם (עד 10:00) - הנחה 20%",
                "שבת": "ארוחת שבת משפחתית - מנה ילדים חינם",
            }
            category = "📅 יום חלש"
            title = f"חזק את יום {day_name}"
            default_action = f"הפעל מבצע מיוחד ביום {day_name}"
            impact = f"פוטנציאל: עד +{currency_symbol}{weak.get('monthly_gain', 0):,.0f}/חודש"
            how_to = [
                f"הפער מהימים הרגילים: ~{gap_pct}%",
                "פרסם בסושיאל יום לפני",
                "הדגש בשילוט בחנות",
                "שלח SMS/וואטסאפ ללקוחות נאמנים"
            ]
        elif lang == "en":
            day_actions = {
                "ראשון": "Launch 'Week Opening' promotion - coffee + pastry at special price",
                "שני": "Early Happy Hour day (11:00-14:00) - 15% discount on meals",
                "שלישי": "Loyalty day - double points for club members",
                "רביעי": "'Midweek' promotion - second dish at 50%",
                "חמישי": "Weekend prep - family promotion",
                "שישי": "Early morning promotion (until 10:00) - 20% discount",
                "שבת": "Family Shabbat meal - free kids' meal",
            }
            category = "📅 Weak Day"
            title = f"Strengthen {day_name} day"
            default_action = f"Launch special promotion on {day_name}"
            impact = f"Potential: up to +{currency_symbol}{weak.get('monthly_gain', 0):,.0f}/month"
            how_to = [
                f"Gap from regular days: ~{gap_pct}%",
                "Post on social media a day before",
                "Highlight in store signage",
                "Send SMS/WhatsApp to loyal customers"
            ]
        else:  # ru
            day_actions = {
                "ראשון": "Запустите акцию 'Открытие недели' - кофе + выпечка по специальной цене",
                "שני": "День раннего Happy Hour (11:00-14:00) - скидка 15% на блюда",
                "שלישי": "День лояльности - двойные баллы для клуба",
                "רביעי": "Акция 'Середина недели' - второе блюдо за 50%",
                "חמישי": "Подготовка к выходным - семейная акция",
                "שישי": "Акция раннего утра (до 10:00) - скидка 20%",
                "שבת": "Семейная субботняя трапеза - детское блюдо бесплатно",
            }
            category = "📅 Слабый день"
            title = f"Усильте день {day_name}"
            default_action = f"Запустите специальную акцию в день {day_name}"
            impact = f"Потенциал: до +{currency_symbol}{weak.get('monthly_gain', 0):,.0f}/месяц"
            how_to = [
                f"Разрыв с обычными днями: ~{gap_pct}%",
                "Опубликуйте в соцсетях за день до",
                "Выделите в вывеске магазина",
                "Отправьте SMS/WhatsApp постоянным клиентам"
            ]
        
        actions.append({
            "priority": 1,
            "category": category,
            "title": title.replace(day_name_he, day_name) if day_name != day_name_he else title,  # Заменяем иврит на переведенное имя в title
            "action": day_actions.get(day_name_he, default_action).replace(day_name_he, day_name) if day_name != day_name_he else day_actions.get(day_name_he, default_action),  # Используем иврит для поиска, но заменяем на переведенное
            "impact": impact,
            "how_to": how_to
        })
    
    # 2. שעות ערב חלשות
    if "evening_hours" in comps:
        eve = comps["evening_hours"]
        midday = eve.get("midday_sum", 0)
        evening = eve.get("evening_sum", 0)
        
        if midday > 0 and evening < midday * 0.4:  # ערב חלש משמעותית
            actions.append({
                "priority": 2,
                "category": "🌙 שעות ערב" if lang == "he" else ("🌙 Evening Hours" if lang == "en" else "🌙 Вечерние часы"),
                "title": "הגבר פעילות בערב (17:00-20:00)" if lang == "he" else ("Increase evening activity (17:00-20:00)" if lang == "en" else "Увеличьте активность вечером (17:00-20:00)"),
                "action": "הפעל Happy Hour או מבצע ערב" if lang == "he" else ("Launch Happy Hour or evening promotion" if lang == "en" else "Запустите Happy Hour или вечернюю акцию"),
                "impact": f"פוטנציאל: עד +{currency_symbol}{eve.get('monthly_gain', 0):,.0f}/חודש" if lang == "he" else (f"Potential: up to +{currency_symbol}{eve.get('monthly_gain', 0):,.0f}/month" if lang == "en" else f"Потенциал: до +{currency_symbol}{eve.get('monthly_gain', 0):,.0f}/месяц"),
                "how_to": [
                    "Happy Hour 17:00-19:00 - הנחה 20% על משקאות",
                    "מבצע 'After Work' לעובדי משרדים",
                    "תאורה ומוזיקה מתאימים לערב",
                    "תפריט ערב מיוחד (טאפאס, שיתוף)"
                ] if lang == "he" else ([
                    "Happy Hour 17:00-19:00 - 20% discount on drinks",
                    "'After Work' promotion for office workers",
                    "Appropriate lighting and music for evening",
                    "Special evening menu (tapas, sharing)"
                ] if lang == "en" else [
                    "Happy Hour 17:00-19:00 - скидка 20% на напитки",
                    "Акция 'After Work' для офисных работников",
                    "Подходящее освещение и музыка для вечера",
                    "Специальное вечернее меню (тапас, на двоих)"
                ])
            })
    
    # 3. מוצרים חלשים (זנב)
    if "tail_products" in comps:
        tail = comps["tail_products"]
        if lang == "he":
            category = "📦 מוצרים"
            title = "הגבר מכירות מוצרים חלשים"
            action = "צור חבילות או מבצעי קומבו"
            impact = f"פוטנציאל: עד +{currency_symbol}{tail.get('monthly_gain', 0):,.0f}/חודש"
            how_to = [
                "צור קומבו: מוצר חזק + מוצר חלש",
                "הצע כ'תוספת' במחיר מיוחד",
                "מקם בגובה העיניים / ליד הקופה",
                "הכשר צוות להציע אקטיבית"
            ]
        elif lang == "en":
            category = "📦 Products"
            title = "Increase sales of weak products"
            action = "Create packages or combo deals"
            impact = f"Potential: up to +{currency_symbol}{tail.get('monthly_gain', 0):,.0f}/month"
            how_to = [
                "Create combo: strong product + weak product",
                "Offer as 'add-on' at special price",
                "Place at eye level / near checkout",
                "Train staff to actively suggest"
            ]
        else:  # ru
            category = "📦 Продукты"
            title = "Увеличьте продажи слабых продуктов"
            action = "Создайте пакеты или комбо-предложения"
            impact = f"Потенциал: до +{currency_symbol}{tail.get('monthly_gain', 0):,.0f}/месяц"
            how_to = [
                "Создайте комбо: сильный продукт + слабый продукт",
                "Предложите как 'дополнение' по специальной цене",
                "Разместите на уровне глаз / у кассы",
                "Обучите персонал активно предлагать"
            ]
        
        actions.append({
            "priority": 3,
            "category": category,
            "title": title,
            "action": action,
            "impact": impact,
            "how_to": how_to
        })
    
    # 4. המלצות כלליות תמיד
    # בדוק אם יש נתוני מוצרים
    if COL_ITEM in df.columns:
        top_product = df.groupby(COL_ITEM)[COL_SUM].sum().idxmax() if not df.empty else None
        if top_product:
            if lang == "he":
                category = "⭐ מוצר מוביל"
                title = f"נצל את ההצלחה של '{top_product}'"
                action = "הרחב את קו המוצרים המוביל"
                impact = "שמור על הביקוש + הגדל סל קנייה"
                how_to = [
                    f"צור וריאציות של '{top_product}'",
                    "הצע גרסה פרימיום במחיר גבוה יותר",
                    "צור חבילה עם מוצרים משלימים",
                    "ודא שתמיד במלאי!"
                ]
            elif lang == "en":
                category = "⭐ Leading Product"
                title = f"Leverage the success of '{top_product}'"
                action = "Expand the leading product line"
                impact = "Maintain demand + increase basket size"
                how_to = [
                    f"Create variations of '{top_product}'",
                    "Offer premium version at higher price",
                    "Create package with complementary products",
                    "Ensure always in stock!"
                ]
            else:  # ru
                category = "⭐ Ведущий продукт"
                title = f"Используйте успех '{top_product}'"
                action = "Расширьте линейку ведущих продуктов"
                impact = "Поддерживайте спрос + увеличивайте размер корзины"
                how_to = [
                    f"Создайте вариации '{top_product}'",
                    "Предложите премиум-версию по более высокой цене",
                    "Создайте пакет с дополнительными продуктами",
                    "Убедитесь, что всегда в наличии!"
                ]
            
            actions.append({
                "priority": 4,
                "category": category,
                "title": title,
                "action": action,
                "impact": impact,
                "how_to": how_to
            })
    
    # 5. טיפ להגדלת עסקה ממוצעת
    if COL_SUM in df.columns:
        avg_transaction = df[COL_SUM].mean() if not df.empty else 0
        if avg_transaction > 0:
            target_increase = avg_transaction * 0.15  # יעד: +15%
            if lang == "he":
                category = "💰 הגדלת סל"
                title = f"הגדל עסקה ממוצעת ב-15%"
                action = f"יעד: מ-{currency_symbol}{avg_transaction:.0f} ל-{currency_symbol}{avg_transaction + target_increase:.0f}"
                impact = f"פוטנציאל: +{currency_symbol}{target_increase * 30:.0f}/חודש (30 עסקאות/יום)"
                how_to = [
                    "הצע תוספות: 'רוצה להוסיף X?'",
                    "Upsell: 'במעט יותר תקבל גרסה גדולה'",
                    "מבצע 'קנה ב-X קבל Y חינם'",
                    "הכשר צוות למכירה אקטיבית"
                ]
            elif lang == "en":
                category = "💰 Basket Increase"
                title = f"Increase average transaction by 15%"
                action = f"Target: from {currency_symbol}{avg_transaction:.0f} to {currency_symbol}{avg_transaction + target_increase:.0f}"
                impact = f"Potential: +{currency_symbol}{target_increase * 30:.0f}/month (30 transactions/day)"
                how_to = [
                    "Suggest add-ons: 'Would you like to add X?'",
                    "Upsell: 'For a bit more you get a large size'",
                    "Promotion 'Buy X get Y free'",
                    "Train staff for active selling"
                ]
            else:  # ru
                category = "💰 Увеличение корзины"
                title = f"Увеличьте среднюю транзакцию на 15%"
                action = f"Цель: с {currency_symbol}{avg_transaction:.0f} до {currency_symbol}{avg_transaction + target_increase:.0f}"
                impact = f"Потенциал: +{currency_symbol}{target_increase * 30:.0f}/месяц (30 транзакций/день)"
                how_to = [
                    "Предлагайте дополнения: 'Хотите добавить X?'",
                    "Апселл: 'За немного больше получите большой размер'",
                    "Акция 'Купите X получите Y бесплатно'",
                    "Обучите персонал активным продажам"
                ]
            
            actions.append({
                "priority": 5,
                "category": category,
                "title": title,
                "action": action,
                "impact": impact,
                "how_to": how_to
            })
    
    return sorted(actions, key=lambda x: x["priority"])


    # Fallback – טקסט גנרי נוח
    return f"{title}: לפי הנתונים, הביצועים מרוכזים סביב הערכים הבולטים בתקציר. " \
           f"בדקו שעות/ימים חזקים לניצול, וחזקו מוצרים מובילים. נסו גם חבילות/מבצעים לשעות חלשות."

# ====== שמירת מצב אחרון לייצוא PDF (MVP) ======
LAST_EXPORT = {
    "generated_at": None,    # datetime
    "lang": "he",            # язык, на котором был выполнен анализ
    "plots": [],             # [{filename,title,note,ai}]
    "summary": ""            # טקסט קצר
}

# -----------------------------------------------------------------------------------
def _clean_plots_dir():
    """Clean old plot files, but keep recent ones (last 5 minutes)"""
    if os.path.exists(PLOTS_DIR):
        import time
        current_time = time.time()
        for f in os.listdir(PLOTS_DIR):
            try:
                file_path = os.path.join(PLOTS_DIR, f)
                # Keep files that are less than 5 minutes old
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 300:  # 5 minutes
                        os.remove(file_path)
                        print(f"🗑️ Removed old plot: {f} (age: {file_age:.0f}s)")
            except Exception as e:
                print(f"⚠️ Error removing {f}: {e}")

def _save_fig(fig, filename):
    path = os.path.join(PLOTS_DIR, filename)
    # Ensure directory exists
    os.makedirs(PLOTS_DIR, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    # Verify file was saved
    if os.path.exists(path):
        file_size = os.path.getsize(path)
        print(f"✅ Saved plot: {filename} ({file_size} bytes) to {path}")
    else:
        print(f"❌ Failed to save plot: {filename} to {path}")
    return filename

def _read_report(file_storage_or_path):
    """
    קריאת דוח מכל פורמט נפוץ של קופות בישראל:
    - CSV/TSV/TXT עם זיהוי מפריד אוטומטי
    - Excel (xlsx, xls, xlsm, xlsb)
    - ODS (OpenDocument - LibreOffice)
    - JSON (מערך או אובייקט עם נתונים)
    - XML (טבלאי)
    תמיכה בקידודים: UTF-8, UTF-8-BOM, Windows-1255, ISO-8859-8
    """
    import io
    import json as json_lib
    import pandas as pd

    # -------------------------------------------------
    # פונקציות עזר לקידודים עבריים
    # -------------------------------------------------
    def _read_text_with_encoding(data_bytes):
        """ניסיון לקרוא עם קידודים שונים לעברית, רוסית ואנגלית"""
        encodings = [
            'utf-8-sig', 'utf-8',  # UTF-8 с BOM и без
            'windows-1251', 'cp1251',  # Русская кодировка
            'windows-1255', 'iso-8859-8', 'cp1255',  # Иврит
            'latin-1', 'iso-8859-1',  # Западноевропейская
            'cp866', 'koi8-r'  # Дополнительные русские кодировки
        ]
        for enc in encodings:
            try:
                return data_bytes.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        # fallback
        return data_bytes.decode('utf-8', errors='replace')

    def _read_csv_smart(data_bytes):
        """קריאת CSV/TSV/TXT עם זיהוי אוטומטי של מפריד וקידוד"""
        text = _read_text_with_encoding(data_bytes)
        # ניסיון עם מפרידים שונים
        for sep in [None, ',', '\t', ';', '|']:
            try:
                df = pd.read_csv(
                    io.StringIO(text),
                    sep=sep,
                    engine="python" if sep is None else "c",
                    on_bad_lines="skip",
                )
                if len(df.columns) > 1:  # הצלחנו לפצל לעמודות
                    return df
            except Exception:
                continue
        # fallback אחרון
        return pd.read_csv(io.StringIO(text), sep=None, engine="python", on_bad_lines="skip")

    def _read_json_to_df(data_bytes):
        """קריאת JSON למבנה DataFrame"""
        text = _read_text_with_encoding(data_bytes)
        obj = json_lib.loads(text)
        # אם זה מערך של אובייקטים
        if isinstance(obj, list):
            return pd.DataFrame(obj)
        # אם יש מפתח עם מערך (למשל {"data": [...], "rows": [...], "transactions": [...]})
        if isinstance(obj, dict):
            for key in ['data', 'rows', 'transactions', 'sales', 'items', 'records']:
                if key in obj and isinstance(obj[key], list):
                    return pd.DataFrame(obj[key])
            # אם זה dict עם ערכים שהם מערכים (columns style)
            return pd.DataFrame(obj)
        raise ValueError("לא ניתן לפרש את מבנה ה-JSON")

    def _read_xml_to_df(data_bytes):
        """קריאת XML למבנה DataFrame"""
        text = _read_text_with_encoding(data_bytes)
        try:
            # pandas יכול לקרוא XML ישירות
            return pd.read_xml(io.StringIO(text))
        except Exception:
            # fallback: ניסיון עם ElementTree
            import xml.etree.ElementTree as ET
            root = ET.fromstring(text)
            rows = []
            for child in root:
                row = {}
                for elem in child:
                    row[elem.tag] = elem.text
                if row:
                    rows.append(row)
            if rows:
                return pd.DataFrame(rows)
            raise ValueError("לא ניתן לפרש את מבנה ה-XML")

    # -------------------------------------------------
    # 1) קריאה לקובץ (קלט יכול להיות FileStorage או נתיב)
    # -------------------------------------------------
    if hasattr(file_storage_or_path, "filename"):  # Flask FileStorage
        filename = file_storage_or_path.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        data = file_storage_or_path.read()

        if ext in (".xlsx", ".xlsm"):
            df = pd.read_excel(io.BytesIO(data), engine="openpyxl")
        elif ext == ".xlsb":
            df = pd.read_excel(io.BytesIO(data), engine="pyxlsb")
        elif ext == ".xls":
            df = pd.read_excel(io.BytesIO(data), engine="xlrd")
        elif ext == ".ods":
            df = pd.read_excel(io.BytesIO(data), engine="odf")
        elif ext == ".json":
            df = _read_json_to_df(data)
        elif ext == ".xml":
            df = _read_xml_to_df(data)
        else:  # .csv, .tsv, .txt ועוד
            df = _read_csv_smart(data)

    else:  # נתיב לקובץ
        path = str(file_storage_or_path)
        ext = os.path.splitext(path)[1].lower()

        if ext in (".xlsx", ".xlsm"):
            df = pd.read_excel(path, engine="openpyxl")
        elif ext == ".xlsb":
            df = pd.read_excel(path, engine="pyxlsb")
        elif ext == ".xls":
            df = pd.read_excel(path, engine="xlrd")
        elif ext == ".ods":
            df = pd.read_excel(path, engine="odf")
        elif ext == ".json":
            with open(path, "rb") as f:
                df = _read_json_to_df(f.read())
        elif ext == ".xml":
            with open(path, "rb") as f:
                df = _read_xml_to_df(f.read())
        else:  # .csv, .tsv, .txt
            with open(path, "rb") as f:
                df = _read_csv_smart(f.read())

    # Проверка что DataFrame создан и не пустой
    if df is None:
        raise ValueError("לא ניתן לקרוא את הקובץ - DataFrame הוא None")
    
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"הקובץ לא הוחזר כ-DataFrame. סוג: {type(df)}")
    
    if df.empty:
        raise ValueError("הקובץ ריק - אין נתונים")
    
    if len(df.columns) == 0:
        raise ValueError("הקובץ לא מכיל עמודות")

    # ניקוי רווחים בכותרות
    df.columns = df.columns.astype(str).str.strip()

    # -----------------------------------------
    # 2) מיפוי שמות עמודות נפוצים לשמות הסטנדרטיים
    # -----------------------------------------
    # בונה מילון חיפוש מנורמל (lowercase, ללא רווחים מיותרים, ללא סימנים מיוחדים)
    def _normalize_col_name(s):
        """מנרמל שם עמודה לחיפוש"""
        s = str(s).strip().lower()
        s = s.replace("_", " ").replace("-", " ")
        # מסיר סוגריים וסימני מטבע (включая рубль ₽)
        s = re.sub(r'[₪$€₽£¥\(\)\[\]]', '', s)
        # מסיר символы № и другие специальные символы
        s = re.sub(r'[№#]', '', s)
        # מסיר רווחים כפולים
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    # בונה מפה מנורמלת
    normalized_map = {}
    for key, val in COLUMN_MAP.items():
        normalized_map[_normalize_col_name(key)] = val

    renamed = {}
    # Сохраняем информацию о колонках, которые будут переименованы в COL_SUM
    cols_to_sum = []
    
    for col in df.columns:
        # ניסיון 1: התאמה מדויקת
        if col in COLUMN_MAP:
            new_name = COLUMN_MAP[col]
            renamed[col] = new_name
            if new_name == COL_SUM:
                cols_to_sum.append(col)
            continue
        # ניסיון 2: התאמה מנורמלת
        norm = _normalize_col_name(col)
        if norm in normalized_map:
            new_name = normalized_map[norm]
            renamed[col] = new_name
            if new_name == COL_SUM:
                cols_to_sum.append(col)
            continue
        # ניסיון 3: חיפוש חלקי (אם שם העמודה מכיל מילת מפתח)
        for key, val in COLUMN_MAP.items():
            if key in col or col in key:
                renamed[col] = val
                if val == COL_SUM:
                    cols_to_sum.append(col)
                break

    # Если несколько колонок маппятся в COL_SUM, выбираем приоритетную
    if len(cols_to_sum) > 1:
        # Приоритет: "Итого" > "Сумма_до_скидки" > остальные
        priority_keywords = [("итого", 1), ("total", 1), ("סה\"כ", 1), ("סהכ", 1), 
                            ("сумма_до_скидки", 2), ("сумма до скидки", 2)]
        
        selected_col = None
        selected_priority = 999
        
        for orig_col in cols_to_sum:
            orig_lower = str(orig_col).lower()
            for keyword, priority in priority_keywords:
                if keyword in orig_lower and priority < selected_priority:
                    selected_col = orig_col
                    selected_priority = priority
                    break
        
        # Если нашли приоритетную, переименовываем остальные в другое имя
        if selected_col:
            for col in cols_to_sum:
                if col != selected_col:
                    # Переименовываем в временное имя, чтобы не создавать дубликат
                    renamed[col] = f"{COL_SUM}_alt_{cols_to_sum.index(col)}"
        else:
            # Если не нашли приоритетную, используем первую
            for col in cols_to_sum[1:]:
                renamed[col] = f"{COL_SUM}_alt_{cols_to_sum.index(col)}"

    df.rename(columns=renamed, inplace=True)
    
    # Удаляем временные альтернативные колонки
    alt_cols = [col for col in df.columns if col.startswith(f"{COL_SUM}_alt_")]
    if alt_cols:
        df.drop(columns=alt_cols, inplace=True)

    # DEBUG: הדפסת עמודות לאבחון
    print(f"📋 עמודות מקוריות: {list(df.columns)}")
    print(f"📋 מיפויים שבוצעו: {renamed}")

    # -------------------------------------------------------
    # 3) פיצול datetime -> תאריך/שעה אם קיימת עמודה משולבת
    # -------------------------------------------------------
    if "datetime" in df.columns or "תאריך-שעה" in df.columns:
        col = "datetime" if "datetime" in df.columns else "תאריך-שעה"
        dt = pd.to_datetime(df[col], errors="coerce")
        df[COL_DATE] = dt.dt.date
        df[COL_TIME] = dt.dt.time
    
    # 3.1) Объединение отдельных колонок "Дата" и "Время" в COL_TIME
    # Если есть COL_DATE и отдельная колонка "Время", но нет COL_TIME
    if COL_DATE in df.columns and COL_TIME not in df.columns:
        # Ищем колонку с временем (может быть "Время", "time", "שעה" и т.д.)
        time_col = None
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if col_lower in ["время", "time", "שעה", "hour", "זמן"]:
                time_col = col
                break
        
        if time_col:
            # Объединяем дату и время
            try:
                date_str = df[COL_DATE].astype(str)
                time_str = df[time_col].astype(str).str.strip()
                # Пробуем создать datetime
                datetime_str = date_str + " " + time_str
                dt = pd.to_datetime(datetime_str, errors="coerce")
                # Если успешно, используем это как COL_TIME
                if dt.notna().any():
                    df[COL_TIME] = dt.dt.time if hasattr(dt.dt, 'time') else dt
                else:
                    # Если не получилось, просто используем колонку времени
                    df[COL_TIME] = df[time_col]
            except Exception as e:
                print(f"⚠️ Не удалось объединить дату и время: {e}")
                # Используем только колонку времени
                df[COL_TIME] = df[time_col]

    # -------------------------------------------------------
    # 3.5) חישוב עמודת סכום אם חסרה אבל יש מחיר וכמות
    # -------------------------------------------------------
    if COL_SUM not in df.columns:
        # אם יש מחיר ליחידה וכמות - נחשב סכום
        if COL_UNIT in df.columns and COL_QTY in df.columns:
            price = pd.to_numeric(df[COL_UNIT], errors="coerce").fillna(0)
            qty = pd.to_numeric(df[COL_QTY], errors="coerce").fillna(0)
            # Убеждаемся что результат - Series
            result = (price * qty).round(2)
            if isinstance(result, pd.Series):
                df[COL_SUM] = result
            else:
                df[COL_SUM] = pd.Series(result, index=df.index)
        # אם יש רק מחיר (בלי כמות נפרדת) - נשתמש בו כסכום
        elif COL_UNIT in df.columns:
            result = pd.to_numeric(df[COL_UNIT], errors="coerce").fillna(0)
            if isinstance(result, pd.Series):
                df[COL_SUM] = result
            else:
                df[COL_SUM] = pd.Series(result, index=df.index)

    # -------------------------------------------------------
    # 4) וידוא עמודות חובה
    # -------------------------------------------------------
    # אם אין עמודת 'שעה', ננסה ליצור אותה מעמודת 'תאריך' או נשים זמן ברירת מחדל
    if COL_TIME not in df.columns:
        print(f"⚠️ עמודת 'שעה' לא נמצאה, מנסה לחלץ מעמודת 'תאריך'...")
        # בודק אם עמודת התאריך מכילה גם שעה (למשל: "2024-01-01 12:30:00")
        if COL_DATE in df.columns:
            date_str = df[COL_DATE].astype(str).str.strip()
            # מנסה לזהות פורמט עם שעה (כולל תאריכים עם רווח ושעה)
            has_time = date_str.str.contains(r'\d{1,2}:\d{2}', na=False, regex=True)
            if has_time.any():
                # מחלץ את החלק של השעה
                time_part = date_str.str.extract(r'(\d{1,2}:\d{2}(?::\d{2})?)', expand=False)
                df[COL_TIME] = time_part.fillna("12:00")  # ברירת מחדל אם לא נמצא
            else:
                # אם אין שעה בתאריך, נשים שעה ברירת מחדל
                df[COL_TIME] = "12:00"
        else:
            # אם אין אפילו תאריך, נשים שעה ברירת מחדל
            df[COL_TIME] = "12:00"
        print(f"✅ עמודת 'שעה' נוצרה")
    
    needed = [COL_DATE, COL_SUM]  # COL_TIME כעת לא חובה כי אנחנו יוצרים אותה
    missing = [c for c in needed if c not in df.columns]
    if missing:
        # הודעת שגיאה מפורטת יותר
        available = ", ".join(df.columns.tolist()[:10])
        raise ValueError(f"עמודות חסרות בקובץ: {', '.join(missing)}. עמודות שנמצאו: {available}...")

    # -------------------------------------------------------
    # 5) נירמול עמודת 'שעה' (מתקן פסיקים/עמודות שהתפצלו)
    # -------------------------------------------------------
    COL_TIME_LOCAL = COL_TIME  # קיצור
    s_time = df[COL_TIME_LOCAL].astype(str).str.strip()

    # 5.1 '7,10' -> '07:10'
    mask_comma = s_time.str.match(r"^\s*\d{1,2},\d{1,2}\s*$", na=False)
    if mask_comma.any():
        df.loc[mask_comma, COL_TIME_LOCAL] = s_time.str.replace(",", ":", regex=False)

    # 5.2 אם הזמן התפצל לעמודה נוספת (למשל Unnamed: 1), ננסה לחבר
    time_siblings = [c for c in df.columns if c == f"{COL_TIME_LOCAL}.1" or c.startswith("Unnamed")]
    if time_siblings:
        for sib in time_siblings:
            cand = pd.to_numeric(df[sib], errors="coerce")
            # אם זה נראה כמו דקות (0-59 עבור רוב השורות), נאחד
            if cand.notna().any() and (cand.between(0, 59).mean() > 0.7):
                hh = df[COL_TIME_LOCAL].astype(str).str.extract(r"(\d{1,2})", expand=False).fillna("0").str.zfill(2)
                mm = cand.fillna(0).astype(int).astype(str).str.zfill(2)
                df[COL_TIME_LOCAL] = hh + ":" + mm
                df.drop(columns=[sib], inplace=True, errors="ignore")
                break

    # 5.3 המרה לפורמט זמן:
    #     קודם ננסה %H:%M; אם נכשל – ננסה parse כללי; ואם עדיין NaT, נטפל במספרים (7=>07:00).
    t1 = pd.to_datetime(df[COL_TIME_LOCAL].astype(str).str.strip(), errors="coerce", format="%H:%M")
    t2 = pd.to_datetime(df[COL_TIME_LOCAL].astype(str).str.strip(), errors="coerce")

    merged = t1.fillna(t2)

    nulls = merged.isna()
    if nulls.any():
        # אם יש שורות שעדיין NaT, ננסה לפרש כשעה מספרית בלבד (0..23)
        num_h = pd.to_numeric(df[COL_TIME_LOCAL].astype(str).str.strip(), errors="coerce")
        # נשאיר רק שעות בטווח
        num_h = num_h.where(num_h.between(0, 23))
        # נייצר datetime מלא (תאריך דמה), ואז נוציא time
        tfallback_dt = pd.to_datetime(num_h, errors="coerce", unit="h", origin="1970-01-01")
        merged = merged.where(~nulls, tfallback_dt)

    # כתוצאה מקבלת time (לא datetime מלא)
    df[COL_TIME_LOCAL] = merged.dt.time

    # -------------------------------------------------------
    # 6) המרות מספריות בסיסיות
    # -------------------------------------------------------
    if COL_QTY in df.columns:
        df[COL_QTY] = pd.to_numeric(df[COL_QTY], errors="coerce").fillna(0)

    # Проверка что COL_SUM существует и является Series
    if COL_SUM not in df.columns:
        available_cols = ', '.join(df.columns.tolist()[:10])
        raise ValueError(f"עמודת '{COL_SUM}' לא נמצאה. עמודות זמינות: {available_cols}...")
    
    # Убеждаемся что это Series, а не что-то другое
    col_sum_data = df[COL_SUM]
    
    # Если это DataFrame (несколько колонок с одинаковым именем), выбираем одну
    if isinstance(col_sum_data, pd.DataFrame):
        print(f"⚠️ Warning: COL_SUM is DataFrame (duplicate columns), selecting first column")
        # Выбираем первую колонку (обычно это правильная)
        col_sum_data = col_sum_data.iloc[:, 0]
        # Удаляем дубликаты колонок, оставляя только одну
        df = df.loc[:, ~df.columns.duplicated(keep='first')]
        df[COL_SUM] = col_sum_data
    # Если это не Series, преобразуем
    elif not isinstance(col_sum_data, pd.Series):
        print(f"⚠️ Warning: COL_SUM is not Series, type: {type(col_sum_data)}")
        # Пробуем преобразовать в Series
        try:
            if hasattr(col_sum_data, 'values'):
                # Если это массив, берем первый столбец если это 2D
                if hasattr(col_sum_data.values, 'ndim') and col_sum_data.values.ndim > 1:
                    col_sum_data = pd.Series(col_sum_data.values[:, 0], index=df.index, name=COL_SUM)
                else:
                    col_sum_data = pd.Series(col_sum_data.values, index=df.index, name=COL_SUM)
            elif hasattr(col_sum_data, '__iter__') and not isinstance(col_sum_data, str):
                col_sum_data = pd.Series(list(col_sum_data), index=df.index, name=COL_SUM)
            else:
                # Если это скаляр, создаем Series с одним значением для всех строк
                col_sum_data = pd.Series([col_sum_data] * len(df), index=df.index, name=COL_SUM)
            df[COL_SUM] = col_sum_data
        except Exception as e:
            raise ValueError(f"לא ניתן להמיר את '{COL_SUM}' ל-Series: {e}")
    
    # Теперь безопасно преобразуем в числовой формат
    try:
        # Заменяем запятые на точки для русских чисел (777,66 -> 777.66)
        col_sum_str = df[COL_SUM].astype(str).str.replace(',', '.', regex=False)
        # Удаляем пробелы и другие символы
        col_sum_str = col_sum_str.str.replace(' ', '', regex=False)
        col_sum_str = col_sum_str.str.replace('₽', '', regex=False)
        col_sum_str = col_sum_str.str.replace('₪', '', regex=False)
        col_sum_str = col_sum_str.str.replace('$', '', regex=False)
        # Преобразуем в число
        df[COL_SUM] = pd.to_numeric(col_sum_str, errors="coerce").fillna(0)
    except TypeError as e:
        # Если все еще ошибка, пробуем другой подход
        print(f"⚠️ TypeError при преобразовании COL_SUM: {e}")
        print(f"   Тип данных: {type(df[COL_SUM])}")
        print(f"   Первые значения: {df[COL_SUM].head()}")
        # Пробуем преобразовать через astype
        try:
            col_sum_str = df[COL_SUM].astype(str).str.replace(',', '.', regex=False)
            df[COL_SUM] = pd.to_numeric(col_sum_str, errors="coerce").fillna(0)
        except Exception as e2:
            raise ValueError(f"שגיאה בהמרת '{COL_SUM}' למספר: {e2}")

    # חישוב מחיר ליחידה אם חסר ויש כמות
    if COL_UNIT not in df.columns and COL_QTY in df.columns and (df[COL_QTY] > 0).any():
        df[COL_UNIT] = (df[COL_SUM] / df[COL_QTY].replace(0, pd.NA)).round(2)

    # -------------------------------------------------------
    # 7) המרות תאריך + "שעה עגולה"
    # -------------------------------------------------------
    # Парсинг дат с учетом формата день.месяц.год для русских дат
    date_str = df[COL_DATE].astype(str).str.strip()
    # Пробуем разные форматы
    df[COL_DATE] = pd.to_datetime(date_str, format='%d.%m.%Y', errors='coerce', dayfirst=True)
    # Если не получилось, пробуем без формата
    if df[COL_DATE].isna().any():
        df[COL_DATE] = pd.to_datetime(date_str, errors='coerce', dayfirst=True)
    df[COL_DATE] = df[COL_DATE].dt.date

    # קבוע לשם העמודה אצלך (אם כבר מוגדר, נשתמש בו; אחרת ניצור)
    hour_col_name = globals().get("HOUR_COL", "שעה עגולה")

    # ---- פונקציה משופרת לחישוב 'שעה עגולה' ----
    def _ensure_hour_col(_df, time_col, out_col):
        # Пробуем разные форматы времени
        time_str = _df[time_col].astype(str).str.strip()
        
        # Формат 1: HH:MM или HH:MM:SS
        h_from_dt = pd.to_datetime(time_str, format='%H:%M', errors='coerce')
        if h_from_dt.isna().any():
            h_from_dt = pd.to_datetime(time_str, format='%H:%M:%S', errors='coerce')
        if h_from_dt.isna().any():
            # Пробуем без формата
            h_from_dt = pd.to_datetime(time_str, errors='coerce')
        
        hours_from_dt = h_from_dt.dt.hour
        
        # fallback: אם השדה הוא מספרי (7, 12, ...)
        h_from_num = pd.to_numeric(time_str, errors="coerce")
        
        # Объединяем результаты
        hours = hours_from_dt.fillna(h_from_num)
        hours = pd.to_numeric(hours, errors="coerce").clip(0, 23).round().astype("Int64")
        _df[out_col] = hours
        return _df

    df = _ensure_hour_col(df, time_col=COL_TIME_LOCAL, out_col=hour_col_name)

    # -------------------------------------------------------
    # 8) יום בשבוע בעברית
    # -------------------------------------------------------
    dtd = pd.to_datetime(pd.Series(df[COL_DATE].astype(str)), errors="coerce")
    df["_weekday_eng"] = dtd.dt.day_name()
    heb = {
        "Sunday": "ראשון", "Monday": "שני", "Tuesday": "שלישי",
        "Wednesday": "רביעי", "Thursday": "חמישי",
        "Friday": "שישי", "Saturday": "שבת"
    }
    df["יום בשבוע"] = df["_weekday_eng"].map(heb)

    # Финальная проверка данных
    if df.empty:
        raise ValueError("הקובץ ריק לאחר עיבוד - אין נתונים תקינים")
    
    # Проверка что COL_SUM содержит валидные данные
    if COL_SUM in df.columns:
        valid_sum = df[COL_SUM].notna() & (df[COL_SUM] != 0)
        if valid_sum.sum() == 0:
            print(f"⚠️ Warning: COL_SUM содержит только нули или NaN. Первые значения: {df[COL_SUM].head()}")
        else:
            print(f"✅ COL_SUM валиден: {valid_sum.sum()} строк с данными, сумма: {df[COL_SUM].sum():.2f}")
    
    # Проверка дат
    if COL_DATE in df.columns:
        valid_dates = df[COL_DATE].notna()
        if valid_dates.sum() == 0:
            raise ValueError("אין תאריכים תקינים בקובץ")
        print(f"✅ Даты валидны: {valid_dates.sum()} строк")
    
    # Проверка времени
    if COL_TIME_LOCAL in df.columns:
        valid_times = df[COL_TIME_LOCAL].notna()
        if valid_times.sum() == 0:
            print(f"⚠️ Warning: Нет валидного времени")
        else:
            print(f"✅ Время валидно: {valid_times.sum()} строк")

    return df

# ---------- DB helper: ensure password_resets table ----------
def ensure_tables():
    db = get_db()
    db.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password_hash TEXT,
        first_name TEXT,
        last_name TEXT,
        plan TEXT DEFAULT 'free',
        subscription_status TEXT DEFAULT 'active',
        canceled_at TEXT
    );

    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- טבלה לשמירת דוחות מוצפנים
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,                          -- שם הדוח (לזיהוי)
        period_type TEXT DEFAULT 'month',            -- סוג תקופה: month/week/day/custom
        period_start DATE,                           -- תחילת תקופה
        period_end DATE,                             -- סוף תקופה
        encrypted_data BLOB NOT NULL,                -- נתונים מוצפנים (DataFrame)
        summary_json TEXT,                           -- סיכום מהיר (לא מוצפן)
        currency TEXT DEFAULT 'USD',                 -- валюта отчета
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- אינדקס לחיפוש מהיר
    CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);
    CREATE INDEX IF NOT EXISTS idx_reports_period ON reports(user_id, period_type, period_start, period_end);
    """)
    db.commit()


@app.teardown_appcontext
def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        plan TEXT NOT NULL DEFAULT 'free',
        ref_code TEXT UNIQUE,
        referred_count INTEGER NOT NULL DEFAULT 0,
        agreed_terms INTEGER NOT NULL DEFAULT 0,   -- חדש
        agreed_at TEXT,                             -- חדש
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db.commit()


def migrate_users_add_terms_columns():
    """
    מוסיף עמודות agreed_terms + agreed_at לטבלת users אם הן לא קיימות.
    SQLite לא באמת מכיר BOOLEAN/TIMESTAMP, אז נשתמש INTEGER/TEXT.
    """
    db = get_db()
    cols = [row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()]

    if "agreed_terms" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN agreed_terms INTEGER NOT NULL DEFAULT 0;")
    if "agreed_at" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN agreed_at TEXT;")
    db.commit()


def migrate_reports_add_period_type():
    """
    מוסיף עמודת period_type לטבלת reports אם היא לא קיימת.
    ערכים אפשריים: month/week/day/custom
    """
    db = get_db()
    
    # בדיקה אם הטבלה קיימת בכלל
    table_exists = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='reports'"
    ).fetchone()
    
    if not table_exists:
        return  # הטבלה תיווצר מאוחר יותר עם העמודה
    
    cols = [row["name"] for row in db.execute("PRAGMA table_info(reports)").fetchall()]
    
    if "period_type" not in cols:
        db.execute("ALTER TABLE reports ADD COLUMN period_type TEXT DEFAULT 'month';")
        print("✅ נוספה עמודת period_type לטבלת reports")
    db.commit()


# =============================================================================
# 📊 פונקציות לשמירה וטעינה של דוחות מוצפנים
# =============================================================================

def save_report(user_id: int, df: pd.DataFrame, name: str = None, period_type: str = "month", plots_info: list = None, roi_data: dict = None) -> int:
    """
    שומר דוח מוצפן לבסיס הנתונים.
    מחזיר את ה-ID של הדוח.
    
    period_type: month/week/day/custom
    plots_info: list of plot dicts with filename, title, etc.
    roi_data: ROI calculation results
    """
    db = get_db()
    
    # Get current currency from session
    from flask import session
    current_currency = session.get("currency", "USD")
    
    # Add currency column to reports table if it doesn't exist
    try:
        db.execute("ALTER TABLE reports ADD COLUMN currency TEXT DEFAULT 'USD'")
        db.commit()
    except:
        pass  # Column already exists
    
    # זיהוי תקופה אוטומטי
    period_start = None
    period_end = None
    if COL_DATE in df.columns:
        dates = pd.to_datetime(df[COL_DATE], errors='coerce').dropna()
        if len(dates) > 0:
            period_start = dates.min().strftime('%Y-%m-%d')
            period_end = dates.max().strftime('%Y-%m-%d')
    
    # Period type names - use English by default, will be translated in templates
    period_type_names = {
        "month": "Month",
        "week": "Week", 
        "day": "Day",
        "custom": "Period"
    }
    type_label = period_type_names.get(period_type, "Period")
    
    # Auto name if not provided
    if not name:
        if period_start:
            from datetime import datetime as dt_cls
            d = dt_cls.strptime(period_start, '%Y-%m-%d')
            if period_type == "month":
                name = f"{type_label} {d.strftime('%m/%Y')}"
            elif period_type == "week":
                name = f"{type_label} {d.strftime('%d/%m')}"
            else:
                name = f"{type_label} {d.strftime('%d/%m/%Y')}"
        else:
            name = f"Report {datetime.now().strftime('%Y-%m-%d')}"
    
    # הצפנה של הנתונים
    import io
    buffer = io.BytesIO()
    df.to_pickle(buffer)
    df_bytes = buffer.getvalue()
    encrypted = encrypt_data(df_bytes)
    
    # חישוב ממוצע יומי
    days_count = df[COL_DATE].nunique() if COL_DATE in df.columns else 1
    total_sales = float(pd.to_numeric(df[COL_SUM], errors='coerce').fillna(0).sum()) if COL_SUM in df.columns else 0
    
    # סיכום מהיר (לא מוצפן - לתצוגה בדשבורד)
    summary = {
        "total_sales": total_sales,
        "avg_daily": total_sales / max(days_count, 1),
        "rows": len(df),
        "days": days_count,
        "top_product": str(df[COL_ITEM].mode().iloc[0]) if COL_ITEM in df.columns and not df[COL_ITEM].mode().empty else None,
    }
    
    # Добавляем информацию о графиках (для восстановления на multi-worker)
    if plots_info:
        summary["plots"] = [
            {
                "filename": p.get("filename", ""),
                "title": p.get("title", ""),
                "note": p.get("note", ""),
                "ai": (p.get("ai") or "")[:400]  # Ограничиваем размер AI текста
            }
            for p in plots_info
        ]
    
    # Добавляем ROI данные
    if roi_data:
        summary["roi"] = roi_data
    
    cursor = db.execute("""
        INSERT INTO reports (user_id, name, period_type, period_start, period_end, encrypted_data, summary_json, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, period_type, period_start, period_end, encrypted, json.dumps(summary, ensure_ascii=False), current_currency))
    db.commit()
    
    return cursor.lastrowid


def load_report(report_id: int, user_id: int) -> pd.DataFrame:
    """
    טוען דוח מוצפן מבסיס הנתונים.
    מוודא שהדוח שייך למשתמש.
    """
    db = get_db()
    row = db.execute(
        "SELECT encrypted_data FROM reports WHERE id = ? AND user_id = ?",
        (report_id, user_id)
    ).fetchone()
    
    if not row:
        return None
    
    decrypted = decrypt_data(row['encrypted_data'])
    df = pd.read_pickle(io.BytesIO(decrypted))
    return df


def get_user_reports(user_id: int, limit: int = 50, period_type: str = None) -> list:
    """
    מחזיר רשימת דוחות של משתמש (לדשבורד).
    אפשר לסנן לפי סוג תקופה.
    """
    db = get_db()
    
    if period_type:
        rows = db.execute("""
            SELECT id, name, period_type, period_start, period_end, summary_json, created_at, currency
            FROM reports
            WHERE user_id = ? AND period_type = ?
            ORDER BY period_start DESC, created_at DESC
            LIMIT ?
        """, (user_id, period_type, limit)).fetchall()
    else:
        rows = db.execute("""
            SELECT id, name, period_type, period_start, period_end, summary_json, created_at, currency
            FROM reports
            WHERE user_id = ?
            ORDER BY period_start DESC, created_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
    
    return [dict(row) for row in rows]


def delete_report(report_id: int, user_id: int) -> bool:
    """מחיקת דוח (רק אם שייך למשתמש)"""
    db = get_db()
    cursor = db.execute(
        "DELETE FROM reports WHERE id = ? AND user_id = ?",
        (report_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


def compare_periods(df1: pd.DataFrame, df2: pd.DataFrame) -> dict:
    """
    משווה בין שתי תקופות ומחזיר תובנות מפורטות.
    Enhanced comparison with weekday analysis, hourly patterns, and top products.
    """
    current_lang = get_language()
    
    def calc_metrics(df):
        total = float(pd.to_numeric(df[COL_SUM], errors='coerce').fillna(0).sum()) if COL_SUM in df.columns else 0
        days = df[COL_DATE].nunique() if COL_DATE in df.columns else 0
        transactions = len(df)
        avg_ticket = total / transactions if transactions > 0 else 0
        return {
            "total": total,
            "days": days,
            "avg_daily": total / days if days > 0 else 0,
            "transactions": transactions,
            "avg_ticket": avg_ticket,
        }
    
    def calc_weekday_breakdown(df):
        """Разбивка по дням недели"""
        if COL_DATE not in df.columns or COL_SUM not in df.columns:
            return {}
        try:
            df_temp = df.copy()
            df_temp['_date'] = pd.to_datetime(df_temp[COL_DATE], errors='coerce')
            df_temp['_weekday'] = df_temp['_date'].dt.dayofweek
            df_temp['_sum'] = pd.to_numeric(df_temp[COL_SUM], errors='coerce').fillna(0)
            
            weekday_names = {
                'he': ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'],
                'en': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
                'ru': ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
            }
            names = weekday_names.get(current_lang, weekday_names['en'])
            
            breakdown = {}
            for wd in range(7):
                day_data = df_temp[df_temp['_weekday'] == wd]
                day_total = day_data['_sum'].sum()
                day_count = len(day_data)
                breakdown[names[wd]] = {
                    "total": float(day_total),
                    "count": day_count,
                    "avg": float(day_total / day_count) if day_count > 0 else 0
                }
            return breakdown
        except:
            return {}
    
    def calc_hourly_breakdown(df):
        """Разбивка по часам"""
        if COL_TIME not in df.columns or COL_SUM not in df.columns:
            return {}
        try:
            df_temp = df.copy()
            df_temp['_hour'] = pd.to_datetime(df_temp[COL_TIME], format='%H:%M:%S', errors='coerce').dt.hour
            df_temp['_sum'] = pd.to_numeric(df_temp[COL_SUM], errors='coerce').fillna(0)
            
            breakdown = {}
            for hour in range(24):
                hour_data = df_temp[df_temp['_hour'] == hour]
                hour_total = hour_data['_sum'].sum()
                hour_count = len(hour_data)
                if hour_count > 0:
                    breakdown[f"{hour:02d}:00"] = {
                        "total": float(hour_total),
                        "count": hour_count,
                        "avg": float(hour_total / hour_count)
                    }
            return breakdown
        except:
            return {}
    
    def get_top_products(df, top_n=5):
        """Топ продуктов по выручке"""
        if COL_ITEM not in df.columns or COL_SUM not in df.columns:
            return []
        try:
            df_temp = df.copy()
            df_temp['_sum'] = pd.to_numeric(df_temp[COL_SUM], errors='coerce').fillna(0)
            top = df_temp.groupby(COL_ITEM)['_sum'].sum().nlargest(top_n)
            return [{"name": name, "total": float(val)} for name, val in top.items()]
        except:
            return []
    
    m1 = calc_metrics(df1)
    m2 = calc_metrics(df2)
    
    # Расчёт изменений в процентах
    def pct_change(old, new):
        if old == 0:
            return 100 if new > 0 else 0
        return round((new - old) / old * 100, 1)
    
    # Расчёт разбивки по дням недели
    weekday1 = calc_weekday_breakdown(df1)
    weekday2 = calc_weekday_breakdown(df2)
    
    # Сравнение по дням недели
    weekday_comparison = {}
    for day in weekday2.keys():
        old_val = weekday1.get(day, {}).get("total", 0)
        new_val = weekday2.get(day, {}).get("total", 0)
        weekday_comparison[day] = {
            "period1": old_val,
            "period2": new_val,
            "change_pct": pct_change(old_val, new_val),
            "change_abs": new_val - old_val
        }
    
    # Расчёт по часам
    hourly1 = calc_hourly_breakdown(df1)
    hourly2 = calc_hourly_breakdown(df2)
    
    # Топ продукты
    top_products1 = get_top_products(df1)
    top_products2 = get_top_products(df2)
    
    # Определение лучшего и худшего дня
    best_day = max(weekday_comparison.items(), key=lambda x: x[1]["change_pct"]) if weekday_comparison else None
    worst_day = min(weekday_comparison.items(), key=lambda x: x[1]["change_pct"]) if weekday_comparison else None
    
    # Определение пиковых часов
    peak_hours1 = sorted(hourly1.items(), key=lambda x: x[1]["total"], reverse=True)[:3] if hourly1 else []
    peak_hours2 = sorted(hourly2.items(), key=lambda x: x[1]["total"], reverse=True)[:3] if hourly2 else []
    
    return {
        "period1": m1,
        "period2": m2,
        "changes": {
            "total_pct": pct_change(m1["total"], m2["total"]),
            "avg_daily_pct": pct_change(m1["avg_daily"], m2["avg_daily"]),
            "transactions_pct": pct_change(m1["transactions"], m2["transactions"]),
            "avg_ticket_pct": pct_change(m1["avg_ticket"], m2["avg_ticket"]),
        },
        "weekday_comparison": weekday_comparison,
        "best_day": {"name": best_day[0], "data": best_day[1]} if best_day else None,
        "worst_day": {"name": worst_day[0], "data": worst_day[1]} if worst_day else None,
        "peak_hours": {
            "period1": [{"hour": h[0], "total": h[1]["total"]} for h in peak_hours1],
            "period2": [{"hour": h[0], "total": h[1]["total"]} for h in peak_hours2],
        },
        "top_products": {
            "period1": top_products1,
            "period2": top_products2,
        },
        "insight": _generate_comparison_insight(m1, m2, best_day, worst_day, current_lang)
    }


def _generate_comparison_insight(m1: dict, m2: dict, best_day=None, worst_day=None, lang='en') -> str:
    """יצירת תובנה טקסטואלית להשוואה עם פרטים על ימים"""
    pct = ((m2["total"] - m1["total"]) / m1["total"] * 100) if m1["total"] > 0 else 0
    
    insights = {
        'he': {
            'up_big': f"📈 עלייה משמעותית של {pct:.0f}% במכירות! המשך כך.",
            'up_small': f"📊 עלייה קלה של {pct:.0f}% במכירות. יש מקום לשיפור.",
            'down_small': f"📉 ירידה קלה של {abs(pct):.0f}% במכירות. כדאי לבדוק מה השתנה.",
            'down_big': f"⚠️ ירידה משמעותית של {abs(pct):.0f}% במכירות! דורש תשומת לב.",
        },
        'en': {
            'up_big': f"📈 Significant increase of {pct:.0f}% in sales! Keep it up.",
            'up_small': f"📊 Slight increase of {pct:.0f}% in sales. Room for improvement.",
            'down_small': f"📉 Slight decrease of {abs(pct):.0f}% in sales. Worth checking what changed.",
            'down_big': f"⚠️ Significant decrease of {abs(pct):.0f}% in sales! Needs attention.",
        },
        'ru': {
            'up_big': f"📈 Значительный рост на {pct:.0f}%! Так держать.",
            'up_small': f"📊 Небольшой рост на {pct:.0f}%. Есть потенциал для улучшения.",
            'down_small': f"📉 Небольшое снижение на {abs(pct):.0f}%. Стоит проверить, что изменилось.",
            'down_big': f"⚠️ Значительное снижение на {abs(pct):.0f}%! Требует внимания.",
        }
    }
    
    msgs = insights.get(lang, insights['en'])
    
    if pct > 10:
        base = msgs['up_big']
    elif pct > 0:
        base = msgs['up_small']
    elif pct > -10:
        base = msgs['down_small']
    else:
        base = msgs['down_big']
    
    # Добавляем информацию о лучшем/худшем дне
    if best_day and worst_day:
        day_info = {
            'he': f" היום הטוב ביותר: {best_day[0]} (+{best_day[1]['change_pct']:.0f}%)",
            'en': f" Best day: {best_day[0]} (+{best_day[1]['change_pct']:.0f}%)",
            'ru': f" Лучший день: {best_day[0]} (+{best_day[1]['change_pct']:.0f}%)"
        }
        base += day_info.get(lang, day_info['en'])
    
    return base

    try:
        db.execute("ALTER TABLE users ADD COLUMN credit_balance INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE users ADD COLUMN ref_bonus_granted INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass

    db.commit()


def ensure_user_columns():
    """מוסיף עמודות first_name/last_name אם הן לא קיימות בטבלת users."""
    db = get_db()
    cols = {row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()}
    changed = False
    if "first_name" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
        changed = True
    if "last_name" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
        changed = True
    if changed:
        db.commit()


def _rand_ref():
    alphabet = string.ascii_uppercase + string.digits
    return "REF" + "".join(secrets.choice(alphabet) for _ in range(6))


with app.app_context():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    ensure_user_columns()  # <<< הוספנו שורה זו

with app.app_context():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    migrate_users_add_terms_columns()  # ← הוספה חשובה
    migrate_reports_add_period_type()  # ← עמודת סוג תקופה

    

def ensure_user_ref_code(user_id):
    db = get_db()
    row = db.execute("SELECT ref_code FROM users WHERE id=?", (user_id,)).fetchone()
    if not row or not row["ref_code"]:
        code = _rand_ref()
        # לוודא ייחודיות
        while db.execute("SELECT 1 FROM users WHERE ref_code=?", (code,)).fetchone():
            code = _rand_ref()
        db.execute("UPDATE users SET ref_code=? WHERE id=?", (code, user_id))
        db.commit()


def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
# שיהיה ניתן להשתמש ב-current_user() בתוך תבניות Jinja
@app.context_processor
def inject_current_user():
    return {
        "current_user": current_user,
        "is_trial_active": is_trial_active,
        "get_effective_plan": get_effective_plan,
        "get_trial_days_left": get_trial_days_left,
        "get_trial_end_timestamp": get_trial_end_timestamp
    }


def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrap(*args, **kwargs):
        if not current_user():
            flash_t("msg_login_required", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrap


# -----------------------------------------------------------------------------------

from datetime import datetime
from flask import redirect, url_for, flash

@app.post("/cancel-subscription")
@login_required
def cancel_subscription():
    """Cancel subscription in PayPal and update database"""
    user = current_user()
    if not user:
        flash_t("msg_login_required", "warning")
        return redirect(url_for("login"))
    
    # Get PayPal subscription ID
    db = get_db()
    cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
    paypal_subscription_id = None
    
    if "paypal_subscription_id" in cols:
        try:
            if hasattr(user, 'keys') and "paypal_subscription_id" in user.keys():
                paypal_subscription_id = user["paypal_subscription_id"]
            elif "paypal_subscription_id" in dict(user).keys():
                paypal_subscription_id = dict(user)["paypal_subscription_id"]
        except (KeyError, TypeError, AttributeError):
            pass
    
    # Cancel subscription in PayPal if exists
    if paypal_subscription_id:
        access_token = get_paypal_access_token()
        if access_token:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Cancel subscription in PayPal
            cancel_data = {
                "reason": "User requested cancellation"
            }
            
            response = requests.post(
                f"{PAYPAL_API_URL}/v1/billing/subscriptions/{paypal_subscription_id}/cancel",
                headers=headers,
                json=cancel_data
            )
            
            if response.status_code in [200, 204]:
                print(f"[PayPal] Subscription {paypal_subscription_id} cancelled successfully")
            else:
                print(f"[PayPal] Failed to cancel subscription: {response.text}")
                # Continue anyway - update DB even if PayPal cancel fails
    
    # Update database
    now_iso = datetime.utcnow().isoformat(timespec="seconds")

    if "canceled_at" in cols and "subscription_status" in cols:
        db.execute("""
            UPDATE users
            SET plan = ?, subscription_status = ?, canceled_at = ?
            WHERE id = ?
        """, ("free", "canceled", now_iso, user["id"]))
    elif "canceled_at" in cols:
        db.execute("""
            UPDATE users
            SET plan = ?, canceled_at = ?
            WHERE id = ?
        """, ("free", now_iso, user["id"]))
    else:
        db.execute("""
            UPDATE users
            SET plan = ?
            WHERE id = ?
        """, ("free", user["id"]))
    db.commit()

    flash_t("msg_subscription_cancelled", "success")
    return redirect(url_for("profile"))


@app.route("/set-language/<lang>")
def set_language(lang):
    """Переключение языка"""
    from flask import session, redirect, url_for, request
    if lang in ["he", "en", "ru"]:
        session["language"] = lang
        session.permanent = True
        session.modified = True
        
        # При смене языка очищаем последний экспорт,
        # чтобы не было сводок/AI на старом языке
        global LAST_EXPORT
        LAST_EXPORT = {
            "generated_at": None,
            "lang": lang,
            "plots": [],
            "summary": "",
        }
        session["last_export"] = {}
        
        # Устанавливаем валюту по умолчанию для языка, если пользователь еще не выбрал
        if "currency" not in session:
            default_currencies = {"he": "ILS", "ru": "RUB", "en": "USD"}
            session["currency"] = default_currencies.get(lang, "USD")
        
        return_url = request.args.get("return_url") or request.referrer or url_for("about")
        return redirect(return_url)
    return redirect(url_for("about"))

@app.route("/set-currency/<currency_code>")
def set_currency(currency_code):
    """Установка валюты пользователем"""
    from flask import session, redirect, url_for, request
    if currency_code in AVAILABLE_CURRENCIES:
        session["currency"] = currency_code
        session.permanent = True
        session.modified = True
    return_url = request.args.get("return_url") or request.referrer or url_for("about")
    return redirect(return_url)

@app.route("/")
def index():
    """Home page - redirect based on login status"""
    u = current_user()
    if u:
        # Logged in users go to upload page
        return redirect(url_for('upload'))
    else:
        # Guests go to about page with explanations and Get Started button
        return redirect(url_for('about'))



@app.route("/about")
def about():
    """About page - different content based on login status"""
    u = current_user()
    if u:
        # Logged in users: show dashboard/upload focused content
        return render_template("about.html", active="about", title="About OnePoweb", is_logged_in=True)
    else:
        # Guests: show Get Started focused content
        return render_template("about.html", active="about", title="About OnePoweb", is_logged_in=False)

@app.route("/get-started")
def get_started():
    """Onboarding questions for new users"""
    return render_template("get_started.html", active="get_started", title=t("get_started_title"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Upload and analyze report - works for both logged in users and guests (one-time)"""
    u = current_user()
    is_guest = not u
    
    # Check if guest already used their one-time upload
    if is_guest and session.get("guest_upload_used"):
        current_lang = get_language()
        if current_lang == 'he':
            flash("כבר השתמשת בניתוח החינמי. הירשם לחשבון מלא להמשך!", "warning")
        elif current_lang == 'ru':
            flash("Вы уже использовали бесплатный анализ. Зарегистрируйтесь для продолжения!", "warning")
        else:
            flash("You've already used the free analysis. Sign up to continue!", "warning")
        return redirect(url_for("signup"))
    
    messages, plots = [], []
    current_lang = get_language()  # Получаем текущий язык
    print(f"🌐 index(): current_lang = {current_lang}")

    def _render():
        return render_template("index.html",
                               messages=messages, plots=plots,
                               active="home", title="ניתוח דוח",
                               is_guest=is_guest)

    # GET – מסך העלאה
    if request.method == "GET":
        print("➡ GET /")
        return _render()

    print("➡ POST / (העלאת דוח)")
    # ===== קובץ =====
    _clean_plots_dir()
    file = request.files.get("file")
    if not file or file.filename.strip() == "":
        messages.append("לא הועלה קובץ.")
        return _render()

    from werkzeug.utils import secure_filename
    # תמיכה בכל הפורמטים הנפוצים של קופות בישראל
    ALLOWED_EXTS = {
        ".csv", ".tsv", ".txt",           # טקסט מופרד
        ".xlsx", ".xls", ".xlsm", ".xlsb",  # Excel כל הגרסאות
        ".ods",                            # OpenDocument (LibreOffice)
        ".json",                           # JSON מודרני
        ".xml",                            # XML (SAP, ERP)
    }
    name = secure_filename(file.filename or "")
    ext  = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTS:
        messages.append("סוג קובץ לא נתמך. פורמטים נתמכים: CSV, Excel, JSON, XML, ODS, TXT.")
        return _render()

    safe_name = secrets.token_hex(8) + ext
    up_path = os.path.join(UPLOAD_DIR, safe_name)
    try:
        file.save(up_path)
        print(f"✅ קובץ נשמר: {up_path}")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ שגיאה בשמירת הקובץ: {e}")
        print(f"📋 Traceback:\n{error_trace}")
        # Сообщение об ошибке на соответствующем языке
        if current_lang == "he":
            messages.append(f"שגיאה בשמירת הקובץ: {str(e)}")
        elif current_lang == "en":
            messages.append(f"Error saving file: {str(e)}")
        else:  # ru
            messages.append(f"Ошибка сохранения файла: {str(e)}")
        return _render()

    # ===== פרמטרים מהטופס =====
    opt_hourly       = bool(request.form.get("opt_hourly"))
    opt_weekday      = bool(request.form.get("opt_weekday"))
    opt_daily        = bool(request.form.get("opt_daily"))
    opt_top_products = bool(request.form.get("opt_top_products"))
    opt_payments     = bool(request.form.get("opt_payments"))
    # --- גרפים מתקדמים חדשים ---
    opt_avg_ticket     = bool(request.form.get("opt_avg_ticket"))
    opt_heatmap        = bool(request.form.get("opt_heatmap"))
    opt_weekend_compare = bool(request.form.get("opt_weekend_compare"))
    
    # --- פרמטרי תקופה ---
    period_type = request.form.get("period_type", "month")  # month/week/day/custom
    period_name = request.form.get("period_name", "").strip()  # שם מותאם אישית
    
    try:
        hour_start = int(request.form.get("hour_start", 8))
        hour_end   = int(request.form.get("hour_end", 20))
    except Exception:
        hour_start, hour_end = 8, 20
    if hour_start > hour_end:
        hour_start, hour_end = hour_end, hour_start

    # ===== קריאת הדו"ח =====
    try:
        df = _read_report(up_path)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ שגיאה בקריאת הקובץ: {e}")
        print(f"📋 Traceback:\n{error_trace}")
        # Сообщение об ошибке на соответствующем языке
        if current_lang == "he":
            messages.append(f"שגיאה בקריאת הקובץ: {str(e)}")
        elif current_lang == "en":
            messages.append(f"Error reading file: {str(e)}")
        else:  # ru
            messages.append(f"Ошибка чтения файла: {str(e)}")
        return _render()

    # ------------------------------------------------------------------
    # 1️⃣ מכירות לפי שעה — הכי חשוב: מתי צריך עובדים
    # ------------------------------------------------------------------
    if opt_hourly:
        print(f"📊 Creating hourly chart, current_lang = {current_lang}")
        try:
            if HOUR_COL not in df.columns and COL_TIME in df.columns:
                tmp_time = pd.to_datetime(df[COL_TIME].astype(str), errors="coerce")
                df[HOUR_COL] = tmp_time.dt.hour

            clip = df.loc[(df[HOUR_COL] >= hour_start) & (df[HOUR_COL] <= hour_end)].copy()
            clip[HOUR_COL] = pd.to_numeric(clip[HOUR_COL], errors="coerce")

            hours_idx = pd.Index(range(hour_start, hour_end + 1), name=HOUR_COL)
            hourly = (clip.groupby(HOUR_COL, dropna=False)[COL_SUM]
                            .sum(min_count=1)
                            .reindex(hours_idx, fill_value=0)
                            .reset_index()
                            .sort_values(HOUR_COL))

            fig, ax = plt.subplots(figsize=(9, 4))
            ax.bar(hourly[HOUR_COL], hourly[COL_SUM], align="center")
            # Переводим заголовки и подписи осей
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            print(f"📊 Hourly chart: current_lang={current_lang}, currency_symbol={currency_symbol}")
            if current_lang == "he":
                ax.set_title(rtl(f"מכירות לפי שעה ({currency_symbol}) {hour_start}:00–{hour_end}:00"))
                ax.set_xlabel(rtl("שעה"))
                ax.set_ylabel(rtl(f'סה"כ ({currency_symbol})'))
            elif current_lang == "en":
                ax.set_title(f"Sales by Hour ({currency_symbol}) {hour_start}:00–{hour_end}:00")
                ax.set_xlabel("Hour")
                ax.set_ylabel(f"Total ({currency_symbol})")
            else:  # ru
                ax.set_title(f"Продажи по часам ({currency_symbol}) {hour_start}:00–{hour_end}:00")
                ax.set_xlabel(t("chart_axis_hour"))
                ax.set_ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            ax.set_xticks(list(range(hour_start, hour_end + 1)))
            ax.set_xlim(hour_start - 0.5, hour_end + 0.5)
            fname = _save_fig(fig, "hourly.png")

            # --- AI ---
            best_hour_row = hourly.loc[hourly[COL_SUM].idxmax()] if not hourly.empty else None
            weak_hour_row = hourly.loc[hourly[COL_SUM].idxmin()] if not hourly.empty else None
            brief = {
                "range": [hour_start, hour_end],
                "best_hour": (int(best_hour_row[HOUR_COL]) if best_hour_row is not None else None),
                "best_hour_sum": float(hourly[COL_SUM].max()) if not hourly.empty else 0.0,
                "weak_hour": (int(weak_hour_row[HOUR_COL]) if weak_hour_row is not None else None),
                "weak_hour_sum": float(hourly[COL_SUM].min()) if not hourly.empty else 0.0,
                "avg_hour": float(hourly[COL_SUM].mean()) if not hourly.empty else 0.0,
            }
            chart_title_he = "מכירות לפי שעה"
            chart_title = t("chart_sales_by_hour")
            ai = ai_explain(chart_title_he, brief, current_lang)

            plots.append({
                "filename": fname,
                "title": chart_title,
                "note": t("chart_note_sales_by_hour"),
                "ai": ai,               # ← הוספת השדה
            })
        except Exception as e:
            print(f"⚠️ Skipping hourly chart: {e}")
            # Пропускаем график, если нет нужных колонок

    # ------------------------------------------------------------------
    # 2️⃣ מכירות לפי יום בשבוע — איזה ימים חזקים/חלשים
    # ------------------------------------------------------------------
    if opt_weekday:
        try:
            tmp = df.copy()
            if "יום בשבוע" not in tmp.columns:
                if COL_DATE in tmp.columns:
                    dow = pd.to_datetime(tmp[COL_DATE], errors="coerce").dt.dayofweek
                    map_he = {0: "ראשון", 1: "שני", 2: "שלישי", 3: "רביעי", 4: "חמישי", 5: "שישי", 6: "שבת"}
                    tmp["יום בשבוע"] = dow.map(map_he)
                else:
                    messages.append("אין עמודת 'יום בשבוע' או 'תאריך' — דילגנו על הגרף הזה.")
                    raise RuntimeError("missing weekday/date")

            days_order = ["ראשון","שני","שלישי","רביעי","חמישי","שישי","שבת"]
            cat_type = pd.api.types.CategoricalDtype(categories=days_order, ordered=True)
            tmp["יום בשבוע"] = tmp["יום בשבוע"].astype(cat_type)

            tmp[COL_SUM] = pd.to_numeric(tmp[COL_SUM], errors="coerce").fillna(0)
            by_wd = tmp.groupby("יום בשבוע", observed=True)[COL_SUM].sum().reset_index()

            if by_wd.empty:
                messages.append("אין נתונים לגרף 'מכירות לפי יום בשבוע'.")
            else:
                # Порядок дней на иврите (как в данных)
                order_he = ["ראשון","שני","שלישי","רביעי","חמישי","שישי","שבת"]
                # Маппинг дней недели на разные языки
                day_mapping = {
                    "he": {"ראשון": "ראשון", "שני": "שני", "שלישי": "שלישי", "רביעי": "רביעי", "חמישי": "חמישי", "שישי": "שישי", "שבת": "שבת"},
                    "en": {"ראשון": "Sunday", "שני": "Monday", "שלישי": "Tuesday", "רביעי": "Wednesday", "חמישי": "Thursday", "שישי": "Friday", "שבת": "Saturday"},
                    "ru": {"ראשון": "Воскресенье", "שני": "Понедельник", "שלישי": "Вторник", "רביעי": "Среда", "חמישי": "Четверг", "שישי": "Пятница", "שבת": "Суббота"}
                }
                
                # Переводим дни недели в зависимости от языка и применяем RTL для иврита
                if current_lang in day_mapping:
                    names = [day_mapping[current_lang].get(x, x) for x in by_wd["יום בשבוע"].tolist()]
                    # Применяем RTL для ивритских меток
                    if current_lang == "he":
                        names = [rtl(name) for name in names]
                else:
                    names = [rtl(str(x)) for x in by_wd["יום בשבוע"].tolist()]
                
                xpos  = list(range(len(names)))
                values = by_wd[COL_SUM].tolist()

                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(xpos, values)
                
                # Переводим заголовки и подписи осей
                currency_info = get_currency(current_lang)
                currency_symbol = currency_info["symbol"]
                
                print(f"📊 Weekday chart (first path): current_lang={current_lang}, currency_symbol={currency_symbol}, names={names[:3] if names else []}")
                if current_lang == "he":
                    ax.set_title(rtl(f"מכירות לפי יום בשבוע ({currency_symbol})"))
                    ax.set_xlabel(rtl("יום בשבוע"))
                    ax.set_ylabel(rtl(f'סה"כ ({currency_symbol})'))
                elif current_lang == "en":
                    ax.set_title(f"Sales by Day of Week ({currency_symbol})")
                    ax.set_xlabel("Day of Week")
                    ax.set_ylabel(f"Total ({currency_symbol})")
                else:  # ru
                    ax.set_title(f"{t('chart_sales_by_weekday')} ({currency_symbol})")
                    ax.set_xlabel(t("chart_axis_day"))
                    ax.set_ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
                ax.set_xticks(xpos)
                ax.set_xticklabels(names, rotation=0)
                fname = _save_fig(fig, "by_weekday.png")

                # --- AI ---
                top_row = by_wd.sort_values(COL_SUM, ascending=False).iloc[0] if not by_wd.empty else None
                weak_row = by_wd.sort_values(COL_SUM, ascending=True).iloc[0] if not by_wd.empty else None
                
                # Переводим дни недели для brief
                best_day_he = str(top_row["יום בשבוע"]) if top_row is not None else None
                weak_day_he = str(weak_row["יום בשבוע"]) if weak_row is not None else None
                best_day_translated = day_mapping.get(current_lang, day_mapping["he"]).get(best_day_he, best_day_he) if best_day_he else None
                weak_day_translated = day_mapping.get(current_lang, day_mapping["he"]).get(weak_day_he, weak_day_he) if weak_day_he else None
                
                # Переводим распределение по дням
                dist_translated = {}
                for k, v in zip(by_wd["יום בשבוע"], by_wd[COL_SUM]):
                    k_translated = day_mapping.get(current_lang, day_mapping["he"]).get(str(k), str(k))
                    dist_translated[k_translated] = float(v)
                
                brief = {
                    "best_day": best_day_translated,
                    "best_day_sum": float(top_row[COL_SUM]) if top_row is not None else 0.0,
                    "weak_day": weak_day_translated,
                    "weak_day_sum": float(weak_row[COL_SUM]) if weak_row is not None else 0.0,
                    "avg_day": float(by_wd[COL_SUM].mean()) if not by_wd.empty else 0.0,
                    "dist": dist_translated
                }
                chart_title_he = "מכירות לפי יום בשבוע"
                chart_title = t("chart_sales_by_weekday")
                ai = ai_explain(chart_title_he, brief, current_lang)

                plots.append({"filename": fname, "title": t("chart_sales_by_weekday"),
                              "note": t("chart_note_sales_by_weekday"),
                              "ai": ai})
        except Exception as e:
            print(f"⚠️ Skipping weekday chart: {e}")
            # Пропускаем график, если нет нужных колонок

    # ------------------------------------------------------------------
    # 4️⃣ מכירות יומיות — מגמות ואנומליות
    # ------------------------------------------------------------------
    if opt_daily:
        try:
            daily = df.groupby(COL_DATE)[COL_SUM].sum().reset_index()
            fig = plt.figure(figsize=(10, 4))
            plt.bar(daily[COL_DATE].astype(str), daily[COL_SUM])
            # Переводим заголовок
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                plt.title(rtl(f"מכירות יומיות ({currency_symbol})"))
            elif current_lang == "en":
                plt.title(f"Daily Sales ({currency_symbol})")
            else:  # ru
                plt.title(f"{t('chart_daily_sales')} ({currency_symbol})")
            # Переводим подписи осей
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                plt.xlabel(rtl("תאריך"))
                plt.ylabel(rtl(f"סה\"כ ({currency_symbol})"))
            elif current_lang == "en":
                plt.xlabel("Date")
                plt.ylabel(f"Total ({currency_symbol})")
            else:  # ru
                plt.xlabel("Дата")
                plt.ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            plt.xticks(rotation=60)
            fname = _save_fig(fig, "daily.png")

            # --- AI ---
            top = daily.sort_values(COL_SUM, ascending=False).iloc[0] if not daily.empty else None
            brief = {
                "best_date": (str(top[COL_DATE]) if top is not None else None),
                "best_sum": float(top[COL_SUM]) if top is not None else 0.0,
                "avg_daily": float(daily[COL_SUM].mean()) if not daily.empty else 0.0,
            }
            chart_title_he = "מכירות יומיות"
            chart_title = t("chart_daily_sales")
            ai = ai_explain(chart_title_he, brief, current_lang)

            plots.append({"filename": fname, "title": chart_title,
                          "note": t("chart_note_daily_sales"),
                          "ai": ai})
        except Exception as e:
            print(f"⚠️ Skipping daily sales chart: {e}")
            # Пропускаем график, если нет нужных колонок

    # ------------------------------------------------------------------
    # 5️⃣ Top 10 מוצרים – כמות/הכנסות
    # ------------------------------------------------------------------
    if opt_top_products:
        try:
            if COL_ITEM not in df.columns:
                messages.append("דילגנו על גרפי מוצרים: לא נמצאה עמודה 'מוצר'.")
            else:
                # כמות
                if COL_QTY in df.columns:
                    qty = (df.groupby(COL_ITEM, as_index=False)[COL_QTY]
                             .sum()
                             .sort_values(COL_QTY, ascending=False)
                             .head(10))
                    if not qty.empty:
                        names = [ _rtl(str(x)) for x in qty[COL_ITEM].tolist() ]
                        xpos  = list(range(len(names)))

                        fig, ax = plt.subplots(figsize=(9, 4))
                        ax.bar(xpos, qty[COL_QTY])
                        # Переводим заголовки и подписи осей
                        if current_lang == "he":
                            ax.set_title(_rtl("Top 10 — כמות לפי מוצר"))
                            ax.set_ylabel(_rtl("כמות"))
                        elif current_lang == "en":
                            ax.set_title("Top 10 — Quantity by Product")
                            ax.set_ylabel("Quantity")
                        else:  # ru
                            ax.set_title("Top 10 — " + t("chart_top_quantity"))
                            ax.set_ylabel(t("chart_axis_quantity"))
                        ax.set_xticks(xpos)
                        ax.set_xticklabels(names, rotation=40, ha="right")
                        fname = _save_fig(fig, "top_qty.png")

                        # --- AI ---
                        brief = {
                            "top_item": str(qty.iloc[0][COL_ITEM]),
                            "top_value": int(qty.iloc[0][COL_QTY]),
                        }
                        chart_title_he = "מוצרים – כמות"
                        chart_title = t("chart_top_quantity")
                        ai = ai_explain(chart_title_he, brief, current_lang)

                        plots.append({"filename": fname, "title": t("chart_top_quantity"),
                                      "note": t("chart_note_top_quantity"),
                                      "ai": ai})
                else:
                    messages.append("דילגנו על 'Top 10 לפי כמות' — אין עמודת 'כמות'.")

                # הכנסות
                rev_df = df.copy()
                rev_df[COL_SUM] = pd.to_numeric(rev_df[COL_SUM], errors="coerce").fillna(0)
                revenue = (rev_df.groupby(COL_ITEM, as_index=False)[COL_SUM]
                                 .sum()
                                 .sort_values(COL_SUM, ascending=False)
                                 .head(10))
                if not revenue.empty:
                    names_r = [ _rtl(str(x)) for x in revenue[COL_ITEM].tolist() ]
                    xpos_r  = list(range(len(names_r)))

                    fig, ax = plt.subplots(figsize=(9, 4))
                    ax.bar(xpos_r, revenue[COL_SUM])
                    # Переводим заголовки и подписи осей
                    if current_lang == "he":
                        ax.set_title(_rtl("Top 10 — הכנסות לפי מוצר"))
                        ax.set_ylabel(_rtl(f'סה"כ ({get_currency("he")["symbol"]})'))
                    elif current_lang == "en":
                        currency_sym = get_currency("en")["symbol"]
                        ax.set_title("Top 10 — Revenue by Product")
                        ax.set_ylabel(f"Total ({currency_sym})")
                    else:  # ru
                        ax.set_title("Top 10 — " + t("chart_top_revenue"))
                        ax.set_ylabel(t("chart_axis_total"))
                    ax.set_xticks(xpos_r)
                    ax.set_xticklabels(names_r, rotation=40, ha="right")
                    fname = _save_fig(fig, "top_rev.png")

                    # --- AI ---
                    # מציאת מוצרים פחות נמכרים (למטרת קומבו)
                    all_items = rev_df.groupby(COL_ITEM)[COL_SUM].sum().sort_values(ascending=True)
                    bottom_items = all_items.head(5).to_dict() if len(all_items) > 5 else all_items.to_dict()
                    
                    brief = {
                        "top_item": str(revenue.iloc[0][COL_ITEM]),
                        "top_value": float(revenue.iloc[0][COL_SUM]),
                        "bottom_items": {str(k): float(v) for k, v in bottom_items.items()},
                        "all_items": {str(k): float(v) for k, v in all_items.items()}
                    }
                    chart_title_he = "מוצרים – הכנסות"
                    chart_title = t("chart_top_revenue")
                    ai = ai_explain(chart_title_he, brief, current_lang)

                    plots.append({"filename": fname, "title": t("chart_top_revenue"),
                                  "note": t("chart_note_top_revenue"),
                                  "ai": ai})
        except Exception as e:
            print(f"⚠️ Skipping products chart: {e}")
            # Пропускаем график, если нет нужных колонок

    # ------------------------------------------------------------------
    # 8️⃣ פילוח אמצעי תשלום — מזומן מול אשראי
    # ------------------------------------------------------------------
    if opt_payments:
        # זיהוי עמודת אמצעי התשלום לפי שמות אפשריים
        possible_pay_cols = ["אמצעי תשלום", "תשלום", "אמצעי_תשלום", "payment", "payment_method"]
        pay_col = next((c for c in df.columns if str(c).strip() in possible_pay_cols), None)

        if pay_col:
            try:
                pay = df.copy()
                pay[COL_SUM] = pd.to_numeric(pay[COL_SUM], errors="coerce").fillna(0)

                pay = pay.groupby(pay_col, as_index=False)[COL_SUM].sum()

                if not pay.empty:
                    labels = [ str(x) for x in pay[pay_col].tolist() ]
                    values = pay[COL_SUM].tolist()

                    # Красивая цветовая палитра
                    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
                    colors = colors[:len(values)]  # Обрезаем до нужного количества
                    
                    # Создаем фигуру с местом для легенды справа
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Круговая диаграмма БЕЗ меток - только проценты
                    wedges, texts, autotexts = ax.pie(
                        values, 
                        autopct="%1.0f%%", 
                        startangle=90,
                        colors=colors,
                        pctdistance=0.75,  # Расстояние процентов от центра
                        textprops={'fontsize': 11, 'fontweight': 'bold', 'color': 'white'}
                    )
                    
                    # Делаем проценты более читаемыми
                    for autotext in autotexts:
                        autotext.set_fontweight('bold')
                    
                    # Легенда справа с цветными метками
                    ax.legend(
                        wedges, 
                        labels,
                        title="",
                        loc="center left",
                        bbox_to_anchor=(1, 0, 0.5, 1),
                        fontsize=11
                    )
                    
                    # Переводим заголовок
                    currency_info = get_currency(current_lang)
                    currency_symbol = currency_info["symbol"]
                    
                    if current_lang == "he":
                        ax.set_title(_rtl(f"פילוח אמצעי תשלום ({currency_symbol})"), fontsize=14, fontweight='bold', pad=20)
                    elif current_lang == "en":
                        ax.set_title(f"Payment Methods ({currency_symbol})", fontsize=14, fontweight='bold', pad=20)
                    else:  # ru
                        ax.set_title(f"{t('chart_payment_methods')} ({currency_symbol})", fontsize=14, fontweight='bold', pad=20)
                    
                    # Обеспечиваем круглую форму диаграммы
                    ax.axis('equal')
                    
                    # Подгоняем layout чтобы легенда не обрезалась
                    plt.tight_layout()

                    fname = _save_fig(fig, "payments.png")

                    # AI
                    total = float(pay[COL_SUM].sum()) or 1.0
                    top3 = (pay.sort_values(COL_SUM, ascending=False).head(3)
                                .assign(share=lambda d: (d[COL_SUM] / total).round(3))
                                [[pay_col, "share"]].to_dict(orient="records"))

                    brief = {"top_methods": top3}
                    chart_title_he = "פילוח אמצעי תשלום"
                    chart_title = t("chart_payment_methods")
                    ai = ai_explain(chart_title_he, brief, current_lang)

                    plots.append({
                        "filename": fname,
                        "title": t("chart_payment_methods"),
                        "note": t("chart_note_payment_methods"),
                        "ai": ai
                    })
                else:
                    messages.append("אין נתונים לגרף 'פילוח אמצעי תשלום'.")
            except Exception as e:
                print(f"⚠️ Skipping payment methods chart: {e}")
                # Пропускаем график, если нет нужных колонок

        else:
            print("⚠️ No payment method column found, skipping chart")

    # ------------------------------------------------------------------
    # 6️⃣ ממוצע קנייה (צ'ק ממוצע) לפי שעה — מתי מגיעים VIP
    # ------------------------------------------------------------------
    if opt_avg_ticket:
        try:
            # fallback: אם אין עמודת שעה עגולה
            if HOUR_COL not in df.columns and COL_TIME in df.columns:
                tmp_time = pd.to_datetime(df[COL_TIME].astype(str), errors="coerce")
                df[HOUR_COL] = tmp_time.dt.hour
            
            if HOUR_COL in df.columns and COL_TXN in df.columns:
                # חישוב ממוצע צ'ק לפי שעה
                hourly_stats = df.groupby(HOUR_COL).agg({
                    COL_SUM: 'sum',
                    COL_TXN: 'nunique'
                }).reset_index()
                hourly_stats['avg_ticket'] = hourly_stats[COL_SUM] / hourly_stats[COL_TXN].replace(0, 1)
                hourly_stats = hourly_stats[(hourly_stats[HOUR_COL] >= hour_start) & (hourly_stats[HOUR_COL] <= hour_end)]
                
                if not hourly_stats.empty:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    bars = ax.bar(hourly_stats[HOUR_COL], hourly_stats['avg_ticket'], color='#2ecc71')
                    # Переводим заголовки и подписи осей
                    if current_lang == "he":
                        ax.set_title(rtl(f"ממוצע קנייה לפי שעה (₪) {hour_start}:00–{hour_end}:00"))
                        ax.set_xlabel(rtl("שעה"))
                        ax.set_ylabel(rtl(f"ממוצע צ'ק ({get_currency('he')['symbol']})"))
                    elif current_lang == "en":
                        currency_sym = get_currency("en")["symbol"]
                        ax.set_title(f"Average Ticket by Hour ({currency_sym}) {hour_start}:00–{hour_end}:00")
                        ax.set_xlabel("Hour")
                        ax.set_ylabel(f"Average Ticket ({currency_sym})")
                    else:  # ru
                        currency_sym = get_currency(current_lang)["symbol"]
                        ax.set_title(t("chart_avg_ticket") + f" ({currency_sym}) {hour_start}:00–{hour_end}:00")
                        ax.set_xlabel(t("chart_axis_hour"))
                        ax.set_ylabel(t("chart_axis_avg_ticket") + f" ({currency_sym})")
                    ax.set_xticks(list(range(hour_start, hour_end + 1)))
                    
                    # הוספת ערכים על העמודות
                    for bar, val in zip(bars, hourly_stats['avg_ticket']):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                               f'{val:.0f}', ha='center', va='bottom', fontsize=8)
                    
                    fname = _save_fig(fig, "avg_ticket.png")
                    
                    best_hour = hourly_stats.loc[hourly_stats['avg_ticket'].idxmax()]
                    brief = {
                        "best_hour": int(best_hour[HOUR_COL]),
                        "best_avg": float(best_hour['avg_ticket']),
                        "overall_avg": float(hourly_stats['avg_ticket'].mean()),
                    }
                    chart_title_he = "ממוצע קנייה לפי שעה"
                    chart_title = t("chart_avg_ticket")
                    ai = ai_explain(chart_title_he, brief, current_lang)
                    
                    plots.append({
                        "filename": fname,
                        "title": chart_title,
                        "note": "באיזו שעה מגיעים לקוחות עם קניות גדולות יותר" if current_lang == "he" else ("At what hour customers come with larger purchases" if current_lang == "en" else "В какое время приходят клиенты с крупными покупками"),
                        "ai": ai
                    })
            else:
                messages.append("דילגנו על 'ממוצע קנייה' — חסרה עמודת שעה או מספר עסקה.")
        except Exception as e:
            print(f"⚠️ Skipping average ticket chart: {e}")
            # Пропускаем график, если нет нужных колонок

    # ------------------------------------------------------------------
    # 3️⃣ מפת חום (Heatmap) – שעה × יום בשבוע — ויזואליזציה מרשימה
    # ------------------------------------------------------------------
    if opt_heatmap:
        try:
            # fallback: אם אין עמודת שעה עגולה
            if HOUR_COL not in df.columns and COL_TIME in df.columns:
                tmp_time = pd.to_datetime(df[COL_TIME].astype(str), errors="coerce")
                df[HOUR_COL] = tmp_time.dt.hour
            # fallback: אם אין יום בשבוע
            if "יום בשבוע" not in df.columns and COL_DATE in df.columns:
                dtd = pd.to_datetime(df[COL_DATE].astype(str), errors="coerce")
                df["_weekday_eng"] = dtd.dt.day_name()
                heb = {"Sunday": "ראשון", "Monday": "שני", "Tuesday": "שלישי",
                       "Wednesday": "רביעי", "Thursday": "חמישי", "Friday": "שישי", "Saturday": "שבת"}
                df["יום בשבוע"] = df["_weekday_eng"].map(heb)
            
            if HOUR_COL in df.columns and "יום בשבוע" in df.columns:
                # יצירת pivot table
                heatmap_data = df.pivot_table(
                    values=COL_SUM, 
                    index="יום בשבוע", 
                    columns=HOUR_COL, 
                    aggfunc='sum',
                    fill_value=0
                )
                
                # סידור ימים בסדר נכון
                days_order = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
                existing_days = [d for d in days_order if d in heatmap_data.index]
                heatmap_data = heatmap_data.reindex(existing_days)
                
                # סינון שעות
                cols_to_keep = [c for c in heatmap_data.columns if hour_start <= c <= hour_end]
                heatmap_data = heatmap_data[cols_to_keep]
                
                if not heatmap_data.empty:
                    fig, ax = plt.subplots(figsize=(12, 5))
                    
                    # יצירת heatmap
                    im = ax.imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')
                    
                    # Маппинг дней недели на разные языки
                    day_mapping = {
                        "he": {"ראשון": "ראשון", "שני": "שני", "שלישי": "שלישי", "רביעי": "רביעי", "חמישי": "חמישי", "שישי": "שישי", "שבת": "שבת"},
                        "en": {"ראשון": "Sunday", "שני": "Monday", "שלישי": "Tuesday", "רביעי": "Wednesday", "חמישי": "Thursday", "שישי": "Friday", "שבת": "Saturday"},
                        "ru": {"ראשון": "Воскресенье", "שני": "Понедельник", "שלישי": "Вторник", "רביעי": "Среда", "חמישי": "Четверг", "שישי": "Пятница", "שבת": "Суббота"}
                    }
                    
                    # Переводим дни недели в зависимости от языка и применяем RTL для иврита
                    if current_lang in day_mapping:
                        translated_days = [day_mapping[current_lang].get(d, d) for d in heatmap_data.index]
                        # Применяем RTL для ивритских меток
                        if current_lang == "he":
                            translated_days = [rtl(day) for day in translated_days]
                    else:
                        translated_days = [rtl(d) for d in heatmap_data.index]
                    
                    # הגדרת labels
                    ax.set_xticks(range(len(heatmap_data.columns)))
                    ax.set_xticklabels([f'{int(h)}:00' for h in heatmap_data.columns])
                    ax.set_yticks(range(len(heatmap_data.index)))
                    ax.set_yticklabels(translated_days)
                    
                    # Переводим заголовки и подписи осей
                    if current_lang == "he":
                        ax.set_title(rtl("מפת חום: מכירות לפי שעה ויום"))
                        ax.set_xlabel(rtl("שעה"))
                        ax.set_ylabel(rtl("יום בשבוע"))
                    elif current_lang == "en":
                        ax.set_title("Heat Map: Sales by Hour and Day")
                        ax.set_xlabel("Hour")
                        ax.set_ylabel("Day of Week")
                    else:  # ru
                        ax.set_title(t("chart_heatmap") + ": " + t("chart_axis_sales") + " по " + t("chart_axis_hour") + " и " + t("chart_axis_day"))
                        ax.set_xlabel(t("chart_axis_hour"))
                        ax.set_ylabel(t("chart_axis_day"))
                    
                    # Colorbar
                    cbar = plt.colorbar(im, ax=ax)
                    # Переводим подпись colorbar
                    currency_info = get_currency(current_lang)
                    currency_symbol = currency_info["symbol"]
                    if current_lang == "he":
                        cbar.set_label(rtl(f'סה"כ מכירות ({currency_symbol})'))
                    elif current_lang == "en":
                        cbar.set_label(f"Total Sales ({currency_symbol})")
                    else:  # ru
                        cbar.set_label(t("summary_total_sales") + f" ({currency_symbol})")
                    
                    # הוספת ערכים בתאים
                    for i in range(len(heatmap_data.index)):
                        for j in range(len(heatmap_data.columns)):
                            val = heatmap_data.iloc[i, j]
                            color = 'white' if val > heatmap_data.values.max() * 0.5 else 'black'
                            ax.text(j, i, f'{val:,.0f}', ha='center', va='center', 
                                   fontsize=7, color=color)
                    
                    fname = _save_fig(fig, "heatmap.png")
                    
                    # מציאת שעה ויום הכי חזקים
                    max_idx = heatmap_data.stack().idxmax()
                    brief = {
                        "best_day": str(max_idx[0]),
                        "best_hour": int(max_idx[1]),
                        "best_value": float(heatmap_data.loc[max_idx[0], max_idx[1]]),
                    }
                    chart_title_he = "מפת חום מכירות"
                    chart_title = t("chart_heatmap")
                    ai = ai_explain(chart_title_he, brief, current_lang)
                    
                    plots.append({
                        "filename": fname,
                        "title": chart_title,
                        "note": "איפה הכסף מרוכז – שעות ×  ימים" if current_lang == "he" else ("Where money is concentrated – hours × days" if current_lang == "en" else "Где сосредоточены деньги – часы × дни"),
                        "ai": ai
                    })
            else:
                messages.append("דילגנו על 'מפת חום' — חסרה עמודת שעה או יום בשבוע.")
        except Exception as e:
            print(f"⚠️ Skipping heatmap chart: {e}")
            # Пропускаем график, если нет нужных колонок

    # ------------------------------------------------------------------
    # 7️⃣ סופ"ש מול ימי חול — השוואה ישראלית
    # ------------------------------------------------------------------
    if opt_weekend_compare:
        try:
            # fallback: אם אין יום בשבוע
            if "יום בשבוע" not in df.columns and COL_DATE in df.columns:
                dtd = pd.to_datetime(df[COL_DATE].astype(str), errors="coerce")
                df["_weekday_eng"] = dtd.dt.day_name()
                heb = {"Sunday": "ראשון", "Monday": "שני", "Tuesday": "שלישי",
                       "Wednesday": "רביעי", "Thursday": "חמישי", "Friday": "שישי", "Saturday": "שבת"}
                df["יום בשבוע"] = df["_weekday_eng"].map(heb)
            
            if "יום בשבוע" in df.columns:
                df_temp = df.copy()
                # בישראל: סופ"ש = שישי + שבת
                df_temp['_is_weekend'] = df_temp["יום בשבוע"].isin(["שישי", "שבת"])
                
                compare = df_temp.groupby('_is_weekend').agg({
                    COL_SUM: ['sum', 'mean', 'count']
                }).reset_index()
                compare.columns = ['is_weekend', 'total', 'avg', 'transactions']
                
                if len(compare) == 2:
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
                    
                    # Переводим метки
                    if current_lang == "he":
                        labels = [rtl('ימי חול'), rtl('סופ"ש (שישי-שבת)')]
                    elif current_lang == "en":
                        labels = ["Weekdays", "Weekend (Fri-Sat)"]
                    else:  # ru
                        labels = ["Будни", "Выходные (Пт-Сб)"]
                    colors = ['#3498db', '#9b59b6']
                    
                    # גרף 1: סה"כ מכירות
                    weekday_total = compare[compare['is_weekend'] == False]['total'].values[0]
                    weekend_total = compare[compare['is_weekend'] == True]['total'].values[0]
                    ax1.bar(labels, [weekday_total, weekend_total], color=colors)
                    
                    # Переводим заголовки и подписи осей
                    currency_info = get_currency(current_lang)
                    currency_symbol = currency_info["symbol"]
                    
                    if current_lang == "he":
                        ax1.set_title(rtl(f'סה"כ מכירות'))
                        ax1.set_ylabel(rtl(currency_symbol))
                        ax2.set_title(rtl('ממוצע עסקה'))
                        ax2.set_ylabel(rtl(currency_symbol))
                    elif current_lang == "en":
                        ax1.set_title("Total Sales")
                        ax1.set_ylabel(currency_symbol)
                        ax2.set_title("Average Transaction")
                        ax2.set_ylabel(currency_symbol)
                    else:  # ru
                        ax1.set_title(t("summary_total_sales"))
                        ax1.set_ylabel(currency_symbol)
                        ax2.set_title("Средняя транзакция")
                        ax2.set_ylabel(currency_symbol)
                    
                    for i, v in enumerate([weekday_total, weekend_total]):
                        ax1.text(i, v + v*0.02, f'{currency_symbol}{v:,.0f}', ha='center', fontsize=10)
                    
                    # גרף 2: ממוצע ליום
                    weekday_avg = compare[compare['is_weekend'] == False]['avg'].values[0]
                    weekend_avg = compare[compare['is_weekend'] == True]['avg'].values[0]
                    ax2.bar(labels, [weekday_avg, weekend_avg], color=colors)
                    for i, v in enumerate([weekday_avg, weekend_avg]):
                        ax2.text(i, v + v*0.02, f'{currency_symbol}{v:,.0f}', ha='center', fontsize=10)
                    
                    plt.tight_layout()
                    fname = _save_fig(fig, "weekend_compare.png")
                    
                    diff_pct = ((weekend_total - weekday_total) / weekday_total * 100) if weekday_total > 0 else 0
                    brief = {
                        "weekday_total": float(weekday_total),
                        "weekend_total": float(weekend_total),
                        "weekend_avg_ticket": float(weekend_avg),
                        "weekday_avg_ticket": float(weekday_avg),
                        "difference_pct": round(diff_pct, 1),
                    }
                    chart_title_he = "השוואת סופ״ש לימי חול"
                    chart_title = t("chart_weekend_compare")
                    ai = ai_explain(chart_title_he, brief, current_lang)
                    
                    plots.append({
                        "filename": fname,
                        "title": chart_title,
                        "note": "האם סופ\"ש חזק יותר או חלש יותר" if current_lang == "he" else ("Is weekend stronger or weaker?" if current_lang == "en" else "Выходные сильнее или слабее?"),
                        "ai": ai
                    })
            else:
                messages.append("דילגנו על 'סופ\"ש מול ימי חול' — חסרה עמודת יום בשבוע.")
        except Exception as e:
            print(f"⚠️ Skipping weekend comparison chart: {e}")
            # Пропускаем график, если нет нужных колонок


    # ===== אם אין גרפים =====
    if not plots:
        messages.append("לא הופקו גרפים—בדוק שהעמודות בדוח תואמות (תאריך, שעה, סכום (₪) לפחות).")

    # ===== סיכום כללי (AI) + שמירה ל-PDF + הפניה =====
        # ===== סיכום כללי (AI) + בניית SNAPSHOT זהה לאתר =====
    from datetime import datetime as _dt

    # סיכום מפורט
    try:
        total_sum = float(pd.to_numeric(df[COL_SUM], errors="coerce").fillna(0).sum())
        days = df[COL_DATE].nunique() if COL_DATE in df.columns else 0
        avg_day = total_sum / days if days else 0.0
        
        # חישובים נוספים
        transaction_count = len(df)
        avg_transaction = total_sum / transaction_count if transaction_count else 0
        
        # מציאת היום הכי טוב
        if COL_DATE in df.columns:
            daily_sales = df.groupby(COL_DATE)[COL_SUM].sum()
            best_day = daily_sales.idxmax() if len(daily_sales) > 0 else None
            best_day_sales = daily_sales.max() if len(daily_sales) > 0 else 0
            worst_day = daily_sales.idxmin() if len(daily_sales) > 0 else None
            worst_day_sales = daily_sales.min() if len(daily_sales) > 0 else 0
        else:
            best_day = worst_day = None
            best_day_sales = worst_day_sales = 0
        
        # --- Строим сводку сразу на трёх языках, чтобы при смене языка
        #     текст автоматически подстраивался без повторного анализа ---
        summary_map = {}

        # Иврит
        try:
            he_currency = get_currency("he")
            he_symbol = he_currency["symbol"]
            he_lines = [
                f"📊 סה\"כ מכירות: {he_symbol}{total_sum:,.0f}",
                f"📅 ימים בדוח: {days} | ממוצע יומי: {he_symbol}{avg_day:,.0f}",
                f"🧾 עסקאות: {transaction_count:,} | ממוצע לעסקה: {he_symbol}{avg_transaction:,.0f}",
            ]
            if best_day and worst_day and days > 1:
                he_lines.append(
                    f"🏆 היום הכי טוב: {he_symbol}{best_day_sales:,.0f} | היום הכי חלש: {he_symbol}{worst_day_sales:,.0f}"
                )
            summary_map["he"] = "\n".join(he_lines)
        except Exception as e_he:
            print(f"Summary HE error: {e_he}")

        # Английский
        try:
            en_currency = get_currency("en")
            en_symbol = en_currency["symbol"]
            en_lines = [
                f"📊 Total Sales: {en_symbol}{total_sum:,.0f}",
                f"📅 Days in Report: {days} | Daily Average: {en_symbol}{avg_day:,.0f}",
                f"🧾 Transactions: {transaction_count:,} | Average per Transaction: {en_symbol}{avg_transaction:,.0f}",
            ]
            if best_day and worst_day and days > 1:
                en_lines.append(
                    f"🏆 Best Day: {en_symbol}{best_day_sales:,.0f} | Weakest Day: {en_symbol}{worst_day_sales:,.0f}"
                )
            summary_map["en"] = "\n".join(en_lines)
        except Exception as e_en:
            print(f"Summary EN error: {e_en}")

        # Русский
        try:
            ru_currency = get_currency("ru")
            ru_symbol = ru_currency["symbol"]
            ru_lines = [
                f"📊 {t('summary_total_sales', 'ru')}: {ru_symbol}{total_sum:,.0f}",
                f"📅 {t('summary_days_in_report', 'ru')}: {days} | {t('summary_daily_avg', 'ru')}: {ru_symbol}{avg_day:,.0f}",
                f"🧾 {t('summary_transactions', 'ru')}: {transaction_count:,} | {t('summary_avg_per_transaction', 'ru')}: {ru_symbol}{avg_transaction:,.0f}",
            ]
            if best_day and worst_day and days > 1:
                ru_lines.append(
                    f"🏆 {t('summary_best_day', 'ru')}: {ru_symbol}{best_day_sales:,.0f} | {t('summary_weakest_day', 'ru')}: {ru_symbol}{worst_day_sales:,.0f}"
                )
            summary_map["ru"] = "\n".join(ru_lines)
        except Exception as e_ru:
            print(f"Summary RU error: {e_ru}")

        # Выбираем текст для текущего языка (fallback на иврит)
        summary_txt = summary_map.get(current_lang) or summary_map.get("he") or ""
    except Exception as e:
        print(f"Summary error: {e}")
        summary_txt = ""

    # טקסט AI כללי
    try:
        summary_title_he = "סיכום כללי לעסק"
        summary_ai_txt = ai_explain(summary_title_he,
                                    {"total": total_sum, "days": days, "avg_day": avg_day}, current_lang)
    except Exception:
        summary_ai_txt = ""


    # --- ROI אישי לחודש (על בסיס הדוח) ---
    try:
        roi_data = estimate_roi(df, ROIParams(
            service_cost=20.0,
            month_days_assumption=30.0,
            evening_hours=(17, 20),
            midday_hours=(11, 14),
            evening_target_ratio=0.5,
            weak_day_target="median",
            tail_boost_ratio=0.10,
            tail_share_cutoff=0.50
        ), current_lang)
    except Exception:
        roi_data = {"text": "", "monthly_gain": 0.0, "roi_percent": 0.0, "components": {}}

    # Данные будут сохранены ниже в LAST_EXPORT и session

    print(f"✅ נוצרו {len(plots)} גרפים, מפנים ל-/result")
    print(f"📊 Plots details: {[p.get('title', 'no title') for p in plots]}")
    
    # --- 📋 יצירת רשימת פעולות מומלצות ---
    try:
        action_items = generate_action_items(df, roi_data, current_lang)
    except Exception as e:
        print(f"⚠️ Failed to generate action items: {e}")
        action_items = []

    # --- 🔐 שמירה אוטומטית של הדוח למשתמשי Pro ---
    saved_report_id = None
    try:
        u = current_user()
        effective_plan = get_effective_plan(u) if u else "free"
        if u and effective_plan in ("pro", "premium", "admin"):
            report_id = save_report(
                user_id=u["id"], 
                df=df, 
                name=period_name if period_name else None,
                period_type=period_type,
                plots_info=plots,  # Сохраняем информацию о графиках
                roi_data=roi_data  # Сохраняем ROI данные
            )
            print(f"💾 דוח נשמר בהצלחה (ID: {report_id}, סוג: {period_type})")
            saved_report_id = report_id
        else:
            print(f"ℹ️ דוח לא נשמר - תוכנית: {effective_plan}")
    except Exception as e:
        print(f"⚠️ שגיאה בשמירת דוח: {e}")

    # שומרים הכל ב-LAST_EXPORT (גלובלי) וגם ב-session (למקרה של multi-worker)
    export_data = {
        "generated_at": _dt.now().isoformat(),
        "lang": current_lang,
        "plots": [
            {
                "filename": p.get("filename", ""),
                "title": p.get("title", ""),
                "note": p.get("note", ""),
                "ai": (p.get("ai") or "")[:400]  # חותך טקסטים ארוכים
            }
            for p in plots
        ],
        # summary может быть как строкой, так и dict c языками; сохраняем как есть
        "summary": summary_txt if summary_txt else "",
        "summary_ai": summary_ai_txt[:400] if summary_ai_txt else "",  # מוגבל ל-400 תווים
        "roi": roi_data,
        "action_items": action_items,
        "saved_report_id": saved_report_id
    }

    # שמירה ב-LAST_EXPORT (גלובלי - למקרה של single worker)
    LAST_EXPORT["generated_at"] = _dt.now()
    LAST_EXPORT["lang"] = current_lang
    LAST_EXPORT["plots"] = plots
    LAST_EXPORT["summary"] = summary_txt
    LAST_EXPORT["summary_ai"] = summary_ai_txt
    LAST_EXPORT["roi"] = roi_data
    LAST_EXPORT["action_items"] = action_items
    LAST_EXPORT["saved_report_id"] = saved_report_id
    
    # שמירה ב-session (למקרה של multi-worker на Render)
    # Сохраняем данные более надежно - копируем все ключи явно
    session["last_export"] = {
        "generated_at": export_data.get("generated_at"),
        "lang": export_data.get("lang"),
        "plots": export_data.get("plots", []),
        "summary": export_data.get("summary", ""),
        "summary_ai": export_data.get("summary_ai", ""),
        "roi": export_data.get("roi", {}),
        "action_items": export_data.get("action_items", []),
        "saved_report_id": export_data.get("saved_report_id")
    }
    session.permanent = True  # Делаем сессию постоянной для надежности
    session.modified = True
    
    # Дополнительная проверка сохранения
    saved_check = session.get("last_export", {})
    if saved_check.get("roi"):
        print(f"✅ ROI data saved to session: monthly_gain={saved_check['roi'].get('monthly_gain', 0)}")
    else:
        print(f"⚠️ Warning: ROI data not found in session after save!")
    
    # Проверяем, что данные действительно сохранились
    saved_plots_count = len(session.get("last_export", {}).get("plots", []))
    last_export_plots_count = len(LAST_EXPORT.get("plots", []))
    print(f"💾 Saved to LAST_EXPORT ({last_export_plots_count} plots) and session ({saved_plots_count} plots). Redirecting to /result")
    
    # Дополнительная проверка перед редиректом
    if not plots or len(plots) == 0:
        print(f"⚠️ WARNING: Redirecting to /result with EMPTY plots list!")
        print(f"⚠️ Selected options: hourly={opt_hourly}, weekday={opt_weekday}, daily={opt_daily}, top_products={opt_top_products}, payments={opt_payments}")
        print(f"⚠️ Plots variable: {plots}, type: {type(plots)}")
        # Если графики не выбраны, все равно редиректим, но с предупреждением
        # В result() будет показано сообщение "Нет графиков для отображения"
    else:
        print(f"✅ Successfully saved {len(plots)} plots, first plot filename: {plots[0].get('filename', 'N/A') if plots else 'N/A'}")

    # If guest uploaded successfully, mark them as used
    if is_guest:
        session["guest_upload_used"] = True
        session["is_guest_session"] = True
        print(f"✅ Guest marked as having used one-time upload")

    return redirect(url_for("result"))


@app.route("/demo-try")
@login_required
def demo_try():
    """
    Try demo analysis with sample cafe report - limited to one use per user.
    """
    u = current_user()
    if not u:
        flash("Please sign in to try the demo", "warning")
        return redirect(url_for("login"))
    
    # Ensure demo_used column exists
    db = get_db()
    cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
    if "demo_used" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN demo_used INTEGER DEFAULT 0")
        db.commit()
        # Re-fetch user to get updated schema
        u = db.execute("SELECT * FROM users WHERE id=?", (u["id"],)).fetchone()
    
    # Check if user already used demo
    demo_used = u['demo_used'] if 'demo_used' in u.keys() else 0
    if demo_used:
        current_lang = get_language()
        if current_lang == 'he':
            flash("כבר השתמשת בדמו. צור קשר אם תרצה לנסות שוב!", "warning")
        elif current_lang == 'ru':
            flash("Вы уже использовали демо. Свяжитесь с нами, если хотите попробовать снова!", "warning")
        else:
            flash("You've already used the demo. Contact us if you want to try again!", "warning")
        return redirect(url_for("about"))
    
    # Mark demo as used
    db.execute("UPDATE users SET demo_used = 1 WHERE id = ?", (u["id"],))
    db.commit()
    
    # Redirect to demo analyze
    return redirect(url_for("demo_analysis"))


@app.route("/demo")
def demo_analysis():
    """
    מציג ניתוח לדוגמה עם נתוני דמו קיימים.
    מאפשר למשתמשים לראות את התוצאות בלי להעלות קובץ משלהם.
    """
    import pandas as pd
    current_lang = get_language()  # Получаем текущий язык
    
    print("➡ Demo analysis requested")
    
    # טעינת קובץ הדמו - пробуем сначала xlsx, потом csv
    demo_file_xlsx = os.path.join(app.static_folder, "img", "cafe_monthly_report.xlsx")
    demo_file_csv = os.path.join(app.static_folder, "demo", "sample_sales.csv")
    
    demo_file = None
    if os.path.exists(demo_file_xlsx):
        demo_file = demo_file_xlsx
    elif os.path.exists(demo_file_csv):
        demo_file = demo_file_csv
    
    if not demo_file:
        current_lang = get_language()
        if current_lang == 'he':
            flash("קובץ הדמו לא נמצא", "danger")
        elif current_lang == 'ru':
            flash("Демо-файл не найден", "danger")
        else:
            flash("Demo file not found", "danger")
        return redirect(url_for("upload"))
    
    try:
        if demo_file.endswith('.xlsx'):
            df = pd.read_excel(demo_file)
        else:
            df = pd.read_csv(demo_file, encoding="utf-8")
    except Exception as e:
        flash(f"שגיאה בטעינת קובץ הדמו: {e}", "danger")
        return redirect(url_for("upload"))
    
    # נרמול עמודות
    df.columns = [c.strip() for c in df.columns]
    df = _normalize_columns(df)
    
    if df.empty:
        flash("קובץ הדמו ריק", "warning")
        return redirect(url_for("upload"))
    
    # ניקוי גרפים קודמים
    _clean_plots_dir()
    
    messages, plots = [], []
    
    # קביעת פרמטרים לדמו
    hour_start, hour_end = 6, 22
    
    # --- יצירת גרפים --- (используем тот же код, что и в основной функции)
    # 1) מכירות לפי שעה
    try:
        if COL_TIME in df.columns:
            # Добавляем колонку с округленным часом, если её нет
            if "שעה עגולה" not in df.columns:
                try:
                    df["שעה עגולה"] = pd.to_datetime(df[COL_TIME].astype(str), errors="coerce").dt.hour
                except:
                    df["שעה עגולה"] = pd.to_numeric(df[COL_TIME], errors="coerce")
            
            clip = df[(df["שעה עגולה"] >= hour_start) & (df["שעה עגולה"] <= hour_end)]
            hourly = clip.groupby("שעה עגולה")[COL_SUM].sum().reset_index()
            fig = plt.figure(figsize=(9,4))
            plt.bar(hourly["שעה עגולה"], hourly[COL_SUM])
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                plt.title(f"מכירות לפי שעה ({currency_symbol}) {hour_start}:00–{hour_end}:00")
                plt.xlabel("שעה")
                plt.ylabel(f'סה"כ ({currency_symbol})')
            elif current_lang == "en":
                plt.title(f"Sales by Hour ({currency_symbol}) {hour_start}:00–{hour_end}:00")
                plt.xlabel("Hour")
                plt.ylabel(f"Total ({currency_symbol})")
            else:  # ru
                plt.title(f"{t('chart_sales_by_hour')} ({currency_symbol}) {hour_start}:00–{hour_end}:00")
                plt.xlabel(t("chart_axis_hour"))
                plt.ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            fname = _save_fig(fig, "hourly.png")
            
            best_hour_row = hourly.loc[hourly[COL_SUM].idxmax()] if not hourly.empty else None
            max_hour = int(best_hour_row["שעה עגולה"]) if best_hour_row is not None else None
            brief = {
                "best_hour": max_hour,
                "best_hour_sum": float(hourly[COL_SUM].max()) if not hourly.empty else 0.0,
                "avg_hour": float(hourly[COL_SUM].mean()) if not hourly.empty else 0.0,
            }
            chart_title_he = "מכירות לפי שעה"
            chart_title = t("chart_sales_by_hour")
            ai_text = ai_explain(chart_title_he, brief, current_lang) if ai_enabled_for_user() else ""
            plots.append({
                "filename": fname, 
                "title": chart_title,
                "note": f"🕐 Peak hour: {max_hour}:00" if max_hour else t("chart_note_sales_by_hour"),
                "ai": ai_text
            })
    except Exception as e:
        print(f"⚠️ Demo hourly error: {e}")
        import traceback
        traceback.print_exc()
    
    # 2) מכירות לפי יום בשבוע
    try:
        if COL_DATE in df.columns:
            order_he = ["ראשון","שני","שלישי","רביעי","חמישי","שישי","שבת"]
            day_mapping = {
                "he": {"ראשון": "ראשון", "שני": "שני", "שלישי": "שלישי", "רביעי": "רביעי", "חמישי": "חמישי", "שישי": "שישי", "שבת": "שבת"},
                "en": {"ראשון": "Sunday", "שני": "Monday", "שלישי": "Tuesday", "רביעי": "Wednesday", "חמישי": "Thursday", "שישי": "Friday", "שבת": "Saturday"},
                "ru": {"ראשון": "Воскресенье", "שני": "Понедельник", "שלישי": "Вторник", "רביעי": "Среда", "חמישי": "Четверг", "שישי": "Пятница", "שבת": "Суббота"}
            }
            
            # Добавляем колонку "יום בשבוע" если её нет
            if "יום בשבוע" not in df.columns:
                ser_date = pd.to_datetime(df[COL_DATE], errors="coerce")
                map_he = {0:"ראשון",1:"שני",2:"שלישי",3:"רביעי",4:"חמישי",5:"שישי",6:"שבת"}
                df["יום בשבוע"] = ser_date.dt.dayofweek.map(map_he)
            
            by_wd = df.groupby("יום בשבוע")[COL_SUM].sum().reindex(order_he).reset_index()
            
            if current_lang in day_mapping:
                by_wd["יום בשבוע_translated"] = by_wd["יום בשבוע"].map(day_mapping[current_lang])
            else:
                by_wd["יום בשבוע_translated"] = by_wd["יום בשבוע"]
            
            fig = plt.figure(figsize=(8,4))
            plt.bar(by_wd["יום בשבוע_translated"], by_wd[COL_SUM])
            
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                plt.title(f"מכירות לפי יום בשבוע ({currency_symbol})")
                plt.xlabel("יום")
                plt.ylabel(f'סה"כ ({currency_symbol})')
            elif current_lang == "en":
                plt.title(f"Sales by Day of Week ({currency_symbol})")
                plt.xlabel("Day")
                plt.ylabel(f"Total ({currency_symbol})")
            else:  # ru
                plt.title(f"{t('chart_sales_by_weekday')} ({currency_symbol})")
                plt.xlabel(t("chart_axis_day"))
                plt.ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            fname = _save_fig(fig, "by_weekday.png")
            
            top = by_wd.sort_values(COL_SUM, ascending=False).iloc[0] if not by_wd.empty else None
            top_day_he = str(top["יום בשבוע"]) if top is not None else None
            top_day = day_mapping.get(current_lang, day_mapping["he"]).get(top_day_he, top_day_he) if top_day_he else None
            
            brief = {
                "best_day": top_day,
                "best_day_sum": float(top[COL_SUM]) if top is not None else 0.0,
                "avg_day": float(by_wd[COL_SUM].mean()) if not by_wd.empty else 0.0,
            }
            chart_title_he = "מכירות לפי יום בשבוע"
            chart_title = t("chart_sales_by_weekday")
            ai_text = ai_explain(chart_title_he, brief, current_lang) if ai_enabled_for_user() else ""
            plots.append({
                "filename": fname,
                "title": chart_title,
                "note": f"📅 Best day: {top_day}" if top_day else t("chart_note_sales_by_weekday"),
                "ai": ai_text
            })
    except Exception as e:
        print(f"⚠️ Demo weekday error: {e}")
        import traceback
        traceback.print_exc()
    
    # 3) Daily Sales
    try:
        if COL_DATE in df.columns:
            daily = df.groupby(COL_DATE)[COL_SUM].sum().reset_index()
            fig = plt.figure(figsize=(10,4))
            plt.bar(daily[COL_DATE].astype(str), daily[COL_SUM])
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                plt.title(f"מכירות יומיות ({currency_symbol})")
                plt.xlabel("תאריך")
                plt.ylabel(f'סה"כ ({currency_symbol})')
            elif current_lang == "en":
                plt.title(f"Daily Sales ({currency_symbol})")
                plt.xlabel("Date")
                plt.ylabel(f"Total ({currency_symbol})")
            else:  # ru
                plt.title(f"{t('chart_daily_sales')} ({currency_symbol})")
                plt.xlabel("Дата")
                plt.ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            plt.xticks(rotation=60)
            fname = _save_fig(fig, "daily.png")
            plots.append({"filename": fname, "title": t("chart_daily_sales"), "note": t("chart_note_daily_sales")})
    except Exception as e:
        print(f"⚠️ Demo daily error: {e}")
        import traceback
        traceback.print_exc()
    
    # 4) Top Products (если есть колонки)
    try:
        # Ищем колонку с продуктами
        product_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if any(word in col_lower for word in ['product', 'מוצר', 'producto', 'товар']):
                product_col = col
                break
        
        if product_col:
            # Quantity chart
            qty_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['quantity', 'כמות', 'cantidad', 'количество']):
                    qty_col = col
                    break
            
            if qty_col:
                qty = df.groupby(product_col)[qty_col].sum().sort_values(ascending=False).head(10).reset_index()
                fig = plt.figure(figsize=(9,4))
                plt.bar(qty[product_col].astype(str), qty[qty_col])
                if current_lang == "he":
                    plt.title("Top 10 — כמות לפי מוצר")
                    plt.ylabel("כמות")
                elif current_lang == "en":
                    plt.title("Top 10 — Quantity by Product")
                    plt.ylabel("Quantity")
                else:
                    plt.title("Top 10 — " + t("chart_top_quantity"))
                    plt.ylabel(t("chart_axis_quantity"))
                plt.xticks(rotation=40, ha="right")
                fname = _save_fig(fig, "top_qty.png")
                plots.append({"filename": fname, "title": t("chart_top_quantity"), "note": t("chart_note_top_quantity")})
            
            # Revenue chart
            revenue = df.groupby(product_col)[COL_SUM].sum().sort_values(ascending=False).head(10).reset_index()
            fig = plt.figure(figsize=(9,4))
            plt.bar(revenue[product_col].astype(str), revenue[COL_SUM])
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            if current_lang == "he":
                plt.title("Top 10 — הכנסות לפי מוצר")
                plt.ylabel(f'סה"כ ({currency_symbol})')
            elif current_lang == "en":
                plt.title("Top 10 — Revenue by Product")
                plt.ylabel(f"Total ({currency_symbol})")
            else:
                plt.title("Top 10 — " + t("chart_top_revenue"))
                plt.ylabel(t("chart_axis_total"))
            plt.xticks(rotation=40, ha="right")
            fname = _save_fig(fig, "top_rev.png")
            plots.append({"filename": fname, "title": t("chart_top_revenue"), "note": t("chart_note_top_revenue")})
    except Exception as e:
        print(f"⚠️ Demo products error: {e}")
        import traceback
        traceback.print_exc()
    
    # --- ROI ---
    try:
        roi_data = estimate_roi(df, ROIParams(
            service_cost=20.0,
            month_days_assumption=30,
            tail_share_cutoff=0.50
        ), current_lang)
    except Exception:
        roi_data = {"text": "", "monthly_gain": 0.0, "roi_percent": 0.0, "components": {}}
    
    # --- Action Items ---
    try:
        action_items = generate_action_items(df, roi_data, current_lang)
    except Exception as e:
        print(f"⚠️ Demo action items error: {e}")
        action_items = []
    
    # Проверка: если графиков нет, показываем ошибку
    if not plots or len(plots) == 0:
        current_lang = get_language()
        if current_lang == 'he':
            flash("לא ניתן ליצור גרפים מהדוח. בדוק שהעמודות נכונות (תאריך, שעה, סכום).", "warning")
        elif current_lang == 'ru':
            flash("Не удалось создать графики из отчета. Проверьте, что колонки правильные (дата, время, сумма).", "warning")
        else:
            flash("Could not create graphs from report. Check that columns are correct (date, time, amount).", "warning")
        return redirect(url_for("upload"))
    
    # --- סיכום ---
    total_sales = float(df[COL_SUM].sum()) if COL_SUM in df.columns else 0.0
    # Переводим текст сводки для демо
    if current_lang == "he":
        currency_info = get_currency(current_lang)
        currency_symbol = currency_info["symbol"]
        summary_txt = f"📊 דוגמה לניתוח | סה\"כ מכירות: {currency_symbol}{total_sales:,.0f} | {len(plots)} גרפים נוצרו"
    elif current_lang == "en":
        currency_info = get_currency(current_lang)
        currency_symbol = currency_info["symbol"]
        summary_txt = f"📊 Demo Analysis | Total Sales: {currency_symbol}{total_sales:,.0f} | {len(plots)} graphs created"
    else:  # ru
        currency_info = get_currency(current_lang)
        currency_symbol = currency_info["symbol"]
        summary_txt = f"📊 Демо-анализ | {t('summary_total_sales')}: {currency_symbol}{total_sales:,.0f} | Создано {len(plots)} графиков"
    
    # שמירה ב-LAST_EXPORT
    from datetime import datetime
    generated_at = datetime.now()
    LAST_EXPORT["generated_at"] = generated_at
    LAST_EXPORT["lang"] = current_lang
    LAST_EXPORT["plots"] = plots
    LAST_EXPORT["summary"] = summary_txt
    LAST_EXPORT["summary_ai"] = "זהו ניתוח לדוגמה. העלה דוח משלך לקבלת תובנות מותאמות!"
    LAST_EXPORT["roi"] = roi_data
    LAST_EXPORT["action_items"] = action_items
    
    # Также сохраняем в сессию для multi-worker окружений (например, Render)
    session["last_export"] = {
        "generated_at": generated_at.isoformat(),
        "lang": current_lang,
        "plots": plots,
        "summary": summary_txt,
        "summary_ai": "זהו ניתוח לדוגמה. העלה דוח משלך לקבלת תובנות מותאמות!",
        "roi": roi_data,
        "action_items": action_items
    }
    session.permanent = True
    session.modified = True
    
    print(f"✅ Demo: נוצרו {len(plots)} גרפים, сохранено в LAST_EXPORT и session")
    print(f"📊 Demo session data: plots={len(plots)}, summary={summary_txt[:50]}...")
    print(f"📊 Demo LAST_EXPORT: plots={len(LAST_EXPORT.get('plots', []))}")

    # Убеждаемся, что редирект идет на правильный URL
    result_url = url_for("result")
    print(f"🔄 Redirecting to: {result_url}")
    return redirect(result_url)


# ================================================================================
# DEAD CODE REMOVED: Duplicate graph generation that was never executed
# (After return redirect, code below was unreachable)
# ================================================================================


    # 4) מכירות יומיות - DEAD CODE START
    if opt_daily:
        try:
            daily = df.groupby("תאריך")["סכום (₪)"].sum().reset_index()
            fig = plt.figure(figsize=(10,4))
            plt.bar(daily["תאריך"].astype(str), daily["סכום (₪)"])
            # Переводим заголовки и подписи осей
            if current_lang == "he":
                plt.title("מכירות יומיות (₪)")
                plt.xlabel("תאריך")
                plt.ylabel("סה\"כ (₪)")
            elif current_lang == "en":
                plt.title("Daily Sales (₪)")
                plt.xlabel("Date")
                plt.ylabel("Total (₪)")
            else:  # ru
                plt.title(t("chart_daily_sales") + " (₪)")
                plt.xlabel("Дата")
                plt.ylabel(t("chart_axis_total"))
            plt.xticks(rotation=60)
            fname = _save_fig(fig, "daily.png")
            plots.append({"filename": fname, "title": "מכירות יומיות", "note": "תנודות יום־יומיות"})
        except Exception as e:
            messages.append(f"שגיאה: מכירות יומיות — {e}")

    # 5) מוצרים – כמות/הכנסות
    if opt_top_products:
        try:
            if "מוצר" in df.columns and "כמות" in df.columns:
                qty = df.groupby("מוצר")["כמות"].sum().sort_values(ascending=False).head(10).reset_index()
                fig = plt.figure(figsize=(9,4))
                plt.bar(qty["מוצר"], qty["כמות"])
                # Переводим заголовки и подписи осей
                if current_lang == "he":
                    plt.title("Top 10 — כמות לפי מוצר")
                    plt.ylabel("כמות")
                elif current_lang == "en":
                    plt.title("Top 10 — Quantity by Product")
                    plt.ylabel("Quantity")
                else:  # ru
                    plt.title("Top 10 — " + t("chart_top_quantity"))
                    plt.ylabel(t("chart_axis_quantity"))
                plt.xticks(rotation=40, ha="right")
                fname = _save_fig(fig, "top_qty.png")
                plots.append({"filename": fname, "title": t("chart_top_quantity"), "note": t("chart_note_top_quantity")})
            revenue = df.groupby("מוצר")["סכום (₪)"].sum().sort_values(ascending=False).head(10).reset_index()
            fig = plt.figure(figsize=(9,4))
            plt.bar(revenue["מוצר"], revenue["סכום (₪)"])
            # Переводим заголовки и подписи осей
            if current_lang == "he":
                plt.title("Top 10 — הכנסות לפי מוצר")
                plt.ylabel("סה\"כ (₪)")
            elif current_lang == "en":
                plt.title("Top 10 — Revenue by Product")
                plt.ylabel("Total (₪)")
            else:  # ru
                plt.title("Top 10 — " + t("chart_top_revenue"))
                plt.ylabel(t("chart_axis_total"))
            plt.xticks(rotation=40, ha="right")
            fname = _save_fig(fig, "top_rev.png")
            plots.append({"filename": fname, "title": t("chart_top_revenue"), "note": t("chart_note_top_revenue")})
        except Exception as e:
            messages.append(f"שגיאה: מוצרים – כמות/רווח — {e}")

    # 6) פילוח אמצעי תשלום
    if opt_payments:
        if "אמצעי תשלום" in df.columns:
            try:
                pay = df.groupby("אמצעי תשלום")["סכום (₪)"].sum().reset_index()
                fig = plt.figure(figsize=(6,6))
                plt.pie(pay["סכום (₪)"], labels=pay["אמצעי תשלום"], autopct="%1.0f%%", startangle=90)
                # Переводим заголовок
                if current_lang == "he":
                    plt.title("פילוח אמצעי תשלום (₪)")
                elif current_lang == "en":
                    plt.title("Payment Methods Breakdown (₪)")
                else:  # ru
                    plt.title(t("chart_payment_methods") + " (₪)")
                fname = _save_fig(fig, "payments.png")
                plots.append({"filename": fname, "title": t("chart_payment_methods"), "note": t("chart_note_payment_methods")})
            except Exception as e:
                messages.append(f"שגיאה: פילוח אמצעי תשלום — {e}")
        else:
            messages.append("לא נמצאה עמודה 'אמצעי תשלום' — דילגנו על הפילוח.")

    if not plots:
        messages.append("לא הופקו גרפים—בדוק שהעמודות בדוח תואמות (תאריך, שעה, סכום (₪) לפחות).")
        return _render()

    # ============ גרפים + הסברים ============
    # 1) לפי שעה
    if opt_hourly:
        try:
            clip = df[(df["שעה עגולה"] >= hour_start) & (df["שעה עגולה"] <= hour_end)]
            hourly = clip.groupby("שעה עגולה")[COL_SUM].sum().reset_index()
            fig = plt.figure(figsize=(9,4))
            plt.bar(hourly["שעה עגולה"], hourly[COL_SUM])
            # Переводим заголовки и подписи осей
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                plt.title(f"מכירות לפי שעה ({currency_symbol}) {hour_start}:00–{hour_end}:00")
                plt.xlabel("שעה")
                plt.ylabel(f'סה"כ ({currency_symbol})')
            elif current_lang == "en":
                plt.title(f"Sales by Hour ({currency_symbol}) {hour_start}:00–{hour_end}:00")
                plt.xlabel("Hour")
                plt.ylabel(f"Total ({currency_symbol})")
            else:  # ru
                plt.title(f"{t('chart_sales_by_hour')} ({currency_symbol}) {hour_start}:00–{hour_end}:00")
                plt.xlabel(t("chart_axis_hour"))
                plt.ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            fname = _save_fig(fig, "hourly.png")

            best_hour_row = hourly.loc[hourly[COL_SUM].idxmax()] if not hourly.empty else None
            weak_hour_row = hourly.loc[hourly[COL_SUM].idxmin()] if not hourly.empty else None
            brief = {
                "best_hour": int(best_hour_row["שעה עגולה"]) if best_hour_row is not None else None,
                "best_hour_sum": float(hourly[COL_SUM].max()) if not hourly.empty else 0.0,
                "weak_hour": int(weak_hour_row["שעה עגולה"]) if weak_hour_row is not None else None,
                "weak_hour_sum": float(hourly[COL_SUM].min()) if not hourly.empty else 0.0,
                "avg_hour": float(hourly[COL_SUM].mean()) if not hourly.empty else 0.0,
                "range": [hour_start, hour_end],
            }
            chart_title_he = "מכירות לפי שעה"
            chart_title = t("chart_sales_by_hour")
            ai = ai_explain(chart_title_he, brief, current_lang)
            plots.append({"filename": fname, "title": chart_title, "note": t("chart_note_sales_by_hour"), "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: מכירות לפי שעה — {e}")

    # 2) לפי יום בשבוע
    if opt_weekday:
        print(f"📊 Creating weekday chart, current_lang = {current_lang}")
        try:
            # Порядок дней на иврите (как в данных)
            order_he = ["ראשון","שני","שלישי","רביעי","חמישי","שישי","שבת"]
            # Маппинг дней недели на разные языки
            day_mapping = {
                "he": {"ראשון": "ראשון", "שני": "שני", "שלישי": "שלישי", "רביעי": "רביעי", "חמישי": "חמישי", "שישי": "שישי", "שבת": "שבת"},
                "en": {"ראשון": "Sunday", "שני": "Monday", "שלישי": "Tuesday", "רביעי": "Wednesday", "חמישי": "Thursday", "שישי": "Friday", "שבת": "Saturday"},
                "ru": {"ראשון": "Воскресенье", "שני": "Понедельник", "שלישי": "Вторник", "רביעי": "Среда", "חמישי": "Четверг", "שישי": "Пятница", "שבת": "Суббота"}
            }
            
            by_wd = df.groupby("יום בשבוע")[COL_SUM].sum().reindex(order_he).reset_index()
            
            # Переводим дни недели в зависимости от языка и применяем RTL для иврита
            if current_lang in day_mapping:
                by_wd["יום בשבוע_translated"] = by_wd["יום בשבוע"].map(day_mapping[current_lang])
                # Применяем RTL для ивритских меток
                if current_lang == "he":
                    by_wd["יום בשבוע_translated"] = by_wd["יום בשבוע_translated"].apply(rtl)
            else:
                by_wd["יום בשבוע_translated"] = by_wd["יום בשבוע"].apply(rtl)
            
            fig = plt.figure(figsize=(8,4))
            plt.bar(by_wd["יום בשבוע_translated"], by_wd[COL_SUM])
            
            # Переводим заголовки и подписи осей
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            print(f"📊 Weekday chart (second path): current_lang={current_lang}, currency_symbol={currency_symbol}")
            if current_lang == "he":
                plt.title(f"מכירות לפי יום בשבוע ({currency_symbol})")
                plt.xlabel("יום")
                plt.ylabel(f'סה"כ ({currency_symbol})')
            elif current_lang == "en":
                plt.title(f"Sales by Day of Week ({currency_symbol})")
                plt.xlabel("Day")
                plt.ylabel(f"Total ({currency_symbol})")
            else:  # ru
                plt.title(f"{t('chart_sales_by_weekday')} ({currency_symbol})")
                plt.xlabel(t("chart_axis_day"))
                plt.ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            fname = _save_fig(fig, "by_weekday.png")

            top = by_wd.sort_values(COL_SUM, ascending=False).iloc[0] if not by_wd.empty else None
            weak = by_wd.sort_values(COL_SUM, ascending=True).iloc[0] if not by_wd.empty else None
            
            # Переводим дни недели для brief
            best_day_he = str(top["יום בשבוע"]) if top is not None else None
            weak_day_he = str(weak["יום בשבוע"]) if weak is not None else None
            best_day_translated = day_mapping.get(current_lang, day_mapping["he"]).get(best_day_he, best_day_he) if best_day_he else None
            weak_day_translated = day_mapping.get(current_lang, day_mapping["he"]).get(weak_day_he, weak_day_he) if weak_day_he else None
            
            brief = {
                "best_day": best_day_translated,
                "best_day_sum": float(top[COL_SUM]) if top is not None else 0.0,
                "weak_day": weak_day_translated,
                "weak_day_sum": float(weak[COL_SUM]) if weak is not None else 0.0,
                "avg_day": float(by_wd[COL_SUM].mean()) if not by_wd.empty else 0.0,
            }
            chart_title_he = "מכירות לפי יום בשבוע"
            chart_title = t("chart_sales_by_weekday")
            ai = ai_explain(chart_title_he, brief, current_lang)
            plots.append({"filename": fname, "title": chart_title, "note": t("chart_note_sales_by_weekday"), "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: מכירות לפי יום בשבוע — {e}")

    # 3) יומי
    if opt_daily:
        try:
            daily = df.groupby(COL_DATE)[COL_SUM].sum().reset_index()
            fig = plt.figure(figsize=(10,4))
            plt.bar(daily[COL_DATE].astype(str), daily[COL_SUM])
            # Переводим заголовки и подписи осей
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                plt.title(f"מכירות יומיות ({currency_symbol})")
                plt.xlabel("תאריך")
                plt.ylabel(f'סה"כ ({currency_symbol})')
            elif current_lang == "en":
                plt.title(f"Daily Sales ({currency_symbol})")
                plt.xlabel("Date")
                plt.ylabel(f"Total ({currency_symbol})")
            else:  # ru
                plt.title(f"{t('chart_daily_sales')} ({currency_symbol})")
                plt.xlabel("Дата")
                plt.ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            plt.xticks(rotation=60)
            fname = _save_fig(fig, "daily.png")

            top = daily.sort_values(COL_SUM, ascending=False).iloc[0] if not daily.empty else None
            brief = {
                "best_date": (str(top[COL_DATE]) if top is not None else None),
                "best_sum": float(top[COL_SUM]) if top is not None else 0.0,
                "avg_daily": float(daily[COL_SUM].mean()) if not daily.empty else 0.0,
            }
            chart_title_he = "מכירות יומיות"
            chart_title = t("chart_daily_sales")
            ai = ai_explain(chart_title_he, brief, current_lang)
            plots.append({"filename": fname, "title": chart_title, "note": t("chart_note_daily_sales"), "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: מכירות יומיות — {e}")

    # 5) מוצרים
    if opt_top_products:
        try:
            # כמות (אם קיימת)
            if COL_QTY in df.columns:
                qty = df.groupby(COL_ITEM)[COL_QTY].sum().sort_values(ascending=False).head(10).reset_index()
                fig = plt.figure(figsize=(9,4))
                plt.bar(qty[COL_ITEM], qty[COL_QTY])
                # Переводим заголовки и подписи осей
                if current_lang == "he":
                    plt.title("Top 10 — כמות לפי מוצר")
                    plt.ylabel("כמות")
                elif current_lang == "en":
                    plt.title("Top 10 — Quantity by Product")
                    plt.ylabel("Quantity")
                else:  # ru
                    plt.title("Top 10 — " + t("chart_top_quantity"))
                    plt.ylabel(t("chart_axis_quantity"))
                plt.xticks(rotation=40, ha="right")
                fname1 = _save_fig(fig, "top_qty.png")
                brief1 = {
                    "top_item": (None if qty.empty else str(qty.iloc[0][COL_ITEM])),
                    "top_value": (0 if qty.empty else int(qty.iloc[0][COL_QTY])),
                }
                chart_title_he1 = "מוצרים – כמות"
                chart_title1 = t("chart_top_quantity")
                ai1 = ai_explain(chart_title_he1, brief1, current_lang)
                plots.append({"filename": fname1, "title": chart_title1, "note": t("chart_note_top_quantity"), "ai": ai1})
            else:
                messages.append("אין עמודת 'כמות' — דילגנו על Top 10 לפי כמות.")

            # הכנסות
            revenue = df.groupby(COL_ITEM)[COL_SUM].sum().sort_values(ascending=False).head(10).reset_index()
            fig = plt.figure(figsize=(9,4))
            plt.bar(revenue[COL_ITEM], revenue[COL_SUM])
            # Переводим заголовки и подписи осей
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                plt.title("Top 10 — הכנסות לפי מוצר")
                plt.ylabel(f'סה"כ ({currency_symbol})')
            elif current_lang == "en":
                plt.title("Top 10 — Revenue by Product")
                plt.ylabel(f"Total ({currency_symbol})")
            else:  # ru
                plt.title("Top 10 — " + t("chart_top_revenue"))
                plt.ylabel(f"{t('chart_axis_total')} ({currency_symbol})")
            plt.xticks(rotation=40, ha="right")
            fname2 = _save_fig(fig, "top_rev.png")
            
            # מציאת מוצרים פחות נמכרים (למטרת קומבו)
            all_items = df.groupby(COL_ITEM)[COL_SUM].sum().sort_values(ascending=True)
            bottom_items = all_items.head(5).to_dict() if len(all_items) > 5 else all_items.to_dict()
            
            brief2 = {
                "top_item": (None if revenue.empty else str(revenue.iloc[0][COL_ITEM])),
                "top_value": (0.0 if revenue.empty else float(revenue.iloc[0][COL_SUM])),
                "bottom_items": {str(k): float(v) for k, v in bottom_items.items()},
                "all_items": {str(k): float(v) for k, v in all_items.items()}
            }
            chart_title_he2 = "מוצרים – הכנסות"
            chart_title2 = t("chart_top_revenue")
            ai2 = ai_explain(chart_title_he2, brief2, current_lang)
            plots.append({"filename": fname2, "title": chart_title2, "note": t("chart_note_top_revenue"), "ai": ai2})
        except Exception as e:
            messages.append(f"שגיאה: מוצרים – כמות/רווח — {e}")

    # 6) אמצעי תשלום
    if opt_payments and COL_PAY in df.columns:
        try:
            pay = df.groupby(COL_PAY)[COL_SUM].sum().reset_index()
            labels = [str(x) for x in pay[COL_PAY].tolist()]
            values = pay[COL_SUM].tolist()
            
            # Красивая цветовая палитра
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
            colors = colors[:len(values)]
            
            # Создаем фигуру с местом для легенды справа
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Круговая диаграмма БЕЗ меток - только проценты
            wedges, texts, autotexts = ax.pie(
                values, 
                autopct="%1.0f%%", 
                startangle=90,
                colors=colors,
                pctdistance=0.75,
                textprops={'fontsize': 11, 'fontweight': 'bold', 'color': 'white'}
            )
            
            for autotext in autotexts:
                autotext.set_fontweight('bold')
            
            # Легенда справа с цветными метками
            ax.legend(
                wedges, 
                labels,
                title="",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
                fontsize=11
            )
            
            # Переводим заголовок
            currency_info = get_currency(current_lang)
            currency_symbol = currency_info["symbol"]
            
            if current_lang == "he":
                ax.set_title(f"פילוח אמצעי תשלום ({currency_symbol})", fontsize=14, fontweight='bold', pad=20)
            elif current_lang == "en":
                ax.set_title(f"Payment Methods ({currency_symbol})", fontsize=14, fontweight='bold', pad=20)
            else:  # ru
                ax.set_title(f"{t('chart_payment_methods')} ({currency_symbol})", fontsize=14, fontweight='bold', pad=20)
            
            ax.axis('equal')
            plt.tight_layout()
            fname = _save_fig(fig, "payments.png")

            total = float(pay[COL_SUM].sum()) or 1.0
            top3 = (pay.sort_values(COL_SUM, ascending=False).head(3)
                        .assign(share=lambda d: (d[COL_SUM] / total).round(3))
                        [[COL_PAY, "share"]].to_dict(orient="records"))
            brief = {"top_methods": top3}
            chart_title_he = "פילוח אמצעי תשלום"
            chart_title = t("chart_payment_methods")
            ai = ai_explain(chart_title_he, brief, current_lang)
            plots.append({"filename": fname, "title": chart_title, "note": t("chart_note_payment_methods"), "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: פילוח אמצעי תשלום — {e}")
    elif opt_payments and COL_PAY not in df.columns:
        messages.append("לא נמצאה עמודה 'אמצעי תשלום' — דילגנו על הפילוח.")

    if not plots:
        messages.append("לא הופקו גרפים—בדוק שהעמודות בדוח תואמות (תאריך, שעה, סכום (₪) לפחות).")
        return _render()

    # Этот код не должен выполняться, так как есть return redirect выше
    # Но оставляем его для совместимости, если по какой-то причине код дойдет сюда
    print(f"⚠️ WARNING: Reached code after return redirect! This should not happen.")
    return _render()
@app.route("/export/pdf")
def export_pdf():
    """
    יצוא PDF באמצעות WeasyPrint (ללא דפדפן) עם RTL תקין.
    כולל בלוק ROI מעוצב בדף הראשון + עמוד ROI מסכם (אם קיים ROI).
    Поддерживает загрузку из сохраненного отчета через параметр report_id.
    """
    import os, io, textwrap
    from datetime import datetime as _dt

    # ---------- 1) שליפת snapshot ----------
    u = current_user()
    plan = get_effective_plan(u) if u else "free"
    
    # DEBUG
    print(f"📄 PDF Export: plan={plan}, LAST_EXPORT plots count={len(LAST_EXPORT.get('plots', []))}")
    print(f"📄 PDF Export: Session has last_export: {bool(session.get('last_export'))}")
    
    if plan not in ("pro", "premium", "admin"):
        return render_template("upgrade_required.html", 
                               feature="הורדת PDF עם המלצות",
                               title="שדרוג נדרש"), 403
    
    # Проверяем, есть ли report_id в параметрах (для экспорта сохраненного отчета)
    report_id = request.args.get("report_id", type=int)
    
    if report_id:
        # Загружаем данные из сохраненного отчета
        print(f"📄 PDF Export: Loading from saved report {report_id}")
        try:
            df = load_report(report_id, u["id"])
            if df is None:
                current_lang = get_language()
                if current_lang == 'he':
                    return "דוח לא נמצא או אין הרשאה", 404
                elif current_lang == 'ru':
                    return "Отчет не найден или нет доступа", 404
                else:
                    return "Report not found or access denied", 404
            
            # Генерируем отчет заново из DataFrame
            # Получаем информацию о отчете из базы данных
            db = get_db()
            report_row = db.execute(
                "SELECT name, created_at, summary_json, currency FROM reports WHERE id = ? AND user_id = ?",
                (report_id, u["id"])
            ).fetchone()
            
            if not report_row:
                return "Report not found", 404
            
            report_name = report_row['name']
            created_at = report_row['created_at']
            summary_json = json.loads(report_row['summary_json'] or '{}')
            # sqlite3.Row doesn't have .get(), use direct access with try/except
            try:
                report_currency = report_row['currency'] or 'USD'
            except (KeyError, IndexError):
                report_currency = 'USD'
            
            # Определяем язык из валюты отчета или используем текущий
            if report_currency == 'ILS':
                report_lang = 'he'
            elif report_currency == 'RUB':
                report_lang = 'ru'
            else:
                report_lang = get_language()
            
            # Создаем snapshot из данных отчета
            # Загружаем графики и ROI из summary_json
            plots_from_db = summary_json.get("plots", [])
            roi_from_db = summary_json.get("roi", {})
            
            snap = {
                "generated_at": created_at,
                "lang": report_lang,
                "summary": f"Report: {report_name}",
                "summary_ai": "",
                "roi": roi_from_db,
                "plots": plots_from_db
            }
            
            # Язык PDF берём из текущей сессии, а не из сохраненного отчета
            # Это позволяет пользователю экспортировать PDF на любом языке
            pdf_lang_code = get_language()
            
            print(f"📄 PDF: Loaded from saved report {report_id}, name={report_name}, plots={len(plots_from_db)}, roi={bool(roi_from_db)}")
            
        except Exception as e:
            print(f"❌ Error loading report {report_id}: {e}")
            import traceback
            traceback.print_exc()
            current_lang = get_language()
            if current_lang == 'he':
                return f"שגיאה בטעינת דוח: {str(e)}", 500
            elif current_lang == 'ru':
                return f"Ошибка загрузки отчета: {str(e)}", 500
            else:
                return f"Error loading report: {str(e)}", 500
    else:
        # Пробуем получить данные из сессии, если нет - из LAST_EXPORT
        session_data = session.get("last_export", {})
        print(f"📄 PDF Export: session_data has {len(session_data.get('plots', []))} plots")
        
        if session_data:
            # Данные из сессии
            generated_at_str = session_data.get("generated_at", "")
            if generated_at_str:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(generated_at_str)
                    generated_at_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    generated_at_str = ""
            current_lang = get_language()
            raw_summary = session_data.get("summary", "")

            # summary может быть dict с языками или строкой
            if isinstance(raw_summary, dict):
                summary_for_lang = raw_summary.get(current_lang) or raw_summary.get("he") or ""
            else:
                summary_for_lang = raw_summary

            snap = {
                "generated_at": generated_at_str,
                "lang": session_data.get("lang") or get_language(),
                "summary": summary_for_lang,
                "summary_ai": session_data.get("summary_ai", ""),
                "roi": session_data.get("roi", {}),
                "plots": session_data.get("plots", []),
            }
            print(f"📄 PDF: Loaded from session, {len(snap.get('plots', []))} plots")
        else:
            # Fallback на LAST_EXPORT
            current_lang = get_language()
            raw_summary = LAST_EXPORT.get("summary", "")
            if isinstance(raw_summary, dict):
                summary_for_lang = raw_summary.get(current_lang) or raw_summary.get("he") or ""
            else:
                summary_for_lang = raw_summary

            snap = {
                "generated_at": (LAST_EXPORT.get("generated_at").strftime("%Y-%m-%d %H:%M")
                                 if LAST_EXPORT.get("generated_at") else ""),
                "lang": LAST_EXPORT.get("lang") or get_language(),
                "summary": summary_for_lang,
                "summary_ai": LAST_EXPORT.get("summary_ai", ""),
                "roi": LAST_EXPORT.get("roi", {}),
                "plots": LAST_EXPORT.get("plots", []),
            }
            print(f"📄 PDF: Loaded from LAST_EXPORT, {len(snap.get('plots', []))} plots")
        
        print(f"📄 PDF Snap: {len(snap.get('plots', []))} plots, ROI={bool(snap.get('roi'))}, lang={snap.get('lang')}")
        print(f"📄 PDF Snap plots detail: {[p.get('filename') for p in snap.get('plots', [])]}")

        # Проверка, есть ли данные для экспорта
        if not snap.get('plots') and not snap.get('summary') and not snap.get('roi'):
            current_lang = get_language()
            if current_lang == 'he':
                error_msg = "לא נמצאו נתונים לייצוא. אנא העלה דוח תחילה."
            elif current_lang == 'ru':
                error_msg = "Нет данных для экспорта. Пожалуйста, сначала загрузите отчет."
            else:
                error_msg = "No data found for export. Please upload a report first."
            return f"<h1>Error</h1><p>{error_msg}</p><p><a href='/'>Go back</a></p>", 404

        # Язык PDF берём из текущей сессии
        # Это позволяет пользователю видеть PDF на выбранном языке
        pdf_lang_code = get_language()

    # ---------- 2) עזרים ----------
    def _esc(s: str) -> str:
        return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def _file_url(p):
        p = os.path.abspath(p)
        return "file:///" + p.replace("\\", "/")

    def _img_url(fname):
        """Returns absolute file:// URL for weasyprint"""
        if not fname:
            return ""
        path = os.path.join(PLOTS_DIR, fname)
        if os.path.exists(path):
            abs_path = os.path.abspath(path).replace("\\", "/")
            return f"file:///{abs_path}"
        return ""
    
    def _img_base64(fname):
        """Returns base64 encoded image for embedding in HTML"""
        if not fname:
            print(f"⚠️ _img_base64: empty filename")
            return ""
        path = os.path.join(PLOTS_DIR, fname)
        print(f"🔍 _img_base64: checking {fname} at {path}")
        if os.path.exists(path):
            try:
                import base64
                with open(path, 'rb') as img_file:
                    img_data = img_file.read()
                    if len(img_data) == 0:
                        print(f"⚠️ _img_base64: {fname} is empty file")
                        return ""
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    # Detect image type from extension
                    ext = os.path.splitext(fname)[1].lower()
                    mime_type = 'image/png' if ext == '.png' else 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                    result = f"data:{mime_type};base64,{img_base64}"
                    print(f"✅ _img_base64: {fname} encoded, length={len(result)}")
                    return result
            except Exception as e:
                print(f"⚠️ Error encoding image {fname}: {e}")
                import traceback
                traceback.print_exc()
                return ""
        else:
            print(f"❌ _img_base64: file not found: {path}")
            # Try alternative paths
            alt_paths = [
                os.path.join(STATIC_DIR, "plots", fname),
                os.path.join(os.getcwd(), "static", "plots", fname),
                fname  # Maybe it's already a full path
            ]
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    print(f"✅ Found at alternative path: {alt_path}")
                    try:
                        import base64
                        with open(alt_path, 'rb') as img_file:
                            img_data = img_file.read()
                            if len(img_data) == 0:
                                continue
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            ext = os.path.splitext(fname)[1].lower()
                            mime_type = 'image/png' if ext == '.png' else 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                            return f"data:{mime_type};base64,{img_base64}"
                    except Exception as e:
                        print(f"⚠️ Error with alternative path {alt_path}: {e}")
                        continue
        return ""

    def _font_face_block():
        fonts_dir = os.path.join(STATIC_DIR, "fonts")
        noto = os.path.join(fonts_dir, "NotoSansHebrew-Regular.ttf")
        if os.path.exists(noto):
            # Use absolute path for weasyprint
            noto_path = os.path.abspath(noto).replace("\\", "/")
            return textwrap.dedent(f"""
            @font-face {{
              font-family: 'NotoSansHebrew';
              src: url('file://{noto_path}') format('truetype');
              font-weight: normal;
              font-style: normal;
            }}
            body {{ font-family: 'NotoSansHebrew', Arial, 'Segoe UI', sans-serif; }}
            """)
        return "body { font-family: Arial, 'Segoe UI', sans-serif; }"

    # No browser needed - using weasyprint

    # ---------- 3) ROI – הכנה בטוחה למשתנים ----------
    roi          = snap.get("roi") or {}
    comps        = roi.get("components") or {}
    c_weak       = comps.get("weak_day") or {}
    c_evening    = comps.get("evening_hours") or {}
    c_tail       = comps.get("tail_products") or {}

    roi_text     = _esc(roi.get("text") or "")
    roi_gain     = float(roi.get("monthly_gain") or 0.0)
    roi_pct      = float(roi.get("roi_percent") or 0.0)
    roi_gain_cons = float(roi.get("monthly_gain_conservative") or (roi_gain * 0.6))
    roi_gain_opt = float(roi.get("monthly_gain_optimistic") or (roi_gain * 1.4))
    roi_pct_cons = float(roi.get("roi_percent_conservative") or (roi_pct * 0.6))
    roi_pct_opt = float(roi.get("roi_percent_optimistic") or (roi_pct * 1.4))
    weak_gain    = float(c_weak.get("monthly_gain") or 0.0)
    evening_note = _esc(str(c_evening.get("note") or "ניצול שעות ערב"))
    evening_gain = float(c_evening.get("monthly_gain") or 0.0)
    tail_gain    = float(c_tail.get("monthly_gain") or 0.0)
    has_roi      = bool(roi_text or roi_gain or roi_pct)

    # Build table rows - translate based on current language
    current_lang = pdf_lang_code
    currency_info = get_currency(current_lang)
    currency_symbol = currency_info["symbol"]
    roi_rows = ""
    if weak_gain:
        if current_lang == 'he':
            roi_rows += f"<tr><td>יום חלש ↗︎</td><td>העלאה לרמת ימים רגילים</td><td>{currency_symbol}{weak_gain:,.0f}</td></tr>"
        elif current_lang == 'ru':
            roi_rows += f"<tr><td>Слабый день ↗︎</td><td>Поднятие до уровня обычных дней</td><td>{currency_symbol}{weak_gain:,.0f}</td></tr>"
        else:  # en
            roi_rows += f"<tr><td>Weak Day ↗︎</td><td>Raise to regular days level</td><td>{currency_symbol}{weak_gain:,.0f}</td></tr>"
    if evening_gain:
        evening_note_esc = _esc(evening_note)
        if current_lang == 'he':
            roi_rows += f"<tr><td>שעות ערב ↗︎</td><td>{evening_note_esc}</td><td>{currency_symbol}{evening_gain:,.0f}</td></tr>"
        elif current_lang == 'ru':
            roi_rows += f"<tr><td>Вечерние часы ↗︎</td><td>{evening_note_esc}</td><td>{currency_symbol}{evening_gain:,.0f}</td></tr>"
        else:  # en
            roi_rows += f"<tr><td>Evening Hours ↗︎</td><td>{evening_note_esc}</td><td>{currency_symbol}{evening_gain:,.0f}</td></tr>"
    if tail_gain:
        if current_lang == 'he':
            roi_rows += f"<tr><td>זנב מוצרים ↗︎</td><td>קידום תחתית סל המוצרים</td><td>{currency_symbol}{tail_gain:,.0f}</td></tr>"
        elif current_lang == 'ru':
            roi_rows += f"<tr><td>Хвост продуктов ↗︎</td><td>Продвижение нижней части корзины</td><td>{currency_symbol}{tail_gain:,.0f}</td></tr>"
        else:  # en
            roi_rows += f"<tr><td>Tail Products ↗︎</td><td>Promote bottom of product basket</td><td>{currency_symbol}{tail_gain:,.0f}</td></tr>"

    # Table headers
    if current_lang == 'he':
        th1, th2, th3 = "רכיב", "פירוט", "תרומה חודשית"
    elif current_lang == 'ru':
        th1, th2, th3 = "Компонент", "Детали", "Месячный вклад"
    else:  # en
        th1, th2, th3 = "Component", "Details", "Monthly Contribution"

    roi_table_html = (
        f"<div class='roi-table-wrap'>"
        f"<table class='roi-table'>"
        f"<thead><tr><th>{th1}</th><th>{th2}</th><th>{th3}</th></tr></thead>"
        f"<tbody>{roi_rows}</tbody></table></div>"
    ) if roi_rows else ""

    # ROI card for first page - translate based on current language
    current_lang = pdf_lang_code
    currency_info = get_currency(current_lang)
    currency_symbol = currency_info["symbol"]
    roi_inline_html = ""
    if has_roi:
        if current_lang == 'he':
            roi_header = "הערכת ROI (חודשי)"
            badge_label_monthly = "תוספת חודשית מוערכת"
            badge_label_roi = "ROI משוער"
        elif current_lang == 'ru':
            roi_header = "Оценка ROI (месячная)"
            badge_label_monthly = "Потенциальная месячная добавка"
            badge_label_roi = "Теоретический ROI"
        else:  # en
            roi_header = "ROI Estimation (Monthly)"
            badge_label_monthly = "Estimated Monthly Addition"
            badge_label_roi = "Estimated ROI"
        
        # Упрощенный заголовок без лишних деталей
        service_cost_label = (
            "עלות שירות: $20" if current_lang == 'he' else
            ("Стоимость услуги: $20" if current_lang == 'ru' else "Service cost: $20")
        )
        disclaimer = (
            "* הערכה זו מבוססת על ניתוח נתונים בלבד. תוצאות בפועל תלויות בפעולות שננקטו." if current_lang == 'he' else
            ("* Эта оценка основана только на анализе данных. Фактические результаты зависят от предпринятых действий." if current_lang == 'ru' else 
             "* This estimate is based on data analysis only. Actual results depend on actions taken.")
        )
        
        roi_inline_html = (
            f"<section class='roi-card' dir={'rtl' if current_lang == 'he' else 'ltr'}>"
            f"<div class='roi-header'>{roi_header}</div>"
            + f"""
            <div class="roi-badges">
              <div class="badge badge-green">
                <div class="badge-label">{badge_label_monthly}</div>
                <div class="badge-value">{currency_symbol}{roi_gain:,.0f}</div>
              </div>
              <div class="badge badge-blue">
                <div class="badge-label">{badge_label_roi}</div>
                <div class="badge-value">{roi_pct:,.0f}%</div>
              </div>
            </div>
            """
            + roi_table_html +
            f"""
            <div class="roi-scenarios" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #ddd;">
              <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                <div style="flex: 1; min-width: 140px; padding: 8px; background: rgba(239,68,68,0.08); border-radius: 8px; border: 1px solid rgba(239,68,68,0.25);">
                  <div style="font-size: 8.5pt; color: #666; margin-bottom: 2px;">""" + (
                    "שמרני (60%)" if current_lang == 'he' else 
                    ("Консервативный (60%)" if current_lang == 'ru' else "Conservative (60%)")
                  ) + """</div>
                  <div style="font-size: 14pt; font-weight: bold; color: #ef4444;">""" + f"{currency_symbol}{roi_gain_cons:,.0f}" + """</div>
                </div>
                <div style="flex: 1; min-width: 140px; padding: 8px; background: rgba(16,185,129,0.08); border-radius: 8px; border: 1px solid rgba(16,185,129,0.25);">
                  <div style="font-size: 8.5pt; color: #666; margin-bottom: 2px;">""" + (
                    "בסיסי (100%)" if current_lang == 'he' else 
                    ("Базовый (100%)" if current_lang == 'ru' else "Base (100%)")
                  ) + """</div>
                  <div style="font-size: 14pt; font-weight: bold; color: #10b981;">""" + f"{currency_symbol}{roi_gain:,.0f}" + """</div>
                </div>
                <div style="flex: 1; min-width: 140px; padding: 8px; background: rgba(34,197,94,0.08); border-radius: 8px; border: 1px solid rgba(34,197,94,0.25);">
                  <div style="font-size: 8.5pt; color: #666; margin-bottom: 2px;">""" + (
                    "אופטימי (140%)" if current_lang == 'he' else 
                    ("Оптимистичный (140%)" if current_lang == 'ru' else "Optimistic (140%)")
                  ) + """</div>
                  <div style="font-size: 14pt; font-weight: bold; color: #22c55e;">""" + f"{currency_symbol}{roi_gain_opt:,.0f}" + """</div>
                </div>
              </div>
              <div style="margin-top: 10px; font-size: 8.5pt; color: #666;">
                """ + service_cost_label + ". " + disclaimer + """
              </div>
            </div>
            """
            + "</section>"
        )

    # ---------- 4) HTML מלא ----------
    # Use snapshot language for PDF
    current_lang = pdf_lang_code
    currency_info = get_currency(current_lang)
    currency_symbol = currency_info["symbol"]
    
    if current_lang == 'he':
        pdf_title = "דו״ח ניתוח מכירות"
        pdf_dir = "rtl"
        pdf_lang = "he"
        date_label = "תאריך הפקה:"
    elif current_lang == 'ru':
        pdf_title = "Отчет анализа продаж"
        pdf_dir = "ltr"
        pdf_lang = "ru"
        date_label = "Дата создания:"
    else:  # en
        pdf_title = "Sales Analysis Report"
        pdf_dir = "ltr"
        pdf_lang = "en"
        date_label = "Generated:"
    
    html = textwrap.dedent(f"""
    <!doctype html>
    <html lang="{pdf_lang}" dir="{pdf_dir}">
    <head>
      <meta charset="utf-8">
      <title>{pdf_title}</title>
      <style>
        {_font_face_block()}
        @page {{
          size: A4;
          margin: 16mm;
        }}
        html, body {{
          direction: {pdf_dir};
          text-align: {'right' if pdf_dir == 'rtl' else 'left'};
          margin: 0; 
          padding: 0;
          background: #ffffff;
          width: 100%;
        }}
        .page {{
          width: 100%; 
          min-height: 100%;
          margin: 0;
          padding: 0;
          box-sizing: border-box;
          direction: {pdf_dir};
        }}
        h1 {{ 
          margin: 0 0 8mm 0; 
          font-size: 22pt; 
          text-align: {'right' if pdf_dir == 'rtl' else 'left'};
          direction: {pdf_dir};
        }}
        h2 {{ 
          margin: 10mm 0 4mm 0; 
          font-size: 14pt; 
          text-align: {'right' if pdf_dir == 'rtl' else 'left'};
          direction: {pdf_dir};
        }}
        p {{ 
          margin: 2mm 0; 
          font-size: 11pt; 
          line-height: 1.6; 
          white-space: pre-wrap; 
          text-align: {'right' if pdf_dir == 'rtl' else 'left'};
          direction: {pdf_dir};
        }}
        .meta {{ 
          color:#555; 
          margin-top: -6mm; 
          margin-bottom: 6mm; 
          text-align: {'right' if pdf_dir == 'rtl' else 'left'};
          direction: {pdf_dir};
        }}
        .plot {{ page-break-inside: avoid; margin: 8mm 0; }}
        .plot img {{ max-width: 100%; height: auto; display:block; margin: 3mm 0; }}
        .hr {{ border-top: 1px solid #ddd; margin: 6mm 0; }}

        /* ===== ROI Card ===== */
        .roi-card {{
          border: 1px solid #1b7f5e;
          background: linear-gradient(180deg, #f2fffa 0%, #ffffff 100%);
          border-radius: 10px;
          padding: 10mm;
          margin: 8mm 0;
          box-shadow: 0 1mm 3mm rgba(0,0,0,0.07);
          text-align: {'right' if pdf_dir == 'rtl' else 'left'};
          direction: {pdf_dir};
        }}
        .roi-header {{
          font-size: 16pt;
          font-weight: 800;
          color: #145a43;
          margin-bottom: 4mm;
        }}
        .roi-text {{
          font-size: 11pt;
          color: #222;
          margin-bottom: 6mm;
        }}
        .roi-badges {{
          display: flex;
          gap: 6mm;
          flex-wrap: wrap;
          align-items: stretch;
        }}
        .badge {{
          border-radius: 10px;
          padding: 7mm;
          min-width: 60mm;
          box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06);
        }}
        .badge-green {{ background:#eafff4; border:2px solid #2e8b57; }}
        .badge-blue  {{ background:#eef5ff; border:2px solid #3a71d1; }}
        .badge-label {{
          font-size: 10pt; color:#555; margin-bottom: 3mm; font-weight: 600;
        }}
        .badge-value {{
          font-size: 24pt; font-weight: 800; letter-spacing: 0.5px;
        }}

        /* ===== ROI Table ===== */
        .roi-table-wrap {{ margin-top: 6mm; }}
        .roi-table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 11pt;
          direction: {pdf_dir};
          text-align: {'right' if pdf_dir == 'rtl' else 'left'};
        }}
        .roi-table th, .roi-table td {{
          border: 1px solid #ccc;
          padding: 4mm 5mm;
          vertical-align: middle;
        }}
        .roi-table thead th {{
          background:#e8f5e9; font-weight:700; color: #145a43;
        }}
        .roi-table td:last-child {{
          font-weight: 700;
          color: #145a43;
        }}
      </style>
    </head>
    <body>
      <div class="page">
        <h1>{pdf_title}</h1>
        {"<div class='meta'>" + date_label + " " + _esc(snap.get("generated_at","")) + "</div>" if snap.get("generated_at") else ""}

        {"<p>" + _esc(snap.get("summary","")) + "</p>" if snap.get("summary") else ""}

        {"<p>" + _esc(snap.get("summary_ai","")) + "</p>" if snap.get("summary_ai") else ""}

        {roi_inline_html}

        <div class="hr"></div>

        {"".join(
            [
              (
                lambda p: (
                    lambda img_src: (
                f"<div class='plot'>"
                f"{('<h2>' + _esc(p.get('title','')) + '</h2>') if p.get('title') else ''}"
                        f"{('<img src=\"' + img_src + '\" alt=\"plot\" style=\"max-width: 100%; height: auto; display: block;\"/>') if img_src else ('<p style=\"color: red;\">Image not found: ' + _esc(p.get('filename', '')) + '</p>' if p.get('filename') else '')}"
                f"{('<p>' + _esc(p.get('ai','')) + '</p>') if p.get('ai') else ''}"
                f"</div>"
              )
                )(_img_base64(p.get('filename', '')))
              )(p)
              for p in (snap.get('plots') or [])
            ]
        )}
      </div>
    </body>
    </html>
    """)

    # ---------- 5) יצירת PDF באמצעות weasyprint (ללא דפדפן) ----------
    try:
        from weasyprint import HTML, CSS
        # Используем стандартную конфигурацию шрифтов WeasyPrint,
        # чтобы избежать проблем несовместимости версий
        print(f"📄 Creating PDF with weasyprint, {len(snap.get('plots', []))} plots")
        print(f"📄 PLOTS_DIR: {PLOTS_DIR}")
        
        # Verify images exist and test base64 encoding
        for plot in snap.get('plots', []):
            filename = plot.get('filename', '')
            if filename:
                img_path = os.path.join(PLOTS_DIR, filename)
                exists = os.path.exists(img_path)
                print(f"📄 Image: {filename} -> {img_path} exists={exists}")
                if exists:
                    # Test base64 encoding
                    base64_result = _img_base64(filename)
                    print(f"📄 Base64 for {filename}: {'OK' if base64_result else 'FAILED'} (length: {len(base64_result) if base64_result else 0})")
                else:
                    print(f"⚠️ Image file not found: {img_path}")
        
        # Create PDF from HTML
        # _img_url already returns absolute file:// URLs, so no base_url needed
        # Using simple approach without base_url
        pdf_bytes = HTML(string=html).write_pdf()
        
        print(f"✅ PDF created, size: {len(pdf_bytes)} bytes")
        
        data = io.BytesIO(pdf_bytes)
        fname = f"report_{_dt.now().strftime('%Y%m%d_%H%M')}.pdf"
        data.seek(0)
        return send_file(data, as_attachment=True, download_name=fname, mimetype="application/pdf")
        
    except ImportError as e:
        print(f"❌ WeasyPrint import error: {e}")
        current_lang = get_language()
        if current_lang == 'he':
            return "ספריית WeasyPrint לא מותקנת. אנא עדכן את requirements.txt.", 500
        elif current_lang == 'ru':
            return "Библиотека WeasyPrint не установлена. Пожалуйста, обновите requirements.txt.", 500
        else:
            return "WeasyPrint library is not installed. Please update requirements.txt.", 500
    except Exception as e:
        print(f"⚠️ PDF Export Error: {e}")
        import traceback
        traceback.print_exc()
        current_lang = get_language()
        if current_lang == 'he':
            error_msg = f"שגיאה ביצירת PDF: {str(e)}"
        elif current_lang == 'ru':
            error_msg = f"Ошибка создания PDF: {str(e)}"
        else:
            error_msg = f"Error creating PDF: {str(e)}"
        return error_msg, 500

















# ---------------- דפים סטטיים: צור קשר / תודה ----------------
@app.route("/pricing")
def pricing():
    """Pricing page with plan comparison"""
    u = current_user()
    current_plan = get_effective_plan(u) if u else 'free'
    trial_active = is_trial_active(u) if u else False
    # Всегда показываем цены в долларах на странице pricing
    currency_symbol = "$"
    return render_template("pricing.html", 
                         active="pricing", 
                         title="תוכניות ומחירים",
                         current_plan=current_plan,
                         trial_active=trial_active,
                         prices=PLAN_PRICES,
                         currency_symbol=currency_symbol)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("contact.html", active="contact", title=t("nav_contact"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "general").strip()
    message = request.form.get("message", "").strip()
    
    # שליחת מייל
    try:
        send_contact_email(name, email, message, subject)
        flash_t("contact_sent", "success")
    except Exception as e:
        print(f"⚠️ שגיאה בשליחת מייל: {e}")
        # עדיין שומרים את ההודעה לlog
        flash_t("contact_sent_received", "success")
    
    return redirect(url_for("contact"))

# ====== PayPal Helper Functions ======
import requests

def get_paypal_access_token():
    """Get PayPal access token for API calls"""
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        return None
    
    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(
        f"{PAYPAL_API_URL}/v1/oauth2/token",
        headers=headers,
        data="grant_type=client_credentials"
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"[PayPal] Failed to get access token: {response.status_code} - {response.text}")
    return None


def get_or_create_paypal_product():
    """Создает или получает продукт в PayPal (выполнить один раз)"""
    access_token = get_paypal_access_token()
    if not access_token:
        print("[PayPal] No access token available for product creation")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Проверяем, есть ли уже продукт
    response = requests.get(
        f"{PAYPAL_API_URL}/v1/catalogs/products",
        headers=headers,
        params={"page_size": 10, "total_required": "yes"}
    )
    
    if response.status_code == 200:
        products = response.json().get("products", [])
        for product in products:
            if product.get("name") == "OnePoweb":
                print(f"[PayPal] Found existing product: {product.get('id')}")
                return product.get("id")
    else:
        print(f"[PayPal] Failed to list products: {response.status_code} - {response.text[:500]}")
    
    # Создаем новый продукт
    product_data = {
        "name": "OnePoweb",
        "description": "OnePoweb - Smart Sales Analysis for Businesses",
        "type": "SERVICE",
        "category": "SOFTWARE"
    }
    
    print(f"[PayPal] Creating new product: {product_data}")
    response = requests.post(
        f"{PAYPAL_API_URL}/v1/catalogs/products",
        headers=headers,
        json=product_data
    )
    
    if response.status_code in [200, 201]:
        product_id = response.json().get("id")
        print(f"[PayPal] Created product: {product_id}")
        return product_id
    
    print(f"[PayPal] Failed to create product: {response.status_code} - {response.text[:500]}")
    return None


def get_or_create_paypal_plan(plan_name, price_usd, with_trial=False):
    """
    Создает или получает план подписки в PayPal.
    Возвращает plan_id или None.
    with_trial: если True, создает план с 7-дневным trial периодом
    """
    access_token = get_paypal_access_token()
    if not access_token:
        print("[PayPal] No access token available for plan creation")
        return None
    
    # Сначала получаем или создаем продукт
    product_id = get_or_create_paypal_product()
    if not product_id:
        print("[PayPal] Failed to get/create product")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Проверяем, есть ли уже план (с учетом trial)
    plan_name_search = f"OnePoweb {plan_name.upper()}" + (" (Trial)" if with_trial else "")
    response = requests.get(
        f"{PAYPAL_API_URL}/v1/billing/plans",
        headers=headers,
        params={"product_id": product_id, "page_size": 10}
    )
    
    if response.status_code == 200:
        plans = response.json().get("plans", [])
        for plan in plans:
            if plan.get("name") == plan_name_search and plan.get("status") == "ACTIVE":
                plan_id = plan.get("id")
                print(f"[PayPal] Found existing plan: {plan_id}")
                return plan_id
    else:
        print(f"[PayPal] Failed to list plans: {response.status_code} - {response.text[:500]}")
    
    # Создаем billing cycles
    billing_cycles = []
    
    # Если нужен trial - добавляем trial цикл (2 дня)
    if with_trial:
        billing_cycles.append({
            "frequency": {
                "interval_unit": "DAY",
                "interval_count": 2
            },
            "tenure_type": "TRIAL",
            "sequence": 1,
            "total_cycles": 1,
            "pricing_scheme": {
                "fixed_price": {
                    "value": "0.00",
                    "currency_code": "USD"
                }
            }
        })
    
    # Регулярный цикл (после trial или сразу)
    billing_cycles.append({
        "frequency": {
            "interval_unit": "MONTH",
            "interval_count": 1
        },
        "tenure_type": "REGULAR",
        "sequence": 2 if with_trial else 1,
        "total_cycles": 0,  # 0 = бесконечно (автоматическое продление)
        "pricing_scheme": {
            "fixed_price": {
                "value": f"{price_usd:.2f}",
                "currency_code": "USD"
            }
        }
    })
    
    # Создаем новый план
    plan_data = {
        "product_id": product_id,
        "name": plan_name_search,
        "description": f"Monthly subscription for OnePoweb {plan_name.upper()} plan" + (" with 2-day free trial, then PRO subscription" if with_trial else ""),
        "status": "ACTIVE",
        "billing_cycles": billing_cycles,
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        }
    }
    
    print(f"[PayPal] Creating new plan: {plan_name_search} with price ${price_usd}")
    response = requests.post(
        f"{PAYPAL_API_URL}/v1/billing/plans",
        headers=headers,
        json=plan_data
    )
    
    if response.status_code in [200, 201]:
        plan_id = response.json().get("id")
        print(f"[PayPal] Created plan: {plan_id}")
        return plan_id
    else:
        print(f"[PayPal] Failed to create plan: {response.status_code} - {response.text[:500]}")
        return None


def create_paypal_subscription_plan(plan_name, price_usd):
    """
    Создает план подписки в PayPal (выполнить один раз для каждого плана).
    Возвращает plan_id или None.
    """
    access_token = get_paypal_access_token()
    if not access_token:
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    plan_data = {
        "product_id": f"PROD_{plan_name.upper()}",  # Нужно создать продукт сначала
        "name": f"OnePoweb {plan_name.upper()} Plan",
        "description": f"Monthly subscription for OnePoweb {plan_name.upper()} plan",
        "status": "ACTIVE",
        "billing_cycles": [{
            "frequency": {
                "interval_unit": "MONTH",
                "interval_count": 1
            },
            "tenure_type": "REGULAR",
            "sequence": 1,
            "total_cycles": 0,  # 0 = бесконечно
            "pricing_scheme": {
                "fixed_price": {
                    "value": f"{price_usd:.2f}",
                    "currency_code": "USD"
                }
            }
        }],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        }
    }
    
    response = requests.post(
        f"{PAYPAL_API_URL}/v1/billing/plans",
        headers=headers,
        json=plan_data
    )
    
    if response.status_code in [200, 201]:
        return response.json().get("id")
    else:
        print(f"[PayPal] Failed to create plan: {response.text}")
        return None


@app.route("/paypal-debug")
@login_required
def paypal_debug():
    """Debug page for PayPal payment testing"""
    return render_template("paypal_debug.html")


@app.route("/subscribe")
@login_required
def subscribe():
    """Show checkout page with PayPal button"""
    plan = request.args.get("plan", "basic")
    trial = request.args.get("trial", "false").lower() == "true"  # Проверяем trial параметр
    
    if plan not in ("basic", "pro"):
        plan = "basic"

    u = current_user()
    if not u:
        flash_t("msg_login_required", "warning")
        return redirect(url_for("login"))
    
    # Проверка trial_used для trial подписки
    if trial:
        keys = u.keys() if hasattr(u, 'keys') else []
        trial_used = u["trial_used"] if "trial_used" in keys else 0
        if trial_used:
            flash_t("msg_trial_used", "warning")
            return redirect(url_for("profile"))
    
    try:
        ensure_user_ref_code(u["id"])
    except Exception as e:
        print(f"⚠️ Error ensuring ref_code: {e}")
        # Continue anyway - not critical
    
    # Calculate price
    base_price_usd = PLAN_PRICES[plan]["usd"]
    net_price_usd = base_price_usd

    # Ensure PayPal client ID is a string (not None)
    paypal_client_id = PAYPAL_CLIENT_ID or ""
    paypal_mode = PAYPAL_MODE or "sandbox"

    return render_template("checkout.html",
        plan=plan,
        base_price_usd=base_price_usd,
        net_price_usd=net_price_usd,
        with_trial=trial,
        paypal_client_id=paypal_client_id,
        paypal_mode=paypal_mode,
        title=t("checkout_order_summary")
    )


@app.route("/api/paypal/create-order", methods=["POST"])
@login_required
def paypal_create_order():
    """Create PayPal order"""
    try:
        data = request.get_json() or {}
        plan = data.get("plan", "basic")
        
        if plan not in ("basic", "pro"):
            return jsonify({"error": "Invalid plan"}), 400
        
        u = current_user()
        if not u:
            return jsonify({"error": "User not found"}), 401
        
        # Get user ID safely (handle sqlite3.Row object)
        try:
            if hasattr(u, 'keys') and "id" in u.keys():
                user_id = u["id"]
            else:
                u_dict = dict(u)
                user_id = u_dict.get("id")
            if not user_id:
                return jsonify({"error": "User ID not found"}), 401
        except (KeyError, TypeError, AttributeError):
            return jsonify({"error": "User ID not found"}), 401
        
        # Calculate price (no discounts)
        base_price_usd = PLAN_PRICES[plan]["usd"]
        net_price_usd = base_price_usd
        discount_usd = 0
        
        access_token = get_paypal_access_token()
        if not access_token:
            print("[PayPal] Failed to get access token")
            print(f"[PayPal] PAYPAL_CLIENT_ID configured: {bool(PAYPAL_CLIENT_ID)}")
            print(f"[PayPal] PAYPAL_SECRET configured: {bool(PAYPAL_SECRET)}")
            return jsonify({"error": "PayPal payment system is not configured. Please contact support."}), 500
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Create subscription using PayPal Subscriptions API
        # First, get or create the subscription plan
        plan_id = get_or_create_paypal_plan(plan, base_price_usd)
        if not plan_id:
            print("[PayPal] Failed to get/create subscription plan")
            print(f"[PayPal] Plan: {plan}, Price: {base_price_usd}")
            return jsonify({"error": "Failed to create subscription plan. Please contact support."}), 500
        
        # Calculate start time (immediate payment)
        from datetime import datetime, timedelta
        start_time = datetime.utcnow() + timedelta(minutes=1)  # Start in 1 minute
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Get user info (handle sqlite3.Row object)
        try:
            if hasattr(u, 'keys') and "first_name" in u.keys():
                user_first_name = u["first_name"] or "User"
                user_last_name = u["last_name"] or ""
                user_email = u["email"] or ""
            else:
                u_dict = dict(u)
                user_first_name = u_dict.get("first_name") or "User"
                user_last_name = u_dict.get("last_name") or ""
                user_email = u_dict.get("email") or ""
        except (KeyError, TypeError, AttributeError):
            user_first_name = "User"
            user_last_name = ""
            user_email = ""
        
        subscription_data = {
            "plan_id": plan_id,
            "start_time": start_time_str,
            "subscriber": {
                "name": {
                    "given_name": user_first_name,
                    "surname": user_last_name
                },
                "email_address": user_email
            },
            "application_context": {
                "brand_name": "OnePoweb",
                "locale": "en-US",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                },
                "landing_page": "BILLING",
                "return_url": url_for("paypal_subscription_return", _external=True),
                "cancel_url": url_for("subscribe", plan=plan, _external=True)
            },
            "custom_id": str(user_id)
        }
        
        # If discount, we need to apply it (for subscriptions, PayPal handles discounts differently)
        # For now, creating subscription with full price, discount will be handled via referral system
        
        print(f"[PayPal] Creating subscription: {subscription_data}")
        
        response = requests.post(
            f"{PAYPAL_API_URL}/v1/billing/subscriptions",
            headers=headers,
            json=subscription_data
        )
        
        print(f"[PayPal] Response status: {response.status_code}")
        print(f"[PayPal] Response body: {response.text[:1000]}")
        
        if response.status_code in [200, 201]:
            subscription = response.json()
            subscription_id = subscription.get("id")
            approval_url = None
            
            # Get approval link from response
            for link in subscription.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    # Add parameters to directly show card form
                    if approval_url:
                        # Add fundingSource parameter to skip login and show card form directly
                        separator = "&" if "?" in approval_url else "?"
                        approval_url = f"{approval_url}{separator}fundingSource=card"
                    break
            
            if not approval_url:
                print(f"[PayPal] No approval URL in subscription response: {subscription}")
                return jsonify({"error": "Failed to get approval URL"}), 500
            
            # Store subscription info in session for verification
            session["pending_subscription"] = {
                "subscription_id": subscription_id,
                "plan": plan,
                "amount_usd": net_price_usd,
                "discount_used": 0
            }
            
            # Return approval URL for redirect
            return jsonify({"id": subscription_id, "approval_url": approval_url})
        else:
            print(f"[PayPal] Error: {response.text}")
            return jsonify({"error": f"PayPal error: {response.status_code}"}), 500
            
    except Exception as e:
        print(f"[PayPal] Exception in create-order: {str(e)}")
        import traceback
        print(f"[PayPal] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Payment system error: {str(e)}"}), 500


@app.route("/api/paypal/capture-order", methods=["POST"])
@login_required
def paypal_capture_order():
    """Handle subscription approval (deprecated - now using return_url)"""
    # This endpoint is kept for backward compatibility
    # Subscriptions are now handled via return_url callback
    return jsonify({"error": "Use return URL instead"}), 400


@app.route("/api/paypal/create-subscription-id", methods=["POST"])
@login_required
def paypal_create_subscription_id():
    """Create PayPal subscription and return ID only (no redirect) for inline payment"""
    try:
        data = request.get_json() or {}
        plan = data.get("plan", "basic")
        with_trial = data.get("trial", False)  # Проверяем, нужен ли trial
        
        if plan not in ("basic", "pro"):
            return jsonify({"error": "Invalid plan"}), 400
        
        u = current_user()
        if not u:
            return jsonify({"error": "User not found"}), 401
        
        # Проверка trial_used для trial подписки
        try:
            if hasattr(u, 'keys') and "trial_used" in u.keys():
                trial_used = u["trial_used"]
            else:
                u_dict = dict(u)
                trial_used = u_dict.get("trial_used", 0)
        except (KeyError, TypeError, AttributeError):
            trial_used = 0
        
        if with_trial and trial_used:
            return jsonify({"error": "Trial period already used"}), 400
        
        # Get user ID safely
        try:
            if hasattr(u, 'keys') and "id" in u.keys():
                user_id = u["id"]
            else:
                u_dict = dict(u)
                user_id = u_dict.get("id")
            if not user_id:
                return jsonify({"error": "User ID not found"}), 401
        except (KeyError, TypeError, AttributeError):
            return jsonify({"error": "User ID not found"}), 401
        
        # Get base price
        base_price_usd = PLAN_PRICES[plan]["usd"]
        net_price_usd = base_price_usd
        
        access_token = get_paypal_access_token()
        if not access_token:
            print("[PayPal] Failed to get access token")
            return jsonify({"error": "PayPal payment system is not configured."}), 500
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get or create subscription plan (с trial если нужно)
        plan_id = get_or_create_paypal_plan(plan, base_price_usd, with_trial=with_trial)
        if not plan_id:
            return jsonify({"error": "Failed to create subscription plan."}), 500
        
        # Get user info safely
        try:
            if hasattr(u, 'keys') and "first_name" in u.keys():
                user_first_name = u["first_name"] or "User"
                user_last_name = u["last_name"] or ""
                user_email = u["email"] or ""
            else:
                u_dict = dict(u)
                user_first_name = u_dict.get("first_name") or "User"
                user_last_name = u_dict.get("last_name") or ""
                user_email = u_dict.get("email") or ""
        except (KeyError, TypeError, AttributeError):
            user_first_name = "User"
            user_last_name = ""
            user_email = ""
        
        from datetime import datetime, timedelta
        start_time = datetime.utcnow() + timedelta(minutes=1)
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        subscription_data = {
            "plan_id": plan_id,
            "start_time": start_time_str,
            "subscriber": {
                "name": {
                    "given_name": user_first_name,
                    "surname": user_last_name
                },
                "email_address": user_email
            },
            "application_context": {
                "brand_name": "OnePoweb",
                "locale": "en-US",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                }
            },
            "custom_id": str(user_id)
        }
        
        print(f"[PayPal] Creating subscription (inline): {subscription_data}")
        
        response = requests.post(
            f"{PAYPAL_API_URL}/v1/billing/subscriptions",
            headers=headers,
            json=subscription_data
        )
        
        print(f"[PayPal] Response status: {response.status_code}")
        print(f"[PayPal] Response body: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            subscription = response.json()
            subscription_id = subscription.get("id")
            
            # Store subscription info in session
            session["pending_subscription"] = {
                "subscription_id": subscription_id,
                "plan": plan,
                "amount_usd": net_price_usd,
                "discount_used": 0  # No discounts after removing referral system
            }
            
            # Return ONLY the subscription ID - no approval_url
            # PayPal SDK will handle the payment inline
            return jsonify({"id": subscription_id})
        else:
            print(f"[PayPal] Error: {response.text}")
            return jsonify({"error": f"PayPal error: {response.status_code}"}), 500
            
    except Exception as e:
        print(f"[PayPal] Exception in create-subscription-id: {str(e)}")
        import traceback
        print(f"[PayPal] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Payment error: {str(e)}"}), 500


@app.route("/api/paypal/activate-subscription", methods=["POST"])
@login_required
def paypal_activate_subscription_api():
    """Activate subscription after inline payment approval"""
    try:
        data = request.get_json() or {}
        subscription_id = data.get("subscription_id")
        plan = data.get("plan", "basic")
        with_trial = data.get("trial", False)  # Проверяем, была ли это trial подписка
        
        if not subscription_id:
            return jsonify({"error": "Subscription ID required"}), 400
        
        u = current_user()
        if not u:
            return jsonify({"error": "User not found"}), 401
        
        # Get user ID safely
        try:
            if hasattr(u, 'keys') and "id" in u.keys():
                user_id = u["id"]
            else:
                u_dict = dict(u)
                user_id = u_dict.get("id")
        except (KeyError, TypeError, AttributeError):
            return jsonify({"error": "User ID not found"}), 401
        
        # Verify subscription with PayPal
        access_token = get_paypal_access_token()
        if access_token:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{PAYPAL_API_URL}/v1/billing/subscriptions/{subscription_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                sub_data = response.json()
                status = sub_data.get("status")
                print(f"[PayPal] Subscription {subscription_id} status: {status}")
                
                if status not in ["ACTIVE", "APPROVED"]:
                    return jsonify({"error": f"Subscription not active: {status}"}), 400
            else:
                print(f"[PayPal] Warning: Could not verify subscription: {response.status_code}")
        
        # Get discount from session
        pending = session.get("pending_subscription", {})
        discount_used = pending.get("discount_used", 0)
        
        # Activate subscription
        result = activate_subscription(user_id, plan, {"subscription_id": subscription_id, "discount": discount_used})
        
        # Если это была trial подписка - помечаем trial_used
        if with_trial:
            from datetime import datetime, timedelta
            trial_until_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            db = get_db()
            db.execute("UPDATE users SET trial_used = 1, trial_until = ? WHERE id = ?", (trial_until_date, user_id))
            db.commit()
            print(f"[PayPal] Marked trial_used and set trial_until to {trial_until_date} for user {user_id}")
        
        # Clear pending subscription
        session.pop("pending_subscription", None)
        
        # Return success response
        success_url = url_for("subscribe_success", plan=plan)
        return jsonify({"success": True, "redirect": success_url})
        
    except Exception as e:
        print(f"[PayPal] Exception in activate-subscription: {str(e)}")
        import traceback
        print(f"[PayPal] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Activation error: {str(e)}"}), 500


@app.route("/api/paypal/subscription-return")
@login_required
def paypal_subscription_return():
    """Handle return from PayPal after subscription approval"""
    try:
        # PayPal adds subscription_id and token to return URL
        subscription_id = request.args.get("subscription_id")
        token = request.args.get("token")
        
        u = current_user()
        if not u:
            flash_t("msg_login_required", "warning")
            return redirect(url_for("login"))
        
        if not subscription_id:
            # Try to get from session
            pending = session.get("pending_subscription", {})
            subscription_id = pending.get("subscription_id")
        
        if not subscription_id:
            flash("Subscription ID missing", "error")
            return redirect(url_for("subscribe", plan="basic"))
        
        # Verify subscription in PayPal
        access_token = get_paypal_access_token()
        if not access_token:
            flash("PayPal not configured", "error")
            return redirect(url_for("subscribe", plan="basic"))
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{PAYPAL_API_URL}/v1/billing/subscriptions/{subscription_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"[PayPal] Failed to get subscription: {response.text}")
            flash("Failed to verify subscription", "error")
            return redirect(url_for("subscribe", plan="basic"))
        
        subscription_data = response.json()
        subscription_status = subscription_data.get("status")
        
        print(f"[PayPal] Subscription status: {subscription_status}")
        print(f"[PayPal] Full subscription data: {json.dumps(subscription_data, indent=2)[:500]}")
        
        # Check if subscription is active or approved
        if subscription_status in ["ACTIVE", "APPROVAL_PENDING", "APPROVED"]:
            # Get plan from subscription plan_id
            plan_id_paypal = subscription_data.get("plan_id", "")
            plan = "basic" if "BASIC" in plan_id_paypal.upper() else "pro" if "PRO" in plan_id_paypal.upper() else "basic"
            
            # Get discount from session if available
            pending = session.get("pending_subscription", {})
            discount_used = pending.get("discount_used", 0)
            
            # Activate subscription in our database
            db = get_db()
            cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
            
            if "paypal_subscription_id" in cols and "canceled_at" in cols:
                db.execute("""
                    UPDATE users 
                    SET plan=?, paypal_subscription_id=?, canceled_at=NULL, referral_discount=0
                    WHERE id=?
                """, (plan, subscription_id, u["id"]))
            elif "paypal_subscription_id" in cols:
                db.execute("""
                    UPDATE users 
                    SET plan=?, paypal_subscription_id=?, referral_discount=0
                    WHERE id=?
                """, (plan, subscription_id, u["id"]))
            else:
                db.execute("""
                    UPDATE users 
                    SET plan=?, canceled_at=NULL, referral_discount=0
                    WHERE id=?
                """, (plan, u["id"]))
            db.commit()

            # Clear pending subscription from session
            session.pop("pending_subscription", None)
            
            print(f"[PayPal] Subscription activated for user {u['id']}, plan: {plan}, subscription_id: {subscription_id}")
            
            flash_t("msg_subscription_active", "success")
            return redirect(url_for("subscribe_success", plan=plan))
        else:
            flash(f"Subscription status: {subscription_status}. Please contact support.", "warning")
            return redirect(url_for("subscribe", plan="basic"))
            
    except Exception as e:
        print(f"[PayPal] Subscription return error: {e}")
        import traceback
        traceback.print_exc()
        flash("Error processing subscription", "error")
        return redirect(url_for("subscribe", plan="basic"))


def activate_subscription(user_id, plan, subscription_info=None):
    """Activate subscription after successful payment"""
    try:
        print(f"[Activate] Starting subscription activation for user {user_id}, plan: {plan}")
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        
        if not u:
            print(f"[Activate] ERROR: User {user_id} not found in database")
            return jsonify({"error": "User not found"}), 404
        
        print(f"[Activate] User found: {u['email'] if 'email' in dict(u).keys() else 'N/A'}")
        
        # Ensure all required columns exist
        cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        if "canceled_at" not in cols:
            print(f"[Activate] Adding canceled_at column to users table")
            try:
                db.execute("ALTER TABLE users ADD COLUMN canceled_at TEXT NULL")
                db.commit()
                print(f"[Activate] canceled_at column added successfully")
            except Exception as e:
                print(f"[Activate] Warning: Could not add canceled_at column: {e}")
        
        # Update user plan and store PayPal subscription_id if provided
        cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        subscription_id_param = None
        if isinstance(subscription_info, dict) and "subscription_id" in subscription_info:
            subscription_id_param = subscription_info["subscription_id"]
        
        if "canceled_at" in cols:
            if "paypal_subscription_id" in cols and subscription_id_param:
                db.execute("""
                    UPDATE users 
                    SET plan=?, canceled_at=NULL, paypal_subscription_id=?
                    WHERE id=?
                """, (plan, subscription_id_param, user_id))
            else:
                db.execute("""
                    UPDATE users 
                    SET plan=?, canceled_at=NULL 
                    WHERE id=?
                """, (plan, user_id))
        else:
            if "paypal_subscription_id" in cols and subscription_id_param:
                db.execute("""
                    UPDATE users 
                    SET plan=?, paypal_subscription_id=?
                    WHERE id=?
                """, (plan, subscription_id_param, user_id))
            else:
                db.execute("""
                    UPDATE users 
                    SET plan=?
                    WHERE id=?
                """, (plan, user_id))
        db.commit()
        print(f"[Activate] User plan updated to {plan}")
        
        success_url = url_for("subscribe_success", plan=plan)
        print(f"[Activate] Success! Redirecting to: {success_url}")
        result = jsonify({"success": True, "redirect": success_url})
        print(f"[Activate] Returning result: {result.get_data(as_text=True)}")
        return result
    except Exception as e:
        print(f"❌ Error activating subscription: {e}")
        import traceback
        traceback.print_exc()
        error_response = jsonify({"error": f"Failed to activate subscription: {str(e)}"})
        print(f"[Activate] Returning error: {error_response.get_data(as_text=True)}")
        return error_response, 500


@app.route("/api/paypal/webhook", methods=["GET", "POST"])
def paypal_webhook():
    """
    Webhook для обработки событий подписки PayPal:
    - BILLING.SUBSCRIPTION.CREATED - подписка создана
    - BILLING.SUBSCRIPTION.ACTIVATED - подписка активирована
    - BILLING.SUBSCRIPTION.CANCELLED - подписка отменена
    - PAYMENT.SALE.COMPLETED - платеж выполнен (автоматическое продление)
    
    GET запрос используется PayPal для проверки доступности webhook URL
    """
    # Handle GET request (PayPal verification)
    if request.method == "GET":
        return jsonify({
            "status": "ok",
            "message": "PayPal webhook endpoint is active",
            "endpoint": "/api/paypal/webhook"
        }), 200
    
    # Handle POST request (actual webhook events)
    try:
        data = request.get_json()
        event_type = data.get("event_type")
        resource = data.get("resource", {})
        
        print(f"[PayPal Webhook] Received event: {event_type}")
        print(f"[PayPal Webhook] Resource: {json.dumps(resource, indent=2)[:500]}")
        
        subscription_id = resource.get("id") or resource.get("billing_agreement_id")
        
        if not subscription_id:
            print("[PayPal Webhook] No subscription ID in resource")
            return jsonify({"status": "ignored"}), 200
        
        db = get_db()
        
        # Find user by subscription_id
        user = db.execute(
            "SELECT * FROM users WHERE paypal_subscription_id = ?",
            (subscription_id,)
        ).fetchone()
        
        if not user:
            print(f"[PayPal Webhook] User not found for subscription {subscription_id}")
            return jsonify({"status": "user_not_found"}), 200
        
        if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
            # Подписка активирована
            plan_id = resource.get("plan_id", "")
            plan = "basic" if "BASIC" in plan_id.upper() else "pro" if "PRO" in plan_id.upper() else "basic"
            
            cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
            if "canceled_at" in cols:
                db.execute("""
                    UPDATE users 
                    SET plan=?, canceled_at=NULL
                    WHERE id=?
                """, (plan, user["id"]))
            else:
                db.execute("""
                    UPDATE users 
                    SET plan=?
                    WHERE id=?
                """, (plan, user["id"]))
            db.commit()
            
            print(f"[PayPal Webhook] Subscription activated for user {user['id']}, plan: {plan}")
            
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            # Подписка отменена
            now_iso = datetime.utcnow().isoformat(timespec="seconds")
            cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
            if "canceled_at" in cols:
                db.execute("""
                    UPDATE users 
                    SET plan='free', canceled_at=?
                    WHERE id=?
                """, (now_iso, user["id"]))
            else:
                db.execute("""
                    UPDATE users 
                    SET plan='free'
                    WHERE id=?
                """, (user["id"],))
            db.commit()
            
            print(f"[PayPal Webhook] Subscription cancelled for user {user['id']}")
            
        elif event_type == "PAYMENT.SALE.COMPLETED":
            # Автоматическое продление - платеж выполнен
            # Подписка остается активной, ничего не нужно делать
            print(f"[PayPal Webhook] Payment completed for subscription {subscription_id}, user {user['id']}")
            
        elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
            # Подписка приостановлена (например, из-за неудачного платежа)
            # Можно оставить план активным или перевести на free
            print(f"[PayPal Webhook] Subscription suspended for user {user['id']}")
            # Оставляем план активным, но можно добавить логику для уведомления пользователя
            
        elif event_type == "BILLING.SUBSCRIPTION.EXPIRED":
            # Подписка истекла
            now_iso = datetime.utcnow().isoformat(timespec="seconds")
            cols = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
            if "canceled_at" in cols:
                db.execute("""
                    UPDATE users 
                    SET plan='free', canceled_at=?
                    WHERE id=?
                """, (now_iso, user["id"]))
            else:
                db.execute("""
                    UPDATE users 
                    SET plan='free'
                    WHERE id=?
                """, (user["id"],))
            db.commit()
            print(f"[PayPal Webhook] Subscription expired for user {user['id']}")
            
        elif event_type == "PAYMENT.SALE.DENIED":
            # Платеж отклонен - подписка может быть приостановлена
            print(f"[PayPal Webhook] Payment denied for subscription {subscription_id}, user {user['id']}")
            # PayPal автоматически приостановит подписку, можно уведомить пользователя
            
        elif event_type == "BILLING.SUBSCRIPTION.CREATED":
            # Подписка создана (для логирования)
            print(f"[PayPal Webhook] Subscription created: {subscription_id}, user {user['id']}")
            
        else:
            # Логируем неизвестные события для отладки
            print(f"[PayPal Webhook] Unhandled event type: {event_type}")
            
        return jsonify({"status": "processed"}), 200
        
    except Exception as e:
        print(f"[PayPal Webhook] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/subscribe/success")
@login_required
def subscribe_success():
    """Payment success page"""
    plan = request.args.get("plan", "basic")
    u = current_user()
    
    base_price = PLAN_PRICES.get(plan, PLAN_PRICES["basic"])["usd"]
    
    flash_t("msg_subscription_active", "success")
    msg = f"נרשמת לחבילת {plan.upper()} במחיר ${base_price}/חודש"
    
    return render_template("subscribe_thanks.html", name="תודה שהצטרפת!", message=msg)


@app.route("/start-trial", methods=["POST"])
@login_required
def start_trial():
    """מפעיל תקופת ניסיון חינמית של 2 ימים - אחר כך מנוי PRO"""
    u = current_user()
    if not u:
        flash_t("msg_login_required", "warning")
        return redirect(url_for("login"))
    
    # בדיקה אם כבר ניצל תקופת ניסיון
    keys = u.keys() if hasattr(u, 'keys') else []
    trial_used = u["trial_used"] if "trial_used" in keys else 0
    if trial_used:
        flash_t("msg_trial_used", "warning")
        return redirect(url_for("profile"))
    
    # בדיקה אם כבר יש מנוי פעיל
    plan = u["plan"] if "plan" in keys else None
    if plan in ("basic", "pro"):
        flash_t("msg_subscription_active", "info")
        return redirect(url_for("profile"))
    
    # מעבר לדף תשלום עם trial
    return redirect(url_for("subscribe", plan="pro", trial="true"))


# --- placeholders so templates with url_for('login'/'signup') won't crash ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    login_id = (request.form.get("email") or "").strip().lower()  # יכול להיות אימייל או שם משתמש
    password = request.form.get("password") or ""
    
    # חיפוש משתמש לפי אימייל או שם משתמש (case-insensitive)
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=? OR LOWER(username)=?", (login_id, login_id.lower())).fetchone()
    
    if not user or not check_password_hash(user["password_hash"], password):
        flash_t("msg_login_failed", "danger")
        return render_template("login.html", email=login_id)
    
    session["uid"] = user["id"]
    return redirect(url_for("profile"))








# =============================================================================
# 📊 DASHBOARD - לוח בקרה עם היסטוריית דוחות והשוואת תקופות
# =============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    """לוח בקרה ראשי עם סיכום וגישה לדוחות שמורים"""
    u = current_user()
    
    # Pro only feature (כולל תקופת ניסיון)
    effective_plan = get_effective_plan(u)
    if effective_plan not in ("pro", "premium", "admin"):
        flash("לוח הבקרה זמין רק למנויי Pro", "warning")
        return redirect(url_for("subscribe", plan="pro"))
    
    # סינון לפי סוג תקופה (מה-URL)
    filter_type = request.args.get("period_type", "")  # month/week/day/custom או ריק לכל
    
    # טעינת דוחות אחרונים (עם סינון אופציונלי)
    reports = get_user_reports(u["id"], limit=50, period_type=filter_type if filter_type else None)
    
    # קיבוץ דוחות לפי סוג תקופה
    reports_by_type = {
        "month": [],
        "week": [],
        "day": [],
        "custom": []
    }
    for r in reports:
        pt = r.get("period_type", "month")
        if pt in reports_by_type:
            reports_by_type[pt].append(r)
        else:
            reports_by_type["custom"].append(r)
    
    # חישוב סטטיסטיקות מצטברות
    total_sales = 0
    latest_summary = {}
    # Use currency from the latest report for total_sales display
    total_sales_currency_code = None
    
    for r in reports:
        try:
            summary = json.loads(r.get("summary_json") or "{}")
            total_sales += summary.get("total_sales", 0)
            if not latest_summary and summary:
                latest_summary = summary
            # Get currency from the first (latest) report
            if not total_sales_currency_code and r.get("currency"):
                total_sales_currency_code = r.get("currency")
        except:
            pass
    
    # השוואת תקופות אם יש לפחות 2 דוחות מאותו סוג
    comparison = None
    comparison_currency = None
    if len(reports) >= 2:
        try:
            # מחפשים שני דוחות מאותו סוג תקופה
            df1 = load_report(reports[1]["id"], u["id"])  # דוח קודם
            df2 = load_report(reports[0]["id"], u["id"])  # דוח אחרון
            if df1 is not None and df2 is not None:
                comparison = compare_periods(df1, df2)
                comparison["report1_name"] = reports[1].get("name", "דוח קודם")
                comparison["report2_name"] = reports[0].get("name", "דוח אחרון")
                # Use currency from the first report (newer one), or fallback to current currency
                comparison_currency_code = reports[0].get("currency") or reports[1].get("currency")
                if comparison_currency_code:
                    comparison_currency = get_currency_by_code(comparison_currency_code)
                else:
                    current_lang = get_language()
                    comparison_currency = get_currency(current_lang)
        except Exception as e:
            print(f"⚠️ שגיאה בהשוואת תקופות: {e}")
    
    # Get current language for currency fallback and labels
    current_lang = get_language()
    
    # Determine currency for total_sales display
    # Use currency from latest report, or fallback to current session currency
    total_sales_currency = None
    if total_sales_currency_code:
        total_sales_currency = get_currency_by_code(total_sales_currency_code)
    else:
        # Fallback to current session currency
        total_sales_currency = get_currency(current_lang)
    
    # Period type labels based on current language
    if current_lang == "he":
        period_type_labels = {
            "month": "חודשים",
            "week": "שבועות",
            "day": "ימים",
            "custom": "מותאם אישית"
        }
    elif current_lang == "en":
        period_type_labels = {
            "month": "Months",
            "week": "Weeks",
            "day": "Days",
            "custom": "Custom"
        }
    else:  # ru
        period_type_labels = {
            "month": "Месяцы",
            "week": "Недели",
            "day": "Дни",
            "custom": "Настраиваемый"
        }
    
    return render_template("dashboard.html",
                          user=u,
                          reports=reports,
                          reports_by_type=reports_by_type,
                          filter_type=filter_type,
                          period_type_labels=period_type_labels,
                          total_sales=total_sales,
                          total_sales_currency_symbol=total_sales_currency["symbol"] if total_sales_currency else get_currency(current_lang)["symbol"],
                          total_reports=len(reports),
                          latest_summary=latest_summary,
                          comparison=comparison,
                          comparison_currency=comparison_currency,
                          active="dashboard",
                          title="לוח בקרה")


@app.route("/dashboard/compare", methods=["POST"])
@login_required
def dashboard_compare():
    """השוואה ידנית בין שני דוחות"""
    u = current_user()
    
    effective_plan = get_effective_plan(u)
    if effective_plan not in ("pro", "premium", "admin"):
        return jsonify({"error": "Pro only"}), 403
    
    report1_id = request.form.get("report1_id", type=int)
    report2_id = request.form.get("report2_id", type=int)
    
    if not report1_id or not report2_id:
        return jsonify({"error": "חסרים פרמטרים"}), 400
    
    try:
        df1 = load_report(report1_id, u["id"])
        df2 = load_report(report2_id, u["id"])
        
        if df1 is None or df2 is None:
            return jsonify({"error": "דוח לא נמצא"}), 404
        
        comparison = compare_periods(df1, df2)
        return jsonify(comparison)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/dashboard/delete/<int:report_id>", methods=["POST"])
@login_required
def dashboard_delete_report(report_id):
    """מחיקת דוח"""
    u = current_user()
    current_lang = get_language()
    
    if delete_report(report_id, u["id"]):
        if current_lang == "he":
            flash("הדוח נמחק בהצלחה", "success")
        elif current_lang == "en":
            flash("Report deleted successfully", "success")
        else:
            flash("Отчет успешно удален", "success")
    else:
        if current_lang == "he":
            flash("שגיאה במחיקת הדוח", "danger")
        elif current_lang == "en":
            flash("Error deleting report", "danger")
        else:
            flash("Ошибка при удалении отчета", "danger")
    
    return redirect(url_for("dashboard"))


@app.route("/profile")
@login_required
def profile():
    u = current_user()
    return render_template("profile.html", user=u, active="profile", title="הפרופיל שלי")

@app.route("/save-onboarding", methods=["POST"])
@login_required
def save_onboarding():
    """Save user's onboarding answers"""
    try:
        data = request.get_json()
        u = current_user()
        
        if not u:
            return jsonify({"error": "Not authenticated"}), 401
        
        db = get_db()
        
        # If user skipped, just mark as completed
        if data.get("skipped"):
            db.execute(
                "UPDATE users SET onboarding_completed = 1 WHERE id = ?",
                (u["id"],)
            )
        else:
            # Save all answers
            db.execute(
                """UPDATE users 
                   SET onboarding_completed = 1, 
                       business_locations = ?, 
                       business_industry = ?, 
                       primary_goal = ?
                   WHERE id = ?""",
                (data.get("locations"), data.get("industry"), data.get("goal"), u["id"])
            )
        
        db.commit()
        return jsonify({"success": True}), 200
    
    except Exception as e:
        print(f"Error saving onboarding: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    u = current_user()
    lang = get_language()
    
    if request.method == "GET":
        return render_template("change_password.html", user=u, active="profile", title=t("change_password_title", lang))
    
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")
    
    # Verify current password
    import hashlib
    if hashlib.sha256(current_password.encode()).hexdigest() != u["password"]:
        flash(t("current_password_incorrect", lang), "danger")
        return render_template("change_password.html", user=u, active="profile", title=t("change_password_title", lang))
    
    # Validate new password
    if new_password != confirm_password:
        flash(t("passwords_dont_match", lang), "danger")
        return render_template("change_password.html", user=u, active="profile", title=t("change_password_title", lang))
    
    is_valid, error_msg = validate_password(new_password, lang)
    if not is_valid:
        flash(error_msg, "danger")
        return render_template("change_password.html", user=u, active="profile", title=t("change_password_title", lang))
    
    # Update password
    hashed = hashlib.sha256(new_password.encode()).hexdigest()
    get_db().execute("UPDATE users SET password=? WHERE id=?", (hashed, u["id"]))
    get_db().commit()
    
    flash(t("password_changed_success", lang), "success")
    return redirect(url_for("profile"))

@app.route("/change_email", methods=["GET", "POST"])
@login_required
def change_email():
    u = current_user()
    lang = get_language()
    
    if request.method == "GET":
        return render_template("change_email.html", user=u, active="profile", title=t("change_email_title", lang))
    
    new_email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    
    # Verify password
    import hashlib
    if hashlib.sha256(password.encode()).hexdigest() != u["password"]:
        flash(t("password_incorrect", lang), "danger")
        return render_template("change_email.html", user=u, active="profile", title=t("change_email_title", lang))
    
    # Validate email
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
        flash(t("invalid_email", lang), "danger")
        return render_template("change_email.html", user=u, active="profile", title=t("change_email_title", lang))
    
    # Check if email already exists
    existing = get_db().execute("SELECT id FROM users WHERE email=? AND id!=?", (new_email, u["id"])).fetchone()
    if existing:
        flash(t("email_already_exists", lang), "danger")
        return render_template("change_email.html", user=u, active="profile", title=t("change_email_title", lang))
    
    # Update email
    get_db().execute("UPDATE users SET email=? WHERE id=?", (new_email, u["id"]))
    get_db().commit()
    
    flash(t("email_changed_success", lang), "success")
    return redirect(url_for("profile"))

@app.route("/saved_reports")
@login_required
def saved_reports():
    u = current_user()
    lang = get_language()
    
    # Get user's saved reports
    db = get_db()
    reports = db.execute("""
        SELECT id, name, period_type, created_at 
        FROM reports 
        WHERE user_id=? 
        ORDER BY created_at DESC
    """, (u["id"],)).fetchall()
    
    return render_template("saved_reports.html", user=u, reports=reports, active="profile", title=t("saved_reports_title", lang))

@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    u = current_user()
    lang = get_language()
    
    if request.method == "GET":
        return render_template("delete_account.html", user=u, active="profile", title=t("delete_account_title", lang))
    
    password = request.form.get("password", "")
    confirm_text = request.form.get("confirm_text", "").strip()
    
    # Verify password
    import hashlib
    if hashlib.sha256(password.encode()).hexdigest() != u["password"]:
        flash(t("password_incorrect", lang), "danger")
        return render_template("delete_account.html", user=u, active="profile", title=t("delete_account_title", lang))
    
    # Verify confirmation text
    expected = "DELETE" if lang == "en" else "УДАЛИТЬ" if lang == "ru" else "מחק"
    if confirm_text.upper() != expected:
        flash(t("confirmation_text_incorrect", lang), "danger")
        return render_template("delete_account.html", user=u, active="profile", title=t("delete_account_title", lang))
    
    # Delete user data
    db = get_db()
    db.execute("DELETE FROM reports WHERE user_id=?", (u["id"],))
    db.execute("DELETE FROM users WHERE id=?", (u["id"],))
    db.commit()
    
    # Logout
    session.clear()
    
    flash(t("account_deleted_success", lang), "success")
    return redirect(url_for("about"))


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    u = current_user()
    if request.method == "GET":
        return render_template("profile_edit.html", user=u, active="profile", title=t("profile_edit_title"))

    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not first_name or not last_name:
        flash_t("msg_fill_name", "danger")
        return render_template("profile_edit.html", user=u)

    # בדיקת שם משתמש (חובה)
    import re
    if not username:
        flash_t("msg_username_required", "danger")
        return render_template("profile_edit.html", user=u)
    if len(username) < 4 or len(username) > 20:
        flash_t("msg_username_length", "danger")
        return render_template("profile_edit.html", user=u)
    if not re.match(r'^[A-Za-z0-9]+$', username):
        flash_t("msg_username_format", "danger")
        return render_template("profile_edit.html", user=u)
    # בדיקה אם שם המשתמש כבר קיים (לא אצל המשתמש הנוכחי)
    existing = get_db().execute("SELECT id FROM users WHERE LOWER(username)=? AND id!=?", (username.lower(), u["id"])).fetchone()
    if existing:
        flash_t("msg_username_taken", "danger")
        return render_template("profile_edit.html", user=u)

    if password:
        if password != confirm:
            flash_t("msg_password_mismatch", "danger")
            return render_template("profile_edit.html", user=u)
        # Password validation
        current_lang = get_language()
        is_valid, error_msg = validate_password(password, current_lang)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("profile_edit.html", user=u)

    # עדכון במסד נתונים
    db = get_db()
    if password:
        db.execute(
            "UPDATE users SET first_name=?, last_name=?, username=?, password_hash=? WHERE id=?",
            (first_name, last_name, username, generate_password_hash(password), u["id"])
        )
    else:
        db.execute(
            "UPDATE users SET first_name=?, last_name=?, username=? WHERE id=?",
            (first_name, last_name, username, u["id"])
        )
    db.commit()

    flash_t("msg_profile_updated", "success")
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    flash_t("msg_logout", "success")
    return redirect(url_for("about"))


from datetime import datetime


@app.route("/signup", methods=["GET", "POST"])
def signup():
    from flask import request, session, render_template, redirect, url_for, flash
    # בGET: שומרים קוד הפניה אם קיים
    if request.method == "GET":
        ref = request.args.get("ref")
        if ref:
            session["pending_ref"] = ref
        return render_template("signup.html")
    
    # POST - הרשמה
    email = (request.form.get("email") or "").strip().lower()
    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    agree_terms = request.form.get("agree_terms")  # נקבל מהצ’קבוקס

    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    confirm_password = request.form.get("confirm_password") or ""
    
    form_data = {"email": email, "username": username, "first_name": first_name, "last_name": last_name}
    
    # בדיקת שם משתמש (חובה)
    import re
    current_lang = get_language()
    if not username:
        if current_lang == 'he':
            flash("שם משתמש הוא שדה חובה", "danger")
        elif current_lang == 'en':
            flash("Username is required", "danger")
        else:
            flash("Имя пользователя обязательно", "danger")
        return render_template("signup.html", **form_data)
    if len(username) < 4 or len(username) > 20:
        if current_lang == 'he':
            flash("שם משתמש חייב להיות בין 4-20 תווים", "danger")
        elif current_lang == 'en':
            flash("Username must be between 4-20 characters", "danger")
        else:
            flash("Имя пользователя должно быть от 4 до 20 символов", "danger")
        return render_template("signup.html", **form_data)
    if not re.match(r'^[A-Za-z0-9]+$', username):
        if current_lang == 'he':
            flash("שם משתמש יכול להכיל רק אותיות אנגליות וספרות", "danger")
        elif current_lang == 'en':
            flash("Username can only contain English letters and numbers", "danger")
        else:
            flash("Имя пользователя может содержать только английские буквы и цифры", "danger")
        return render_template("signup.html", **form_data)
    existing = get_db().execute("SELECT id FROM users WHERE LOWER(username)=?", (username.lower(),)).fetchone()
    if existing:
        if current_lang == 'he':
            flash("שם משתמש זה כבר תפוס", "danger")
        elif current_lang == 'en':
            flash("This username is already taken", "danger")
        else:
            flash("Это имя пользователя уже занято", "danger")
        return render_template("signup.html", **form_data)

    # אם לא סומן – נחזיר הודעת שגיאה
    if not agree_terms:
        current_lang = get_language()
        if current_lang == 'he':
            flash("חובה לאשר את תנאי השימוש ומדיניות הפרטיות כדי להירשם.", "danger")
        elif current_lang == 'en':
            flash("You must agree to the Terms of Use and Privacy Policy to register.", "danger")
        else:
            flash("Вы должны согласиться с Условиями использования и Политикой конфиденциальности для регистрации.", "danger")
        return render_template("signup.html", **form_data)

    # בדיקת התאמת סיסמאות
    if password != confirm_password:
        current_lang = get_language()
        if current_lang == 'he':
            flash("הסיסמאות אינן תואמות", "danger")
        elif current_lang == 'en':
            flash("Passwords do not match", "danger")
        else:
            flash("Пароли не совпадают", "danger")
        return render_template("signup.html", **form_data)

    # Password validation
    current_lang = get_language()
    is_valid, error_msg = validate_password(password, current_lang)
    if not is_valid:
        flash(error_msg, "danger")
        return render_template("signup.html", **form_data)

    # יצירת טוקן אימות
    verification_token = generate_verification_token()

    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO users (email, username, password_hash, first_name, last_name, agreed_terms, agreed_at, email_verified, verification_token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (email, username, generate_password_hash(password), first_name, last_name, 1, datetime.now().isoformat(timespec="seconds"), 0, verification_token)
        )
        db.commit()
    except sqlite3.IntegrityError:
        current_lang = get_language()
        if current_lang == 'he':
            flash("האימייל או שם המשתמש כבר קיימים", "danger")
        elif current_lang == 'en':
            flash("Email or username already exists", "danger")
        else:
            flash("Email или имя пользователя уже существуют", "danger")
        return render_template("signup.html", **form_data)

    # קבלת המשתמש החדש (בלי כניסה אוטומטית - צריך לאמת מייל)
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

    # שליחת מייל אימות
    try:
        send_verification_email(email, verification_token)
    except Exception as e:
        print(f"⚠️ Error sending verification email: {e}")
        import traceback
        traceback.print_exc()
        # Продолжаем даже если email не отправился - пользователь уже создан
    
    # מעבירים לדף בדיקת אימייל
    return redirect(url_for("signup_check_email", email=email))


@app.route("/signup/check-email")
def signup_check_email():
    """דף שמציג הודעה לבדוק את האימייל"""
    email = request.args.get("email", "")
    current_lang = get_language()
    title = "בדוק את האימייל שלך" if current_lang == 'he' else ("Check Your Email" if current_lang == 'en' else "Проверьте вашу почту")
    return render_template("signup_check_email.html", email=email, title=title, current_lang=current_lang)


@app.route("/verify-email/<token>")
def verify_email(token):
    """אימות כתובת אימייל"""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE verification_token=?", (token,)).fetchone()
    
    if not user:
        flash("קישור האימות אינו תקין או שפג תוקפו.", "danger")
        return redirect(url_for("login"))
    
    # עדכון המשתמש כמאומת
    db.execute("""
        UPDATE users 
        SET email_verified = 1, verification_token = NULL 
        WHERE id = ?
    """, (user["id"],))
    db.commit()
    
    # כניסה אוטומטית אחרי אימות
    session["uid"] = user["id"]
    
    # מעבר לדף ברכה
    return redirect(url_for("welcome"))


@app.route("/welcome")
@login_required
def welcome():
    """דף ברכה למשתמשים חדשים"""
    current_lang = get_language()
    return render_template("welcome.html", current_lang=current_lang)


@app.route("/resend-verification", methods=["POST"])
def resend_verification():
    """שליחה חוזרת של מייל אימות"""
    email = request.form.get("email", "").strip().lower()
    
    if not email:
        flash("נא להזין כתובת אימייל.", "danger")
        return redirect(url_for("login"))
    
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    
    if not user:
        flash("אם האימייל קיים במערכת, נשלח קישור אימות חדש.", "info")
        return redirect(url_for("login"))
    
    # בדיקה אם כבר מאומת
    keys = user.keys() if hasattr(user, 'keys') else []
    if "email_verified" in keys and user["email_verified"]:
        flash("האימייל כבר אומת. ניתן להתחבר.", "info")
        return redirect(url_for("login"))
    
    # יצירת טוקן חדש ושליחה
    new_token = generate_verification_token()
    db.execute("UPDATE users SET verification_token=? WHERE id=?", (new_token, user["id"]))
    db.commit()
    
    send_verification_email(email, new_token)
    
    flash("נשלח קישור אימות חדש לאימייל שלך.", "success")
    return redirect(url_for("signup_check_email", email=email))


@app.route("/roi")
def roi_page():
    # Используем те же данные, что и для result/pdf:
    # сначала LAST_EXPORT, потом session["last_export"]
    current_lang = get_language()
    
    # Пробуем получить данные из нескольких источников
    roi = {}
    export_data = {}
    
    # 1. Сначала пробуем LAST_EXPORT (глобальная переменная - самый быстрый)
    saved_report_id = None
    if LAST_EXPORT.get("roi"):
        roi = LAST_EXPORT.get("roi", {})
        export_data = LAST_EXPORT
        saved_report_id = LAST_EXPORT.get("saved_report_id")
        print(f"📊 ROI Page: Loaded from LAST_EXPORT")
    else:
        # 2. Fallback на session (для multi-worker на Render)
        session_data = session.get("last_export", {})
        if session_data:
            roi = session_data.get("roi", {})
            export_data = session_data
            saved_report_id = session_data.get("saved_report_id")
            print(f"📊 ROI Page: Loaded from session")
    
    # Если данных все еще нет, пробуем загрузить из последнего сохраненного отчета
    if not roi or not any([
        bool(roi.get("text")),
        float(roi.get("monthly_gain") or 0) != 0.0,
        float(roi.get("roi_percent") or 0) != 0.0,
    ]):
        # Пробуем загрузить из последнего отчета пользователя
        if session.get("uid"):
            try:
                u = current_user()
                if u:
                    reports = get_user_reports(u["id"], limit=1)
                    if reports:
                        latest_report = reports[0]
                        summary_json = latest_report.get("summary_json")
                        if summary_json:
                            summary = json.loads(summary_json)
                            # Пробуем восстановить ROI из summary
                            if summary.get("roi"):
                                roi = summary.get("roi", {})
                                print(f"📊 ROI Page: Loaded from latest report")
            except Exception as e:
                print(f"⚠️ Error loading ROI from report: {e}")
    
    print(f"📊 ROI Page: roi={bool(roi)}, monthly_gain={roi.get('monthly_gain', 0)}, roi_percent={roi.get('roi_percent', 0)}")
    
    # Проверка наличия данных
    has_any = bool(roi) and any(
        [
            bool(roi.get("text")),
            float(roi.get("monthly_gain") or 0) != 0.0,
            float(roi.get("roi_percent") or 0) != 0.0,
        ]
    )
    
    print(f"📊 ROI Page: has_any={has_any}")
    
    # Если данных нет, пробуем загрузить из последнего отчета перед перенаправлением
    if not has_any:
        # Пробуем загрузить из последнего отчета пользователя
        if session.get("uid"):
            try:
                u = current_user()
                if u:
                    reports = get_user_reports(u["id"], limit=1)
                    if reports:
                        latest_report = reports[0]
                        summary_json = latest_report.get("summary_json")
                        if summary_json:
                            summary = json.loads(summary_json)
                            # Пробуем восстановить ROI из summary
                            if summary.get("roi"):
                                roi = summary.get("roi", {})
                                # Обновляем has_any
                                has_any = bool(roi) and any([
                                    bool(roi.get("text")),
                                    float(roi.get("monthly_gain") or 0) != 0.0,
                                    float(roi.get("roi_percent") or 0) != 0.0,
                                ])
                                if has_any:
                                    print(f"✅ Restored ROI from latest report, has_any={has_any}")
                                    # Обновляем LAST_EXPORT и session для будущих запросов
                                    LAST_EXPORT["roi"] = roi
                                    if session.get("last_export"):
                                        session["last_export"]["roi"] = roi
                                        session.modified = True
            except Exception as e:
                print(f"⚠️ Error loading ROI from report: {e}")
        
        # Если все еще нет данных, перенаправляем на result с сообщением
        if not has_any:
            current_lang = get_language()
            if current_lang == "ru":
                flash("Нет данных ROI для отображения. Пожалуйста, загрузите отчет сначала.", "warning")
            elif current_lang == "en":
                flash("No ROI data available. Please upload a report first.", "warning")
            else:
                flash("אין נתוני ROI להצגה. אנא העלה דוח קודם.", "warning")
            return redirect(url_for("result"))
    
    # Генерируем дополнительные данные для новых блоков
    diagnosis = {}
    action_plan = {}
    
    # Для диагностики нужен dataframe, но его нет в LAST_EXPORT
    # Создаем упрощенную диагностику на основе компонентов
    diagnosis = {"insights": [], "chart_data": {}}  # Упрощенная версия
    
    # Генерируем actionable план на 7 дней
    # Создаем пустой dataframe для совместимости (функция ожидает его)
    import pandas as pd
    empty_df = pd.DataFrame()
    try:
        action_plan = generate_7day_action_plan(empty_df, roi, current_lang)
    except Exception as e:
        print(f"⚠️ Action plan generation error: {e}")
        import traceback
        traceback.print_exc()
        action_plan = {"plans": []}
    
    return render_template(
        "roi.html",
        roi=roi,
        has_any=has_any,
        diagnosis=diagnosis,
        action_plan=action_plan,
        saved_report_id=saved_report_id,
        title="ROI משוער",
        active="roi",
    )


@app.route("/result")
def result():
    # ВАЖНО: Сначала проверяем LAST_EXPORT (работает мгновенно), потом сессию
    # Это решает проблему race condition при первом запросе после редиректа
    
    plots = []
    summary = ""
    summary_ai = ""
    roi = {}
    action_items = []
    
    current_lang = get_language()
    
    # Сначала пробуем LAST_EXPORT (глобальная переменная - работает мгновенно)
    plots_from_export = LAST_EXPORT.get("plots", [])
    saved_report_id = None
    print(f"🔍 /result: Checking LAST_EXPORT - has_data={bool(LAST_EXPORT)}, plots_count={len(plots_from_export)}")
    
    if plots_from_export and len(plots_from_export) > 0:
        # Данные есть в LAST_EXPORT - используем их (самый быстрый способ)
        plots = plots_from_export
        raw_summary = LAST_EXPORT.get("summary", "")
        if isinstance(raw_summary, dict):
            summary = raw_summary.get(current_lang) or raw_summary.get("he") or ""
        else:
            summary = raw_summary
        summary_ai = LAST_EXPORT.get("summary_ai", "")
        roi = LAST_EXPORT.get("roi", {})
        action_items = LAST_EXPORT.get("action_items", [])
        saved_report_id = LAST_EXPORT.get("saved_report_id")
        print(f"✅ Loaded from LAST_EXPORT: {len(plots)} plots, saved_report_id={saved_report_id}")
        if plots:
            print(f"✅ First plot sample: filename={plots[0].get('filename', 'N/A')}, title={plots[0].get('title', 'N/A')}")
    else:
        # Fallback на сессию (для multi-worker на Render)
        session_data = session.get("last_export", {})
        print(f"🔍 Checking session: has_data={bool(session_data)}, keys={list(session_data.keys()) if session_data else []}")
        
        if session_data:
            plots_from_session = session_data.get("plots", [])
            print(f"🔍 Session plots: count={len(plots_from_session)}, type={type(plots_from_session)}")
            if plots_from_session and len(plots_from_session) > 0:
                plots = plots_from_session
                raw_summary = session_data.get("summary", "")
                if isinstance(raw_summary, dict):
                    summary = raw_summary.get(current_lang) or raw_summary.get("he") or ""
                else:
                    summary = raw_summary
                summary_ai = session_data.get("summary_ai", "")
                roi = session_data.get("roi", {})
                action_items = session_data.get("action_items", [])
                saved_report_id = session_data.get("saved_report_id")
                print(f"✅ Loaded from session: {len(plots)} plots, saved_report_id={saved_report_id}")
                if plots:
                    print(f"✅ First plot sample: filename={plots[0].get('filename', 'N/A')}, title={plots[0].get('title', 'N/A')}")
            else:
                print(f"⚠️ Session data exists but plots is empty or invalid: {plots_from_session}")
        else:
            print(f"⚠️ No session data found!")
    
    # Дополнительная проверка: если данные потеряны, пробуем восстановить из последнего отчета
    if (not plots or len(plots) == 0) and session.get("uid"):
        try:
            u = current_user()
            if u:
                reports = get_user_reports(u["id"], limit=1)
                if reports:
                    latest_report = reports[0]
                    saved_report_id = latest_report.get("id")
                    summary_json = latest_report.get("summary_json")
                    if summary_json:
                        summary_data = json.loads(summary_json)
                        # Восстанавливаем графики из сохраненного отчета
                        if summary_data.get("plots"):
                            plots = summary_data.get("plots", [])
                            print(f"✅ Restored {len(plots)} plots from latest report (ID: {saved_report_id})")
                        # Восстанавливаем ROI
                        if summary_data.get("roi"):
                            roi = summary_data.get("roi", {})
                            print(f"✅ Restored ROI from latest report")
                        # Восстанавливаем summary
                        if summary_data.get("total_sales"):
                            summary = f"Total: {summary_data.get('total_sales', 0):,.0f}"
                        print(f"🔄 Attempting to reload from last saved report (ID: {saved_report_id})")
        except Exception as e:
            print(f"⚠️ Error restoring data from report: {e}")
            import traceback
            traceback.print_exc()

    messages = []
    if not plots or len(plots) == 0:
        # Проверяем, есть ли данные в LAST_EXPORT или session, которые мы могли пропустить
        # Это может произойти, если данные еще не успели сохраниться после редиректа
        session_data_check = session.get("last_export", {})
        last_export_plots = LAST_EXPORT.get("plots", [])
        
        # Если есть данные в LAST_EXPORT или session, но plots пустой - это странно, но не перенаправляем
        if last_export_plots or (session_data_check and session_data_check.get("plots")):
            print(f"⚠️ Plots list is empty but data exists! LAST_EXPORT: {len(last_export_plots)} plots, Session: {len(session_data_check.get('plots', [])) if session_data_check else 0} plots")
            # Попробуем использовать данные из LAST_EXPORT или session
            if last_export_plots:
                plots = last_export_plots
                print(f"✅ Restored {len(plots)} plots from LAST_EXPORT")
            elif session_data_check and session_data_check.get("plots"):
                plots = session_data_check.get("plots", [])
                print(f"✅ Restored {len(plots)} plots from session")
        
        # Только если действительно нет данных нигде - пробуем загрузить последний отчет
        # НО только если это не первый запрос после загрузки файла (т.е. если прошло достаточно времени)
        if not plots or len(plots) == 0:
            # Проверяем, не был ли это только что загруженный файл
            # Если LAST_EXPORT или session были недавно обновлены, не перенаправляем
            last_export_time = LAST_EXPORT.get("generated_at")
            session_export_time = session_data_check.get("generated_at") if session_data_check else None
            
            # Если данные были сохранены менее 5 секунд назад, не перенаправляем
            should_redirect = True
            if last_export_time:
                from datetime import datetime, timedelta
                try:
                    if isinstance(last_export_time, datetime):
                        time_diff = datetime.now() - last_export_time
                    else:
                        time_diff = datetime.now() - datetime.fromisoformat(str(last_export_time))
                    if time_diff < timedelta(seconds=5):
                        should_redirect = False
                        print(f"⏱️ Last export was {time_diff.total_seconds():.1f}s ago - too recent, not redirecting")
                except:
                    pass
            
            if should_redirect:
                u = current_user()
                if u:
                    try:
                        db = get_db()
                        last_report = db.execute("""
                            SELECT id, name, period_type, summary_json, created_at
                            FROM reports
                            WHERE user_id = ?
                            ORDER BY created_at DESC
                            LIMIT 1
                        """, (u["id"],)).fetchone()
                        
                        if last_report:
                            print(f"🔄 Attempting to reload from last saved report (ID: {last_report['id']})")
                            # Перенаправляем на страницу дашборда, где пользователь может просмотреть сохраненные отчеты
                            flash_t("results_no_graphs_reload", "info")
                            return redirect(url_for("dashboard"))
                    except Exception as e:
                        print(f"⚠️ Error loading last report: {e}")
            
            messages.append(t("results_no_graphs"))
            print(f"⚠️ No plots found! LAST_EXPORT: {len(LAST_EXPORT.get('plots', []))} plots, Session: {len(session_data_check.get('plots', [])) if session_data_check else 0} plots, Session exists: {bool(session_data_check)}")

    # קבלת תוכנית המשתמש
    u = current_user()
    user_plan = "free"
    if u:
        user_plan = u["plan"] if u["plan"] else "free"
        # בדיקה אם יש trial פעיל
        if u["trial_until"]:
            from datetime import datetime
            try:
                trial_end = datetime.strptime(u["trial_until"], "%Y-%m-%d")
                if trial_end >= datetime.now():
                    user_plan = "pro"  # trial פעיל = גישה לPRO
            except:
                pass

    # Check if this is a guest session
    is_guest_session = session.get("is_guest_session", False)
    
    return render_template(
        "result.html",
        plots=plots,
        summary=summary,
        summary_ai=summary_ai,
        roi=roi,
        action_items=action_items,
        messages=messages,
        user_plan=user_plan,
        saved_report_id=saved_report_id,
        is_guest=is_guest_session,
        title="תוצאות הניתוח",
        active="result",
    )






@app.route("/terms")
def terms():
    return render_template("terms.html", title="תנאי שימוש", active="terms")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html", title="מדיניות פרטיות", active="privacy")

# --- אחידות שעות לקולום אחד: "שעה עגולה" 0-23 ---
HOUR_COL = "שעה עגולה"

def _ensure_hour_col(df, time_col="שעה", out_col=HOUR_COL):
    """
    יוצר/מעדכן עמודת שעה עגולה 0-23 מתוך time_col אם קיימת.
    time_col יכול להיות 8, '8', '08:30', '8:00', '2025-09-01 08:00' וכו'.
    """
    if time_col not in df.columns:
        # אין בכלל עמודת שעה – ניצור עמודת שעה ריקה (NaN) שלא תשבור את הקוד
        df[out_col] = pd.Series(dtype="float")
        return df

    s = df[time_col]

    # נסיון 1: אם זה כבר מספרי (int/float), לקחת כמו שהוא
    hour_num = pd.to_numeric(s, errors="coerce")

    # נסיון 2: לנסות לחלץ שעה ממחרוזת זמן/תאריך-זמן
    # (למקרים של '08:15' או '2025-09-01 14:00')
    as_dt = pd.to_datetime(s, errors="coerce", format=None)
    hour_from_dt = as_dt.dt.hour

    # לאחד – נעדיף את המספרי, ואם NaN נשתמש במה שמחושב מה־datetime
    out = hour_num.fillna(hour_from_dt)

    # אם עדיין NaN – ננסה לחלוץ ספרות מהמחרוזת (למשל "שעה 9")
    still_nan = out.isna()
    if still_nan.any():
        tmp = s.astype(str).str.extract(r'(\d{1,2})', expand=False)
        out = out.fillna(pd.to_numeric(tmp, errors="coerce"))

    # לנקות ולתחום 0..23
    out = out.clip(lower=0, upper=23).round().astype("Int64")

    df[out_col] = out.astype("float").astype("Int64")  # Int64 מאפשר NaN עם int
    return df

    # ליצור/לעדכן "שעה עגולה" לשימוש בכל הגרפים לפי שעה
    df = _ensure_hour_col(df, time_col="שעה", out_col=HOUR_COL)
    print("DEBUG שעות ייחודיות:", df["שעה עגולה"].unique())
    print(df[["שעה", "שעה עגולה"]].head(20))




    # כמה נרשמו דרכי?
    count = db.execute("SELECT referred_count FROM users WHERE id=?", (u["id"],)).fetchone()["referred_count"]
    credit = db.execute("SELECT credit_balance FROM users WHERE id=?", (u["id"],)).fetchone()["credit_balance"]

    ref_link = url_for("signup", ref=db.execute("SELECT ref_code FROM users WHERE id=?", (u["id"],)).fetchone()["ref_code"], _external=True)

    return render_template("referrals.html",
                           ref_link=ref_link,
                           referred_count=count or 0,
                           credit_balance=int(credit or 0))


    # --- קריאת נתונים מהטופס ---
    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm  = request.form.get("confirm_password") or ""

    # --- ולידציה בסיסית ---
    if not first_name or not last_name or not email or not password or not confirm:
        flash("נא למלא את כל השדות", "danger")
        return render_template("signup.html",
                               first_name=first_name, last_name=last_name, email=email)
    if len(password) < 6:
        flash("הסיסמה חייבת להיות באורך 6 תווים לפחות", "danger")
        return render_template("signup.html",
                               first_name=first_name, last_name=last_name, email=email)
    if password != confirm:
        flash("האימות לא תואם את הסיסמה", "danger")
        return render_template("signup.html",
                               first_name=first_name, last_name=last_name, email=email)

    # --- יצירת המשתמש במסד נתונים ---
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?)",
            (email, generate_password_hash(password), first_name, last_name)
        )
        db.commit()
    except sqlite3.IntegrityError:
        flash("האימייל כבר קיים", "danger")
        return render_template("signup.html",
                               first_name=first_name, last_name=last_name, email=email)

    # --- התחברות אוטומטית + דף תודה ---
    user = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    session["uid"] = user["id"]

    # אפשר גם flash, אבל העיקר: רינדור דף התודה
    return render_template("signup_thanks.html", first_name=first_name, email=email)


    # 3) יצירת המשתמש (עם שם פרטי/משפחה)
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?)",
            (email, generate_password_hash(password), first_name, last_name)
        )
        db.commit()
    except sqlite3.IntegrityError:
        flash("האימייל כבר קיים", "danger")
        return render_template("signup.html",
                               first_name=first_name, last_name=last_name, email=email)

    # 4) התחברות אוטומטית והפניה לפרופיל
    user = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    session["uid"] = user["id"]
    flash("נרשמת בהצלחה!", "success")
    return redirect(url_for("profile"))




# -----------------------------------------------------------------------------------

from flask import render_template

@app.errorhandler(404)
def not_found(e):
    lang = session.get("lang", "he")
    if lang == "en":
        msg = "Page not found"
    elif lang == "ru":
        msg = "Страница не найдена"
    else:
        msg = "העמוד לא נמצא"
    return render_template("error.html", code=404, msg=msg), 404

@app.errorhandler(500)
def server_error(e):
    current_lang = get_language()
    msg = t("error_500")
    return render_template("error.html", code=500, msg=msg), 500

@app.route("/_debug/tables")
def debug_tables():
    db = get_db()
    rows = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1"
    ).fetchall()
    return "<pre>" + "\n".join(r["name"] for r in rows) + "</pre>"


@app.route("/robots.txt")
def robots():
    return send_file("static/robots.txt", mimetype="text/plain")


if __name__ == "__main__":
    # יוצרים הקשר אפליקציה רגע לפני ההרצה
    with app.app_context():
        init_db()  # Initialize database with all columns including onboarding
        ensure_tables()  # כאן נוצרת/מתעדכנת הטבלה

    app.run(debug=True)

