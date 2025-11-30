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

# Prices in USD (PayPal works better with USD)
# מחירים מותאמים לעסקים קטנים בישראל
PLAN_PRICES = {
    "basic": {"usd": 9, "ils": 39},
    "pro": {"usd": 19, "ils": 69}
}

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
def validate_password(password: str) -> tuple:
    """
    בדיקת תקינות סיסמה:
    - 8-32 תווים
    - רק אותיות אנגליות וספרות
    - לפחות אות גדולה אחת
    - לפחות ספרה אחת
    מחזיר (תקין, הודעת שגיאה)
    """
    import re
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
            is_valid, error_msg = validate_password(p1)
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
    
    # עמודת הנחת רפרל (50% חד-פעמי)
    if "referral_discount" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN referral_discount INTEGER DEFAULT 0")

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

    # שעה - כל הווריאציות
    "שעה": COL_TIME,
    "time": COL_TIME,
    "זמן": COL_TIME,
    "hour": COL_TIME,
    "שעת עסקה": COL_TIME,
    "שעת מכירה": COL_TIME,
    "transaction time": COL_TIME,

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

    # מחיר ליחידה
    "מחיר": COL_UNIT,
    "מחיר ליחידה": COL_UNIT,
    "מחיר ליחידה (₪)": COL_UNIT,
    "מחיר יחידה": COL_UNIT,
    "price": COL_UNIT,
    "unit price": COL_UNIT,
    "unit_price": COL_UNIT,

    # כמות
    "כמות": COL_QTY,
    "qty": COL_QTY,
    "quantity": COL_QTY,
    "יחידות": COL_QTY,
    "כמות שנמכרה": COL_QTY,
    "units": COL_QTY,

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

    # אמצעי תשלום
    "אמצעי תשלום": COL_PAY,
    "תשלום": COL_PAY,
    "אמצעי_תשלום": COL_PAY,
    "סוג תשלום": COL_PAY,
    "payment": COL_PAY,
    "payment method": COL_PAY,
    "payment_method": COL_PAY,
    "payment type": COL_PAY,
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
    # Email verification columns
    if "email_verified" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0")
    if "verification_token" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN verification_token TEXT NULL")
    # Username column
    if "username" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN username TEXT NULL")

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

def ai_explain(title: str, brief: dict) -> str:
    """
    2–3 משפטים בעברית + המלצה. מנסה כמה מסלולים:
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
        prompt = (
            "אתה יועץ עסקי מומחה לחנויות קמעונאיות ומסעדות בישראל. "
            "תפקידך לעזור לבעל העסק להבין את הנתונים ולקבל החלטות חכמות.\n\n"
            "כללים:\n"
            "• כתוב בעברית פשוטה וברורה, כאילו אתה מדבר עם בעל מכולת או בית קפה\n"
            "• התמקד בתובנה העיקרית אחת — מה הכי חשוב לדעת מהגרף הזה?\n"
            "• תן המלצה מעשית אחת שאפשר ליישם מחר בבוקר (לא תיאוריה!)\n"
            "• אורך: 2-3 משפטים בלבד\n"
            "• אל תחזור על מספרים שכבר מופיעים בגרף — תן פרשנות\n\n"
            "דוגמאות להמלצות טובות:\n"
            "- 'שקול להוסיף עובד בין 12:00-14:00'\n"
            "- 'נסה מבצע על המוצר הזה ביום שלישי'\n"
            "- 'בדוק למה יום ראשון חלש — אולי לפתוח מאוחר יותר?'\n\n"
            f"כותרת הגרף: {title}\n"
            f"נתונים: {payload}"
        )

        # ---- נסיון A1: Chat Completions עם max_completion_tokens ----
        try:
            print(f"📤 Chat.Completions call → {OPENAI_MODEL} | {title} | A1")
            r = _openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
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
                messages=[{"role": "user", "content": prompt}]
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

def estimate_roi(df, params: ROIParams = ROIParams()) -> Dict[str, Any]:
    """
    מחשב ROI משוער מהדוח:
    - העלאת יום חלש לרמת הימים הרגילים
    - ניצול שעות ערב חלשות
    - קידום מוצרים חלשים (זנב)
    מחזיר פירוט סכומים חודשיים + ROI%.
    """
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
    out["monthly_gain"] = total_gain
    out["roi_percent"] = (total_gain / max(1e-9, params.service_cost)) * 100.0

    # טקסט מוכן (ימין-לשמאל תוסיף עם rtl/rtl_pdf אצלך)
    parts = []
    if "weak_day" in out["components"]:
        c = out["components"]["weak_day"]
        parts.append(
            f"יום חלש (‘{c['day']}’) יעלה לרמת הימים הרגילים: +{c['monthly_gain']:,.0f} ₪/חודש."
        )
    if "evening_hours" in out["components"]:
        c = out["components"]["evening_hours"]
        parts.append(
            f"שעות ערב חלשות → יעד חדש: +{c['uplift_per_day']:,.0f} ₪ ליום × {int(c['days_in_month_factor']):d} ימים ≈ +{c['monthly_gain']:,.0f} ₪/חודש."
        )
    if "tail_products" in out["components"]:
        c = out["components"]["tail_products"]
        parts.append(
            f"קידום ‘זנב מוצרים’ (≈{int(params.tail_share_cutoff*100)}% מההכנסות) ב+{int(params.tail_boost_ratio*100)}% → +{c['monthly_gain']:,.0f} ₪/חודש."
        )

    summary_text = (
        f"פוטנציאל שיפור חודשי (בתנאי שפועלים על התובנות): ~{total_gain:,.0f} ₪. "
        f"עלות השירות: {params.service_cost:,.0f} ₪. "
        f"ROI תיאורטי: {out['roi_percent']:,.0f}%."
    )
    disclaimer = "⚠️ הערכה זו מבוססת על ניתוח הנתונים בלבד. התוצאות בפועל תלויות בפעולות שתנקטו."
    out["text"] = " • ".join(parts + [summary_text, disclaimer])
    return out


def generate_action_items(df, roi_data: dict) -> list:
    """
    יוצר רשימת פעולות קונקרטיות ומעשיות על בסיס ניתוח הנתונים.
    מחזיר רשימה של dicts: [{priority, category, action, impact, how_to}]
    """
    actions = []
    comps = roi_data.get("components", {})
    
    # 1. יום חלש - המלצה ספציפית
    if "weak_day" in comps:
        weak = comps["weak_day"]
        day_name = weak.get("day", "")
        current = weak.get("current", 0)
        target = weak.get("target", 0)
        gap_pct = int((1 - current / max(1, target)) * 100) if target > 0 else 0
        
        # המלצות ספציפיות לפי היום
        day_actions = {
            "ראשון": "הפעל מבצע 'פתיחת שבוע' - קפה + מאפה במחיר מיוחד",
            "שני": "יום Happy Hour מוקדם (11:00-14:00) - הנחה 15% על ארוחות",
            "שלישי": "יום נאמנות - כפל נקודות למועדון",
            "רביעי": "מבצע 'באמצע השבוע' - מנה שנייה ב-50%",
            "חמישי": "הכנה לסופ\"ש - מבצע משפחות",
            "שישי": "מבצע בוקר מוקדם (עד 10:00) - הנחה 20%",
            "שבת": "ארוחת שבת משפחתית - מנה ילדים חינם",
        }
        
        actions.append({
            "priority": 1,
            "category": "📅 יום חלש",
            "title": f"חזק את יום {day_name}",
            "action": day_actions.get(day_name, f"הפעל מבצע מיוחד ביום {day_name}"),
            "impact": f"פוטנציאל: עד +₪{weak.get('monthly_gain', 0):,.0f}/חודש",
            "how_to": [
                f"הפער מהימים הרגילים: ~{gap_pct}%",
                "פרסם בסושיאל יום לפני",
                "הדגש בשילוט בחנות",
                "שלח SMS/וואטסאפ ללקוחות נאמנים"
            ]
        })
    
    # 2. שעות ערב חלשות
    if "evening_hours" in comps:
        eve = comps["evening_hours"]
        midday = eve.get("midday_sum", 0)
        evening = eve.get("evening_sum", 0)
        
        if midday > 0 and evening < midday * 0.4:  # ערב חלש משמעותית
            actions.append({
                "priority": 2,
                "category": "🌙 שעות ערב",
                "title": "הגבר פעילות בערב (17:00-20:00)",
                "action": "הפעל Happy Hour או מבצע ערב",
                "impact": f"פוטנציאל: עד +₪{eve.get('monthly_gain', 0):,.0f}/חודש",
                "how_to": [
                    "Happy Hour 17:00-19:00 - הנחה 20% על משקאות",
                    "מבצע 'After Work' לעובדי משרדים",
                    "תאורה ומוזיקה מתאימים לערב",
                    "תפריט ערב מיוחד (טאפאס, שיתוף)"
                ]
            })
    
    # 3. מוצרים חלשים (זנב)
    if "tail_products" in comps:
        tail = comps["tail_products"]
        actions.append({
            "priority": 3,
            "category": "📦 מוצרים",
            "title": "הגבר מכירות מוצרים חלשים",
            "action": "צור חבילות או מבצעי קומבו",
            "impact": f"פוטנציאל: עד +₪{tail.get('monthly_gain', 0):,.0f}/חודש",
            "how_to": [
                "צור קומבו: מוצר חזק + מוצר חלש",
                "הצע כ'תוספת' במחיר מיוחד",
                "מקם בגובה העיניים / ליד הקופה",
                "הכשר צוות להציע אקטיבית"
            ]
        })
    
    # 4. המלצות כלליות תמיד
    # בדוק אם יש נתוני מוצרים
    if COL_ITEM in df.columns:
        top_product = df.groupby(COL_ITEM)[COL_SUM].sum().idxmax() if not df.empty else None
        if top_product:
            actions.append({
                "priority": 4,
                "category": "⭐ מוצר מוביל",
                "title": f"נצל את ההצלחה של '{top_product}'",
                "action": "הרחב את קו המוצרים המוביל",
                "impact": "שמור על הביקוש + הגדל סל קנייה",
                "how_to": [
                    f"צור וריאציות של '{top_product}'",
                    "הצע גרסה פרימיום במחיר גבוה יותר",
                    "צור חבילה עם מוצרים משלימים",
                    "ודא שתמיד במלאי!"
                ]
            })
    
    # 5. טיפ להגדלת עסקה ממוצעת
    if COL_SUM in df.columns:
        avg_transaction = df[COL_SUM].mean() if not df.empty else 0
        if avg_transaction > 0:
            target_increase = avg_transaction * 0.15  # יעד: +15%
            actions.append({
                "priority": 5,
                "category": "💰 הגדלת סל",
                "title": f"הגדל עסקה ממוצעת ב-15%",
                "action": f"יעד: מ-₪{avg_transaction:.0f} ל-₪{avg_transaction + target_increase:.0f}",
                "impact": f"פוטנציאל: +₪{target_increase * 30:.0f}/חודש (30 עסקאות/יום)",
                "how_to": [
                    "הצע תוספות: 'רוצה להוסיף X?'",
                    "Upsell: 'במעט יותר תקבל גרסה גדולה'",
                    "מבצע 'קנה ב-X קבל Y חינם'",
                    "הכשר צוות למכירה אקטיבית"
                ]
            })
    
    return sorted(actions, key=lambda x: x["priority"])


    # Fallback – טקסט גנרי נוח
    return f"{title}: לפי הנתונים, הביצועים מרוכזים סביב הערכים הבולטים בתקציר. " \
           f"בדקו שעות/ימים חזקים לניצול, וחזקו מוצרים מובילים. נסו גם חבילות/מבצעים לשעות חלשות."

# ====== שמירת מצב אחרון לייצוא PDF (MVP) ======
LAST_EXPORT = {
    "generated_at": None,    # datetime
    "plots": [],             # [{filename,title,note,ai}]
    "summary": ""            # טקסט קצר
}

# -----------------------------------------------------------------------------------
def _clean_plots_dir():
    if os.path.exists(PLOTS_DIR):
        for f in os.listdir(PLOTS_DIR):
            try:
                os.remove(os.path.join(PLOTS_DIR, f))
            except:
                pass

def _save_fig(fig, filename):
    path = os.path.join(PLOTS_DIR, filename)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
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
        """ניסיון לקרוא עם קידודים שונים לעברית"""
        encodings = ['utf-8-sig', 'utf-8', 'windows-1255', 'iso-8859-8', 'cp1255', 'latin-1']
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
        # מסיר סוגריים וסימני מטבע
        s = re.sub(r'[₪$€\(\)\[\]]', '', s)
        # מסיר רווחים כפולים
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    # בונה מפה מנורמלת
    normalized_map = {}
    for key, val in COLUMN_MAP.items():
        normalized_map[_normalize_col_name(key)] = val

    renamed = {}
    for col in df.columns:
        # ניסיון 1: התאמה מדויקת
        if col in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col]
            continue
        # ניסיון 2: התאמה מנורמלת
        norm = _normalize_col_name(col)
        if norm in normalized_map:
            renamed[col] = normalized_map[norm]
            continue
        # ניסיון 3: חיפוש חלקי (אם שם העמודה מכיל מילת מפתח)
        for key, val in COLUMN_MAP.items():
            if key in col or col in key:
                renamed[col] = val
                break

    df.rename(columns=renamed, inplace=True)

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

    # -------------------------------------------------------
    # 3.5) חישוב עמודת סכום אם חסרה אבל יש מחיר וכמות
    # -------------------------------------------------------
    if COL_SUM not in df.columns:
        # אם יש מחיר ליחידה וכמות - נחשב סכום
        if COL_UNIT in df.columns and COL_QTY in df.columns:
            price = pd.to_numeric(df[COL_UNIT], errors="coerce").fillna(0)
            qty = pd.to_numeric(df[COL_QTY], errors="coerce").fillna(0)
            df[COL_SUM] = (price * qty).round(2)
        # אם יש רק מחיר (בלי כמות נפרדת) - נשתמש בו כסכום
        elif COL_UNIT in df.columns:
            df[COL_SUM] = pd.to_numeric(df[COL_UNIT], errors="coerce").fillna(0)

    # -------------------------------------------------------
    # 4) וידוא עמודות חובה
    # -------------------------------------------------------
    needed = [COL_DATE, COL_TIME, COL_SUM]
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

    df[COL_SUM] = pd.to_numeric(df[COL_SUM], errors="coerce").fillna(0)

    # חישוב מחיר ליחידה אם חסר ויש כמות
    if COL_UNIT not in df.columns and COL_QTY in df.columns and (df[COL_QTY] > 0).any():
        df[COL_UNIT] = (df[COL_SUM] / df[COL_QTY].replace(0, pd.NA)).round(2)

    # -------------------------------------------------------
    # 7) המרות תאריך + "שעה עגולה"
    # -------------------------------------------------------
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce").dt.date

    # קבוע לשם העמודה אצלך (אם כבר מוגדר, נשתמש בו; אחרת ניצור)
    hour_col_name = globals().get("HOUR_COL", "שעה עגולה")

    # ---- פונקציה משופרת לחישוב 'שעה עגולה' ----
    def _ensure_hour_col(_df, time_col, out_col):
        # ננסה להמיר לזמן ואז להוציא שעה
        h_from_dt = pd.to_datetime(_df[time_col].astype(str), errors="coerce").dt.hour
        # fallback: אם השדה הוא מספרי (7, 12, ...)
        h_from_num = pd.to_numeric(_df[time_col], errors="coerce")
        hours = h_from_dt.fillna(h_from_num)
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

def save_report(user_id: int, df: pd.DataFrame, name: str = None, period_type: str = "month") -> int:
    """
    שומר דוח מוצפן לבסיס הנתונים.
    מחזיר את ה-ID של הדוח.
    
    period_type: month/week/day/custom
    """
    db = get_db()
    
    # זיהוי תקופה אוטומטי
    period_start = None
    period_end = None
    if COL_DATE in df.columns:
        dates = pd.to_datetime(df[COL_DATE], errors='coerce').dropna()
        if len(dates) > 0:
            period_start = dates.min().strftime('%Y-%m-%d')
            period_end = dates.max().strftime('%Y-%m-%d')
    
    # שמות לפי סוג תקופה
    period_type_names = {
        "month": "חודש",
        "week": "שבוע", 
        "day": "יום",
        "custom": "תקופה"
    }
    type_label = period_type_names.get(period_type, "תקופה")
    
    # שם אוטומטי אם לא סופק
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
            name = f"דוח {datetime.now().strftime('%Y-%m-%d')}"
    
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
    
    cursor = db.execute("""
        INSERT INTO reports (user_id, name, period_type, period_start, period_end, encrypted_data, summary_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, period_type, period_start, period_end, encrypted, json.dumps(summary, ensure_ascii=False)))
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
            SELECT id, name, period_type, period_start, period_end, summary_json, created_at
            FROM reports
            WHERE user_id = ? AND period_type = ?
            ORDER BY period_start DESC, created_at DESC
            LIMIT ?
        """, (user_id, period_type, limit)).fetchall()
    else:
        rows = db.execute("""
            SELECT id, name, period_type, period_start, period_end, summary_json, created_at
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
    משווה בין שתי תקופות ומחזיר תובנות.
    """
    def calc_metrics(df):
        return {
            "total": float(pd.to_numeric(df[COL_SUM], errors='coerce').fillna(0).sum()) if COL_SUM in df.columns else 0,
            "days": df[COL_DATE].nunique() if COL_DATE in df.columns else 0,
            "avg_daily": 0,
            "transactions": len(df),
        }
    
    m1 = calc_metrics(df1)
    m2 = calc_metrics(df2)
    
    m1["avg_daily"] = m1["total"] / m1["days"] if m1["days"] > 0 else 0
    m2["avg_daily"] = m2["total"] / m2["days"] if m2["days"] > 0 else 0
    
    # חישוב שינויים באחוזים
    def pct_change(old, new):
        if old == 0:
            return 100 if new > 0 else 0
        return round((new - old) / old * 100, 1)
    
    return {
        "period1": m1,
        "period2": m2,
        "changes": {
            "total_pct": pct_change(m1["total"], m2["total"]),
            "avg_daily_pct": pct_change(m1["avg_daily"], m2["avg_daily"]),
            "transactions_pct": pct_change(m1["transactions"], m2["transactions"]),
        },
        "insight": _generate_comparison_insight(m1, m2)
    }


def _generate_comparison_insight(m1: dict, m2: dict) -> str:
    """יצירת תובנה טקסטואלית להשוואה"""
    total_change = m2["total"] - m1["total"]
    pct = ((m2["total"] - m1["total"]) / m1["total"] * 100) if m1["total"] > 0 else 0
    
    if pct > 10:
        return f"📈 עלייה משמעותית של {pct:.0f}% במכירות! המשך כך."
    elif pct > 0:
        return f"📊 עלייה קלה של {pct:.0f}% במכירות. יש מקום לשיפור."
    elif pct > -10:
        return f"📉 ירידה קלה של {abs(pct):.0f}% במכירות. כדאי לבדוק מה השתנה."
    else:
        return f"⚠️ ירידה משמעותית של {abs(pct):.0f}% במכירות! דורש תשומת לב."


    # הוספת עמודות חדשות אם חסרות (SQLite סובלנית פה)
    try:
        db.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
    except Exception:
        pass
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
    if not row["ref_code"]:
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
            flash("יש להתחבר קודם", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrap


# -----------------------------------------------------------------------------------

from datetime import datetime
from flask import redirect, url_for, flash

@app.post("/cancel-subscription")
def cancel_subscription():
    user = current_user()
    if not user:
        # אם אין התחברות — שולחים להתחברות אם יש, אחרת לדף הבית
        return redirect(url_for("login") if "login" in app.view_functions else url_for("index"))

    now_iso = datetime.utcnow().isoformat(timespec="seconds")

    db = get_db()
    db.execute("""
        UPDATE users
        SET plan = ?, subscription_status = ?, canceled_at = ?, active_until = ?
        WHERE id = ?
    """, ("free", "canceled", now_iso, now_iso, user["id"]))
    db.commit()

    # אם אין לך flash, לא חיוני
    try:
        flash("המנוי בוטל. עברתם למסלול חינמי.", "success")
    except Exception:
        pass

    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    messages, plots = [], []

    def _render():
        return render_template("index.html",
                               messages=messages, plots=plots,
                               active="home", title="ניתוח דוח")

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
    except Exception as e:
        messages.append(f"שגיאה בשמירת הקובץ: {e}")
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
        messages.append(f"שגיאה בקריאת הקובץ: {e}")
        return _render()

    # ------------------------------------------------------------------
    # 1️⃣ מכירות לפי שעה — הכי חשוב: מתי צריך עובדים
    # ------------------------------------------------------------------
    if opt_hourly:
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
            ax.set_title(rtl(f"מכירות לפי שעה (₪) {hour_start}:00–{hour_end}:00"))
            ax.set_xlabel(rtl("שעה"))
            ax.set_ylabel(rtl('סה"כ (₪)'))
            ax.set_xticks(list(range(hour_start, hour_end + 1)))
            ax.set_xlim(hour_start - 0.5, hour_end + 0.5)
            fname = _save_fig(fig, "hourly.png")

            # --- AI ---
            brief = {
                "range": [hour_start, hour_end],
                "best_hour": (int(hourly.loc[hourly[COL_SUM].idxmax()][HOUR_COL]) if not hourly.empty else None),
                "best_hour_sum": float(hourly[COL_SUM].max()) if not hourly.empty else 0.0,
                "avg_hour": float(hourly[COL_SUM].mean()) if not hourly.empty else 0.0,
            }
            ai = ai_explain("מכירות לפי שעה", brief)

            plots.append({
                "filename": fname,
                "title": "מכירות לפי שעה",
                "note": "סכום המכירות לכל שעה בטווח שנבחר",
                "ai": ai,               # ← הוספת השדה
            })
        except Exception as e:
            messages.append(f"שגיאה: מכירות לפי שעה — {e}")

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
                names = [ _rtl(str(x)) for x in by_wd["יום בשבוע"].tolist() ]
                xpos  = list(range(len(names)))
                values = by_wd[COL_SUM].tolist()

                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(xpos, values)
                ax.set_title(rtl("מכירות לפי יום בשבוע (₪)"))
                ax.set_xlabel(rtl("יום בשבוע"))
                ax.set_ylabel(rtl('סה"כ (₪)'))
                ax.set_xticks(xpos)
                ax.set_xticklabels(names, rotation=0)
                fname = _save_fig(fig, "by_weekday.png")

                # --- AI ---
                top_row = by_wd.sort_values(COL_SUM, ascending=False).iloc[0] if not by_wd.empty else None
                brief = {
                    "best_day": (str(top_row["יום בשבוע"]) if top_row is not None else None),
                    "best_day_sum": float(top_row[COL_SUM]) if top_row is not None else 0.0,
                    "avg_day": float(by_wd[COL_SUM].mean()) if not by_wd.empty else 0.0,
                    "dist": {str(k): float(v) for k, v in zip(by_wd["יום בשבוע"], by_wd[COL_SUM])}
                }
                ai = ai_explain("מכירות לפי יום בשבוע", brief)

                plots.append({"filename": fname, "title": "מכירות לפי יום בשבוע",
                              "note": "איזה ימים חזקים/חלשים",
                              "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: מכירות לפי יום בשבוע — {e}")

    # ------------------------------------------------------------------
    # 4️⃣ מכירות יומיות — מגמות ואנומליות
    # ------------------------------------------------------------------
    if opt_daily:
        try:
            daily = df.groupby(COL_DATE)[COL_SUM].sum().reset_index()
            fig = plt.figure(figsize=(10, 4))
            plt.bar(daily[COL_DATE].astype(str), daily[COL_SUM])
            plt.title(rtl("מכירות יומיות"))
            plt.xlabel(rtl("תאריך"))
            plt.ylabel(rtl("סה\"כ (₪)"))
            plt.xticks(rotation=60)
            fname = _save_fig(fig, "daily.png")

            # --- AI ---
            top = daily.sort_values(COL_SUM, ascending=False).iloc[0] if not daily.empty else None
            brief = {
                "best_date": (str(top[COL_DATE]) if top is not None else None),
                "best_sum": float(top[COL_SUM]) if top is not None else 0.0,
                "avg_daily": float(daily[COL_SUM].mean()) if not daily.empty else 0.0,
            }
            ai = ai_explain("מכירות יומיות", brief)

            plots.append({"filename": fname, "title": "מכירות יומיות",
                          "note": "תנודות יום־יומיות",
                          "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: מכירות יומיות — {e}")

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
                        ax.set_title(_rtl("Top 10 — כמות לפי מוצר"))
                        ax.set_ylabel(_rtl("כמות"))
                        ax.set_xticks(xpos)
                        ax.set_xticklabels(names, rotation=40, ha="right")
                        fname = _save_fig(fig, "top_qty.png")

                        # --- AI ---
                        brief = {
                            "top_item": str(qty.iloc[0][COL_ITEM]),
                            "top_value": int(qty.iloc[0][COL_QTY]),
                        }
                        ai = ai_explain("מוצרים – כמות", brief)

                        plots.append({"filename": fname, "title": "Top 10 כמות",
                                      "note": "המוצרים הנמכרים בכמות הגבוהה ביותר",
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
                    ax.set_title(_rtl("Top 10 — הכנסות לפי מוצר"))
                    ax.set_ylabel(_rtl('סה"כ (₪)'))
                    ax.set_xticks(xpos_r)
                    ax.set_xticklabels(names_r, rotation=40, ha="right")
                    fname = _save_fig(fig, "top_rev.png")

                    # --- AI ---
                    brief = {
                        "top_item": str(revenue.iloc[0][COL_ITEM]),
                        "top_value": float(revenue.iloc[0][COL_SUM]),
                    }
                    ai = ai_explain("מוצרים – הכנסות", brief)

                    plots.append({"filename": fname, "title": "Top 10 הכנסות",
                                  "note": "המוצרים שמכניסים הכי הרבה כסף",
                                  "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: מוצרים – כמות/הכנסות — {e}")

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
                    labels = [ _rtl(str(x)) for x in pay[pay_col].tolist() ]
                    values = pay[COL_SUM].tolist()

                    fig, ax = plt.subplots(figsize=(6, 6))
                    ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
                    ax.set_title(_rtl("פילוח אמצעי תשלום (₪)"))

                    fname = _save_fig(fig, "payments.png")

                    # AI
                    total = float(pay[COL_SUM].sum()) or 1.0
                    top3 = (pay.sort_values(COL_SUM, ascending=False).head(3)
                                .assign(share=lambda d: (d[COL_SUM] / total).round(3))
                                [[pay_col, "share"]].to_dict(orient="records"))

                    brief = {"top_methods": top3}
                    ai = ai_explain("פילוח אמצעי תשלום", brief)

                    plots.append({
                        "filename": fname,
                        "title": "אמצעי תשלום",
                        "note": "התפלגות לפי אמצעי תשלום",
                        "ai": ai
                    })
                else:
                    messages.append("אין נתונים לגרף 'פילוח אמצעי תשלום'.")
            except Exception as e:
                messages.append(f"שגיאה: פילוח אמצעי תשלום — {e}")

        else:
            messages.append("לא נמצאה עמודה המתאימה לאמצעי תשלום — דילגנו על הפילוח.")

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
                    ax.set_title(rtl(f"ממוצע קנייה לפי שעה (₪) {hour_start}:00–{hour_end}:00"))
                    ax.set_xlabel(rtl("שעה"))
                    ax.set_ylabel(rtl("ממוצע צ'ק (₪)"))
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
                    ai = ai_explain("ממוצע קנייה לפי שעה", brief)
                    
                    plots.append({
                        "filename": fname,
                        "title": "ממוצע קנייה לפי שעה",
                        "note": "באיזו שעה מגיעים לקוחות עם קניות גדולות יותר",
                        "ai": ai
                    })
            else:
                messages.append("דילגנו על 'ממוצע קנייה' — חסרה עמודת שעה או מספר עסקה.")
        except Exception as e:
            messages.append(f"שגיאה: ממוצע קנייה לפי שעה — {e}")

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
                    
                    # הגדרת labels
                    ax.set_xticks(range(len(heatmap_data.columns)))
                    ax.set_xticklabels([f'{int(h)}:00' for h in heatmap_data.columns])
                    ax.set_yticks(range(len(heatmap_data.index)))
                    ax.set_yticklabels([rtl(d) for d in heatmap_data.index])
                    
                    ax.set_title(rtl("מפת חום: מכירות לפי שעה ויום"))
                    ax.set_xlabel(rtl("שעה"))
                    ax.set_ylabel(rtl("יום בשבוע"))
                    
                    # Colorbar
                    cbar = plt.colorbar(im, ax=ax)
                    cbar.set_label(rtl('סה"כ מכירות (₪)'))
                    
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
                    ai = ai_explain("מפת חום מכירות", brief)
                    
                    plots.append({
                        "filename": fname,
                        "title": "מפת חום מכירות",
                        "note": "איפה הכסף מרוכז – שעות ×  ימים",
                        "ai": ai
                    })
            else:
                messages.append("דילגנו על 'מפת חום' — חסרה עמודת שעה או יום בשבוע.")
        except Exception as e:
            messages.append(f"שגיאה: מפת חום — {e}")

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
                    
                    labels = [rtl('ימי חול'), rtl('סופ"ש (שישי-שבת)')]
                    colors = ['#3498db', '#9b59b6']
                    
                    # גרף 1: סה"כ מכירות
                    weekday_total = compare[compare['is_weekend'] == False]['total'].values[0]
                    weekend_total = compare[compare['is_weekend'] == True]['total'].values[0]
                    ax1.bar(labels, [weekday_total, weekend_total], color=colors)
                    ax1.set_title(rtl('סה"כ מכירות'))
                    ax1.set_ylabel(rtl('₪'))
                    for i, v in enumerate([weekday_total, weekend_total]):
                        ax1.text(i, v + v*0.02, f'₪{v:,.0f}', ha='center', fontsize=10)
                    
                    # גרף 2: ממוצע ליום
                    weekday_avg = compare[compare['is_weekend'] == False]['avg'].values[0]
                    weekend_avg = compare[compare['is_weekend'] == True]['avg'].values[0]
                    ax2.bar(labels, [weekday_avg, weekend_avg], color=colors)
                    ax2.set_title(rtl('ממוצע עסקה'))
                    ax2.set_ylabel(rtl('₪'))
                    for i, v in enumerate([weekday_avg, weekend_avg]):
                        ax2.text(i, v + v*0.02, f'₪{v:,.0f}', ha='center', fontsize=10)
                    
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
                    ai = ai_explain("השוואת סופ״ש לימי חול", brief)
                    
                    plots.append({
                        "filename": fname,
                        "title": "סופ\"ש מול ימי חול",
                        "note": "האם סופ\"ש חזק יותר או חלש יותר",
                        "ai": ai
                    })
            else:
                messages.append("דילגנו על 'סופ\"ש מול ימי חול' — חסרה עמודת יום בשבוע.")
        except Exception as e:
            messages.append(f"שגיאה: סופ\"ש מול ימי חול — {e}")


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
        
        # בניית הסיכום
        summary_lines = [
            f"📊 סה\"כ מכירות: ₪{total_sum:,.0f}",
            f"📅 ימים בדוח: {days} | ממוצע יומי: ₪{avg_day:,.0f}",
            f"🧾 עסקאות: {transaction_count:,} | ממוצע לעסקה: ₪{avg_transaction:,.0f}",
        ]
        
        if best_day and worst_day and days > 1:
            summary_lines.append(f"🏆 היום הכי טוב: ₪{best_day_sales:,.0f} | היום הכי חלש: ₪{worst_day_sales:,.0f}")
        
        summary_txt = "\n".join(summary_lines)
    except Exception as e:
        print(f"Summary error: {e}")
        summary_txt = ""

    # טקסט AI כללי
    try:
        summary_ai_txt = ai_explain("סיכום כללי לעסק",
                                    {"total": total_sum, "days": days, "avg_day": avg_day})
    except Exception:
        summary_ai_txt = ""


    # --- ROI אישי לחודש (על בסיס הדוח) ---
    try:
        roi_data = estimate_roi(df, ROIParams(
            service_cost=149.0,          # תעדכן לפי התמחור שלך
            month_days_assumption=30.0,  # אם הדוח פחות מחודש – נשליך לחודש
            evening_hours=(17, 20),      # אפשר לשנות
            midday_hours=(11, 14),
            evening_target_ratio=0.5,
            weak_day_target="median",    # או "mean"
            tail_boost_ratio=0.10,
            tail_share_cutoff=0.50
        ))
    except Exception:
        roi_data = {"text": "", "monthly_gain": 0.0, "roi_percent": 0.0, "components": {}}

    # --- ROI אישי לחודש (על בסיס הדוח) ---
    try:
        roi_data = estimate_roi(df, ROIParams(
            service_cost=149.0,
            month_days_assumption=30.0,
            evening_hours=(17, 20),
            midday_hours=(11, 14),
            evening_target_ratio=0.5,
            weak_day_target="median",
            tail_boost_ratio=0.10,
            tail_share_cutoff=0.50
        ))
    except Exception:
        roi_data = {"text": "", "monthly_gain": 0.0, "roi_percent": 0.0, "components": {}}

    # ---------- שמירה למבנה ה"ישן" גם את ה-ROI (חשוב!) ----------
    LAST_EXPORT["generated_at"] = _dt.now()
    LAST_EXPORT["plots"] = plots
    LAST_EXPORT["summary"] = summary_txt
    LAST_EXPORT["summary_ai"] = summary_ai_txt
    LAST_EXPORT["roi"] = roi_data   # ← הוסף שורה זו



    # נשמור גם במבנה הישן (למי שקורא ממנו), אבל מקור האמת יהיה בסשן:
    LAST_EXPORT["generated_at"] = _dt.now()
    LAST_EXPORT["plots"] = plots
    LAST_EXPORT["summary"] = summary_txt
    LAST_EXPORT["summary_ai"] = summary_ai_txt

    # --- SNAPSHOT יחיד: בדיוק מה שמוצג באתר ---
    snap = {
        "generated_at": _dt.now().strftime("%Y-%m-%d %H:%M"),
        "summary": summary_txt,
        "summary_ai": summary_ai_txt,
        "roi": roi_data,   # ← חדש
        "plots": [
            {
                "filename": p.get("filename", ""),
                "title": p.get("title", ""),
                # זה הטקסט שמופיע באתר – ללא שינוי/נרמול:
                "ai": p.get("ai", "")
            }
            for p in plots
        ],
    }
    # --- Reduce session size (prevent >4KB cookie crash) ---
    snap["summary_ai"] = snap.get("summary_ai", "")[:400]  # טקסט קצר
    for p in snap["plots"]:
        p["ai"] = (p.get("ai") or "")[:400]  # חותך טקסטים ארוכים
        session.modified = True

    print(f"✅ נוצרו {len(plots)} גרפים, מפנים ל-/result")
    # שומרים הכל ב-LAST_EXPORT בלבד ולא בקוקי
    LAST_EXPORT["generated_at"] = _dt.now()
    LAST_EXPORT["plots"] = plots
    LAST_EXPORT["summary"] = summary_txt
    LAST_EXPORT["summary_ai"] = summary_ai_txt
    LAST_EXPORT["roi"] = roi_data
    
    # --- 📋 יצירת רשימת פעולות מומלצות ---
    try:
        action_items = generate_action_items(df, roi_data)
    except Exception as e:
        print(f"⚠️ Failed to generate action items: {e}")
        action_items = []
    LAST_EXPORT["action_items"] = action_items

    # --- 🔐 שמירה אוטומטית של הדוח למשתמשי Pro ---
    try:
        u = current_user()
        effective_plan = get_effective_plan(u) if u else "free"
        if u and effective_plan in ("pro", "premium", "admin"):
            report_id = save_report(
                user_id=u["id"], 
                df=df, 
                name=period_name if period_name else None,
                period_type=period_type
            )
            print(f"💾 דוח נשמר בהצלחה (ID: {report_id}, סוג: {period_type})")
            LAST_EXPORT["saved_report_id"] = report_id
        else:
            print(f"ℹ️ דוח לא נשמר - תוכנית: {effective_plan}")
    except Exception as e:
        print(f"⚠️ שגיאה בשמירת דוח: {e}")

    return redirect(url_for("result"))


@app.route("/demo")
def demo_analysis():
    """
    מציג ניתוח לדוגמה עם נתוני דמו קיימים.
    מאפשר למשתמשים לראות את התוצאות בלי להעלות קובץ משלהם.
    """
    import pandas as pd
    
    print("➡ Demo analysis requested")
    
    # טעינת קובץ הדמו
    demo_file = os.path.join(app.static_folder, "demo", "sample_sales.csv")
    if not os.path.exists(demo_file):
        flash("קובץ הדמו לא נמצא", "danger")
        return redirect(url_for("index"))
    
    try:
        df = pd.read_csv(demo_file, encoding="utf-8")
    except Exception as e:
        flash(f"שגיאה בטעינת קובץ הדמו: {e}", "danger")
        return redirect(url_for("index"))
    
    # נרמול עמודות
    df.columns = [c.strip() for c in df.columns]
    df = _normalize_columns(df)
    
    if df.empty:
        flash("קובץ הדמו ריק", "warning")
        return redirect(url_for("index"))
    
    # ניקוי גרפים קודמים
    _clean_plots_dir()
    
    messages, plots = [], []
    
    # קביעת פרמטרים לדמו
    hour_start, hour_end = 6, 22
    
    # --- יצירת גרפים ---
    # 1) מכירות לפי שעה
    try:
        hourly, max_hour = _plot_hourly(df, hour_start, hour_end)
        fname = _save_fig(hourly, "hourly.png")
        ai_text = ""
        if ai_enabled_for_user():
            ai_text = ai_explain("מכירות לפי שעה", {"שעת שיא": max_hour})
        plots.append({
            "filename": fname, 
            "title": "מכירות לפי שעה",
            "note": f"🕐 שעת השיא: {max_hour}",
            "ai": ai_text
        })
    except Exception as e:
        print(f"⚠️ Demo hourly error: {e}")
    
    # 2) מכירות לפי יום בשבוע
    try:
        weekday_fig, top_day = _plot_weekday(df)
        fname = _save_fig(weekday_fig, "by_weekday.png")
        ai_text = ""
        if ai_enabled_for_user():
            ai_text = ai_explain("מכירות לפי יום", {"יום שיא": top_day})
        plots.append({
            "filename": fname,
            "title": "מכירות לפי יום בשבוע",
            "note": f"📅 יום השיא: {top_day}",
            "ai": ai_text
        })
    except Exception as e:
        print(f"⚠️ Demo weekday error: {e}")
    
    # 3) Top 10 מוצרים
    try:
        fig_qty, fig_rev, top_item = _plot_top_products(df)
        fname_qty = _save_fig(fig_qty, "top_qty.png")
        fname_rev = _save_fig(fig_rev, "top_rev.png")
        plots.append({"filename": fname_qty, "title": "Top 10 מוצרים (כמות)", "note": f"⭐ הכי נמכר: {top_item}"})
        plots.append({"filename": fname_rev, "title": "Top 10 מוצרים (הכנסות)", "note": ""})
    except Exception as e:
        print(f"⚠️ Demo products error: {e}")
    
    # 4) מפת חום
    try:
        hm_fig = _plot_heatmap(df)
        fname = _save_fig(hm_fig, "heatmap.png")
        plots.append({"filename": fname, "title": "מפת חום (שעה × יום)", "note": "🔥 צבע חם = מכירות גבוהות"})
    except Exception as e:
        print(f"⚠️ Demo heatmap error: {e}")
    
    # --- ROI ---
    try:
        roi_data = estimate_roi(df, ROIParams(
            service_cost=149.0,
            month_days_assumption=30,
            tail_share_cutoff=0.50
        ))
    except Exception:
        roi_data = {"text": "", "monthly_gain": 0.0, "roi_percent": 0.0, "components": {}}
    
    # --- Action Items ---
    try:
        action_items = generate_action_items(df, roi_data)
    except Exception as e:
        print(f"⚠️ Demo action items error: {e}")
        action_items = []
    
    # --- סיכום ---
    total_sales = float(df[COL_SUM].sum()) if COL_SUM in df.columns else 0.0
    summary_txt = f"📊 דוגמה לניתוח | סה\"כ מכירות: ₪{total_sales:,.0f} | {len(plots)} גרפים נוצרו"
    
    # שמירה ב-LAST_EXPORT
    LAST_EXPORT["generated_at"] = datetime.now()
    LAST_EXPORT["plots"] = plots
    LAST_EXPORT["summary"] = summary_txt
    LAST_EXPORT["summary_ai"] = "זהו ניתוח לדוגמה. העלה דוח משלך לקבלת תובנות מותאמות!"
    LAST_EXPORT["roi"] = roi_data
    LAST_EXPORT["action_items"] = action_items
    
    print(f"✅ Demo: נוצרו {len(plots)} גרפים")
    
    return redirect(url_for("result"))


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
            plt.title("מכירות יומיות (₪)")
            plt.xlabel("תאריך"); plt.ylabel("סה\"כ (₪)")
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
                plt.title("Top 10 — כמות לפי מוצר")
                plt.xticks(rotation=40, ha="right"); plt.ylabel("כמות")
                fname = _save_fig(fig, "top_qty.png")
                plots.append({"filename": fname, "title": "Top 10 כמות", "note": "המוצרים הנמכרים בכמות הגבוהה ביותר"})
            revenue = df.groupby("מוצר")["סכום (₪)"].sum().sort_values(ascending=False).head(10).reset_index()
            fig = plt.figure(figsize=(9,4))
            plt.bar(revenue["מוצר"], revenue["סכום (₪)"])
            plt.title("Top 10 — הכנסות לפי מוצר")
            plt.xticks(rotation=40, ha="right"); plt.ylabel("סה\"כ (₪)")
            fname = _save_fig(fig, "top_rev.png")
            plots.append({"filename": fname, "title": "Top 10 הכנסות", "note": "המוצרים שמכניסים הכי הרבה כסף"})
        except Exception as e:
            messages.append(f"שגיאה: מוצרים – כמות/רווח — {e}")

    # 6) פילוח אמצעי תשלום
    if opt_payments:
        if "אמצעי תשלום" in df.columns:
            try:
                pay = df.groupby("אמצעי תשלום")["סכום (₪)"].sum().reset_index()
                fig = plt.figure(figsize=(6,6))
                plt.pie(pay["סכום (₪)"], labels=pay["אמצעי תשלום"], autopct="%1.0f%%", startangle=90)
                plt.title("פילוח אמצעי תשלום (₪)")
                fname = _save_fig(fig, "payments.png")
                plots.append({"filename": fname, "title": "אמצעי תשלום", "note": "התפלגות לפי אמצעי תשלום"})
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
            plt.title(f"מכירות לפי שעה (₪) {hour_start}:00–{hour_end}:00")
            plt.xlabel("שעה"); plt.ylabel('סה"כ (₪)')
            fname = _save_fig(fig, "hourly.png")

            brief = {
                "best_hour": int(hourly.loc[hourly[COL_SUM].idxmax()]["שעה עגולה"]) if not hourly.empty else None,
                "best_hour_sum": float(hourly[COL_SUM].max()) if not hourly.empty else 0.0,
                "avg_hour": float(hourly[COL_SUM].mean()) if not hourly.empty else 0.0,
                "range": [hour_start, hour_end],
            }
            ai = ai_explain("מכירות לפי שעה", brief)
            plots.append({"filename": fname, "title": "מכירות לפי שעה", "note": "סכום המכירות לכל שעה בטווח שנבחר", "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: מכירות לפי שעה — {e}")

    # 2) לפי יום בשבוע
    if opt_weekday:
        try:
            order = ["ראשון","שני","שלישי","רביעי","חמישי","שישי","שבת"]
            by_wd = df.groupby("יום בשבוע")[COL_SUM].sum().reindex(order).reset_index()
            fig = plt.figure(figsize=(8,4))
            plt.bar(by_wd["יום בשבוע"], by_wd[COL_SUM])
            plt.title("מכירות לפי יום בשבוע (₪)")
            plt.xlabel("יום"); plt.ylabel('סה"כ (₪)')
            fname = _save_fig(fig, "by_weekday.png")

            top = by_wd.sort_values(COL_SUM, ascending=False).iloc[0] if not by_wd.empty else None
            brief = {
                "best_day": (top["יום בשבוע"] if top is not None else None),
                "best_day_sum": float(top[COL_SUM]) if top is not None else 0.0,
                "avg_day": float(by_wd[COL_SUM].mean()) if not by_wd.empty else 0.0,
            }
            ai = ai_explain("מכירות לפי יום בשבוע", brief)
            plots.append({"filename": fname, "title": "מכירות לפי יום בשבוע", "note": "איזה ימים חזקים/חלשים", "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: מכירות לפי יום בשבוע — {e}")

    # 3) יומי
    if opt_daily:
        try:
            daily = df.groupby(COL_DATE)[COL_SUM].sum().reset_index()
            fig = plt.figure(figsize=(10,4))
            plt.bar(daily[COL_DATE].astype(str), daily[COL_SUM])
            plt.title("מכירות יומיות (₪)")
            plt.xlabel("תאריך"); plt.ylabel('סה"כ (₪)')
            plt.xticks(rotation=60)
            fname = _save_fig(fig, "daily.png")

            top = daily.sort_values(COL_SUM, ascending=False).iloc[0] if not daily.empty else None
            brief = {
                "best_date": (str(top[COL_DATE]) if top is not None else None),
                "best_sum": float(top[COL_SUM]) if top is not None else 0.0,
                "avg_daily": float(daily[COL_SUM].mean()) if not daily.empty else 0.0,
            }
            ai = ai_explain("מכירות יומיות", brief)
            plots.append({"filename": fname, "title": "מכירות יומיות", "note": "תנודות יום־יומיות", "ai": ai})
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
                plt.title("Top 10 — כמות לפי מוצר")
                plt.xticks(rotation=40, ha="right"); plt.ylabel("כמות")
                fname1 = _save_fig(fig, "top_qty.png")
                brief1 = {
                    "top_item": (None if qty.empty else str(qty.iloc[0][COL_ITEM])),
                    "top_value": (0 if qty.empty else int(qty.iloc[0][COL_QTY])),
                }
                ai1 = ai_explain("מוצרים – כמות", brief1)
                plots.append({"filename": fname1, "title": "Top 10 כמות", "note": "המוצרים הנמכרים בכמות הגבוהה ביותר", "ai": ai1})
            else:
                messages.append("אין עמודת 'כמות' — דילגנו על Top 10 לפי כמות.")

            # הכנסות
            revenue = df.groupby(COL_ITEM)[COL_SUM].sum().sort_values(ascending=False).head(10).reset_index()
            fig = plt.figure(figsize=(9,4))
            plt.bar(revenue[COL_ITEM], revenue[COL_SUM])
            plt.title("Top 10 — הכנסות לפי מוצר")
            plt.xticks(rotation=40, ha="right"); plt.ylabel('סה"כ (₪)')
            fname2 = _save_fig(fig, "top_rev.png")
            brief2 = {
                "top_item": (None if revenue.empty else str(revenue.iloc[0][COL_ITEM])),
                "top_value": (0.0 if revenue.empty else float(revenue.iloc[0][COL_SUM])),
            }
            ai2 = ai_explain("מוצרים – הכנסות", brief2)
            plots.append({"filename": fname2, "title": "Top 10 הכנסות", "note": "המוצרים שמכניסים הכי הרבה כסף", "ai": ai2})
        except Exception as e:
            messages.append(f"שגיאה: מוצרים – כמות/רווח — {e}")

    # 6) אמצעי תשלום
    if opt_payments and COL_PAY in df.columns:
        try:
            pay = df.groupby(COL_PAY)[COL_SUM].sum().reset_index()
            fig = plt.figure(figsize=(6,6))
            plt.pie(pay[COL_SUM], labels=pay[COL_PAY], autopct="%1.0f%%", startangle=90)
            plt.title("פילוח אמצעי תשלום (₪)")
            fname = _save_fig(fig, "payments.png")

            total = float(pay[COL_SUM].sum()) or 1.0
            top3 = (pay.sort_values(COL_SUM, ascending=False).head(3)
                        .assign(share=lambda d: (d[COL_SUM] / total).round(3))
                        [[COL_PAY, "share"]].to_dict(orient="records"))
            brief = {"top_methods": top3}
            ai = ai_explain("פילוח אמצעי תשלום", brief)
            plots.append({"filename": fname, "title": "אמצעי תשלום", "note": "התפלגות לפי אמצעי תשלום", "ai": ai})
        except Exception as e:
            messages.append(f"שגיאה: פילוח אמצעי תשלום — {e}")
    elif opt_payments and COL_PAY not in df.columns:
        messages.append("לא נמצאה עמודה 'אמצעי תשלום' — דילגנו על הפילוח.")

    if not plots:
        messages.append("לא הופקו גרפים—בדוק שהעמודות בדוח תואמות (תאריך, שעה, סכום (₪) לפחות).")

    # שמירת מצב אחרון לייצוא PDF
    LAST_EXPORT["generated_at"] = datetime.now()
    LAST_EXPORT["plots"] = plots
    # סיכום קצר
    total_sum = float(df[COL_SUM].sum())
    days = df[COL_DATE].nunique()
    avg_day = total_sum / days if days else 0.0
# ---------------- ייצוא PDF ----------------
# ---------------- ייצוא PDF ----------------
# ---------------- ייצוא PDF ----------------
@app.route("/export/pdf")
def export_pdf():
    """
    יצוא PDF בעזרת דפדפן headless (Chrome/Edge) עם RTL תקין.
    כולל בלוק ROI מעוצב בדף הראשון + עמוד ROI מסכם (אם קיים ROI).
    """
    import os, io, tempfile, shutil, subprocess, textwrap
    from datetime import datetime as _dt

    # ---------- 1) שליפת snapshot ----------
    # תמיד לקחת מ-LAST_EXPORT (הכי עדכני)
    u = current_user()
    plan = get_effective_plan(u) if u else "free"
    
    # DEBUG
    print(f"📄 PDF Export: plan={plan}, LAST_EXPORT plots count={len(LAST_EXPORT.get('plots', []))}")
    
    if plan not in ("pro", "premium", "admin"):
        return render_template("upgrade_required.html", 
                               feature="הורדת PDF עם המלצות",
                               title="שדרוג נדרש"), 403
    
    # תמיד משתמשים ב-LAST_EXPORT (לא בסשן)
    snap = {
        "generated_at": (LAST_EXPORT.get("generated_at").strftime("%Y-%m-%d %H:%M")
                         if LAST_EXPORT.get("generated_at") else ""),
        "summary": LAST_EXPORT.get("summary", ""),
        "summary_ai": LAST_EXPORT.get("summary_ai", ""),
        "roi": LAST_EXPORT.get("roi", {}),
        "plots": LAST_EXPORT.get("plots", []),
    }
    
    print(f"📄 PDF Snap: {len(snap.get('plots', []))} plots, ROI={bool(snap.get('roi'))}")

    # ---------- 2) עזרים ----------
    def _esc(s: str) -> str:
        return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def _file_url(p):
        p = os.path.abspath(p)
        return "file:///" + p.replace("\\", "/")

    def _img_url(fname):
        if not fname:
            return ""
        path = os.path.join(PLOTS_DIR, fname)
        return _file_url(path) if os.path.exists(path) else ""

    def _font_face_block():
        fonts_dir = os.path.join(STATIC_DIR, "fonts")
        noto = os.path.join(fonts_dir, "NotoSansHebrew-Regular.ttf")
        if os.path.exists(noto):
            return textwrap.dedent(f"""
            @font-face {{
              font-family: 'NotoSansHebrew';
              src: url('{_file_url(noto)}') format('truetype');
              font-weight: normal;
              font-style: normal;
            }}
            body {{ font-family: 'NotoSansHebrew', Arial, 'Segoe UI', sans-serif; }}
            """)
        return "body { font-family: Arial, 'Segoe UI', sans-serif; }"

    def _find_browser():
        for p in [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]:
            if os.path.exists(p):
                return p
        return None

    browser = _find_browser()
    if not browser:
        return "לא נמצא Chrome/Edge במחשב. התקן Chrome/Edge ואז נסה שוב.", 500

    # ---------- 3) ROI – הכנה בטוחה למשתנים ----------
    roi          = snap.get("roi") or {}
    comps        = roi.get("components") or {}
    c_weak       = comps.get("weak_day") or {}
    c_evening    = comps.get("evening_hours") or {}
    c_tail       = comps.get("tail_products") or {}

    roi_text     = _esc(roi.get("text") or "")
    roi_gain     = float(roi.get("monthly_gain") or 0.0)
    roi_pct      = float(roi.get("roi_percent") or 0.0)
    weak_gain    = float(c_weak.get("monthly_gain") or 0.0)
    evening_note = _esc(str(c_evening.get("note") or "ניצול שעות ערב"))
    evening_gain = float(c_evening.get("monthly_gain") or 0.0)
    tail_gain    = float(c_tail.get("monthly_gain") or 0.0)
    has_roi      = bool(roi_text or roi_gain or roi_pct)

    # בונה את שורות הטבלה כ־HTML פשוט (רק מה שקיים)
    roi_rows = ""
    if weak_gain:
        roi_rows += f"<tr><td>יום חלש ↗︎</td><td>העלאה לרמת ימים רגילים</td><td>₪{weak_gain:,.0f}</td></tr>"
    if evening_gain:
        roi_rows += f"<tr><td>שעות ערב ↗︎</td><td>{evening_note}</td><td>₪{evening_gain:,.0f}</td></tr>"
    if tail_gain:
        roi_rows += f"<tr><td>זנב מוצרים ↗︎</td><td>קידום תחתית סל המוצרים</td><td>₪{tail_gain:,.0f}</td></tr>"

    roi_table_html = (
        f"<div class='roi-table-wrap'>"
        f"<table class='roi-table'>"
        f"<thead><tr><th>רכיב</th><th>פירוט</th><th>תרומה חודשית</th></tr></thead>"
        f"<tbody>{roi_rows}</tbody></table></div>"
    ) if roi_rows else ""

    # כרטיס ROI לדף הראשון
    roi_inline_html = ""
    if has_roi:
        roi_inline_html = (
            "<section class='roi-card' dir='rtl'>"
            "<div class='roi-header'>הערכת ROI (חודשי)</div>"
            + (f"<div class='roi-text'>{roi_text}</div>" if roi_text else "")
            + f"""
            <div class="roi-badges">
              <div class="badge badge-green">
                <div class="badge-label">תוספת חודשית מוערכת</div>
                <div class="badge-value">₪{roi_gain:,.0f}</div>
              </div>
              <div class="badge badge-blue">
                <div class="badge-label">ROI משוער</div>
                <div class="badge-value">{roi_pct:,.0f}%</div>
              </div>
            </div>
            """
            + roi_table_html +
            "</section>"
        )

    # ---------- 4) HTML מלא ----------
    html = textwrap.dedent(f"""
    <!doctype html>
    <html lang="he" dir="rtl">
    <head>
      <meta charset="utf-8">
      <title>דו״ח ניתוח מכירות</title>
      <style>
        {_font_face_block()}
        html, body {{
          direction: rtl;
          text-align: right;
          margin: 0; padding: 0;
          background: #ffffff;
        }}
        .page {{
          width: 210mm; min-height: 297mm;
          padding: 16mm;
          box-sizing: border-box;
        }}
        h1 {{ margin: 0 0 8mm 0; font-size: 22pt; }}
        h2 {{ margin: 10mm 0 4mm 0; font-size: 14pt; }}
        p  {{ margin: 2mm 0; font-size: 11pt; line-height: 1.6; white-space: pre-wrap; }}
        .meta {{ color:#555; margin-top: -6mm; margin-bottom: 6mm; }}
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
          padding: 6mm;
          min-width: 55mm;
          box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06);
        }}
        .badge-green {{ background:#eafff4; border:1px solid #2e8b57; }}
        .badge-blue  {{ background:#eef5ff; border:1px solid #3a71d1; }}
        .badge-label {{
          font-size: 9pt; color:#555; margin-bottom: 2mm;
        }}
        .badge-value {{
          font-size: 20pt; font-weight: 800; letter-spacing: 0.5px;
        }}

        /* ===== ROI Table ===== */
        .roi-table-wrap {{ margin-top: 6mm; }}
        .roi-table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 10pt;
        }}
        .roi-table th, .roi-table td {{
          border: 1px solid #ddd;
          padding: 3mm 4mm;
          vertical-align: top;
        }}
        .roi-table thead th {{
          background:#f7f7f7; font-weight:700;
        }}
      </style>
    </head>
    <body>
      <div class="page">
        <h1>דו״ח ניתוח מכירות</h1>
        {"<div class='meta'>תאריך הפקה: " + _esc(snap.get("generated_at","")) + "</div>" if snap.get("generated_at") else ""}

        {"<p>" + _esc(snap.get("summary","")) + "</p>" if snap.get("summary") else ""}

        {"<p>" + _esc(snap.get("summary_ai","")) + "</p>" if snap.get("summary_ai") else ""}

        {roi_inline_html}

        <div class="hr"></div>

        {"".join(
            [
              (
                f"<div class='plot'>"
                f"{('<h2>' + _esc(p.get('title','')) + '</h2>') if p.get('title') else ''}"
                f"{('<img src='+repr(_img_url(p.get('filename'))) + ' alt=\"plot\"/>') if _img_url(p.get('filename')) else ''}"
                f"{('<p>' + _esc(p.get('ai','')) + '</p>') if p.get('ai') else ''}"
                f"</div>"
              )
              for p in (snap.get('plots') or [])
            ]
        )}
      </div>
    </body>
    </html>
    """)

    # ---------- 5) הדפסה באמצעות הדפדפן ----------
    tmpdir = tempfile.mkdtemp(prefix="pdf_export_")
    try:
        html_path = os.path.join(tmpdir, "report.html")
        pdf_path  = os.path.join(tmpdir, "report.pdf")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

            cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--allow-file-access-from-files",
            "--disable-web-security",
            "--allow-file-access",
            f"--print-to-pdf={pdf_path}",
            html_path,
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
            return "נכשלה הפקת ה-PDF באמצעות הדפדפן.", 500

        with open(pdf_path, "rb") as f:
            data = io.BytesIO(f.read())

        fname = f"report_{_dt.now().strftime('%Y%m%d_%H%M')}.pdf"
        data.seek(0)
        return send_file(data, as_attachment=True, download_name=fname, mimetype="application/pdf")
    except subprocess.CalledProcessError as e:
        return f"שגיאה בהרצת הדפדפן להדפסת PDF: {e}", 500
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass

















# ---------------- דפים סטטיים: אודות / צור קשר / תודה ----------------
@app.route("/about")
def about():
    return render_template("about.html", active="about", title="אודות")

@app.route("/pricing")
def pricing():
    """Pricing page with plan comparison"""
    u = current_user()
    current_plan = get_effective_plan(u) if u else 'free'
    trial_active = is_trial_active(u) if u else False
    return render_template("pricing.html", 
                         active="pricing", 
                         title="תוכניות ומחירים",
                         current_plan=current_plan,
                         trial_active=trial_active,
                         prices=PLAN_PRICES)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("contact.html", active="contact", title="צור קשר")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "general").strip()
    message = request.form.get("message", "").strip()
    
    # שליחת מייל
    try:
        send_contact_email(name, email, message, subject)
        flash("ההודעה נשלחה בהצלחה! נחזור אליך בהקדם. 📧", "success")
    except Exception as e:
        print(f"⚠️ שגיאה בשליחת מייל: {e}")
        # עדיין שומרים את ההודעה לlog
        flash("ההודעה התקבלה! נחזור אליך בהקדם.", "success")
    
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
    return None


@app.route("/subscribe")
@login_required
def subscribe():
    """Show checkout page with PayPal button"""
    plan = request.args.get("plan", "basic")
    if plan not in ("basic", "pro"):
        plan = "basic"

    u = current_user()
    ensure_user_ref_code(u["id"])

    # Calculate price with referral discount (50% off, one time)
    base_price_ils = PLAN_PRICES[plan]["ils"]
    base_price_usd = PLAN_PRICES[plan]["usd"]
    
    # Check for referral discount (50% off next month)
    referral_discount = int(u["referral_discount"] or 0) if "referral_discount" in u.keys() else 0
    
    if referral_discount > 0:
        # 50% discount on current plan
        discount_percent = min(referral_discount, 50)
        discount_usd = int(base_price_usd * discount_percent / 100)
        discount_ils = int(base_price_ils * discount_percent / 100)
    else:
        discount_usd = 0
        discount_ils = 0
    
    net_price_usd = base_price_usd - discount_usd
    net_price_ils = base_price_ils - discount_ils

    return render_template("checkout.html",
        plan=plan,
        base_price_ils=base_price_ils,
        base_price_usd=base_price_usd,
        referral_discount=referral_discount,
        discount_usd=discount_usd,
        discount_ils=discount_ils,
        net_price_usd=net_price_usd,
        net_price_ils=net_price_ils,
        paypal_client_id=PAYPAL_CLIENT_ID,
        paypal_mode=PAYPAL_MODE
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
        
        # Calculate price with referral discount
        base_price_usd = PLAN_PRICES[plan]["usd"]
        referral_discount = int(u["referral_discount"] or 0) if "referral_discount" in u.keys() else 0
        
        if referral_discount > 0:
            discount_percent = min(referral_discount, 50)
            discount_usd = int(base_price_usd * discount_percent / 100)
        else:
            discount_usd = 0
        
        net_price_usd = base_price_usd - discount_usd
        
        # If price is 0 (fully covered by discount), activate immediately
        if net_price_usd <= 0:
            return activate_subscription(u["id"], plan, referral_discount)
        
        access_token = get_paypal_access_token()
        if not access_token:
            print("[PayPal] Failed to get access token")
            return jsonify({"error": "PayPal not configured"}), 500
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Format price with 2 decimal places (PayPal requirement)
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": f"{net_price_usd:.2f}"
                },
                "description": f"OnePoweb {plan.upper()} Plan"
            }]
        }
        
        print(f"[PayPal] Creating order: {order_data}")
        
        response = requests.post(
            f"{PAYPAL_API_URL}/v2/checkout/orders",
            headers=headers,
            json=order_data
        )
        
        print(f"[PayPal] Response status: {response.status_code}")
        print(f"[PayPal] Response body: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            order = response.json()
            # Store order info in session for verification
            session["pending_order"] = {
                "order_id": order["id"],
                "plan": plan,
                "amount_usd": net_price_usd,
                "credit_used": credit_usd * 4
            }
            return jsonify({"id": order["id"]})
        else:
            print(f"[PayPal] Error: {response.text}")
            return jsonify({"error": f"PayPal error: {response.status_code}"}), 500
            
    except Exception as e:
        print(f"[PayPal] Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/paypal/capture-order", methods=["POST"])
@login_required
def paypal_capture_order():
    """Capture PayPal payment and activate subscription"""
    data = request.get_json()
    order_id = data.get("orderID")
    
    pending = session.get("pending_order", {})
    if pending.get("order_id") != order_id:
        return jsonify({"error": "Order mismatch"}), 400
    
    access_token = get_paypal_access_token()
    if not access_token:
        return jsonify({"error": "PayPal not configured"}), 500
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{PAYPAL_API_URL}/v2/checkout/orders/{order_id}/capture",
        headers=headers
    )
    
    if response.status_code in [200, 201]:
        capture_data = response.json()
        if capture_data.get("status") == "COMPLETED":
            u = current_user()
            plan = pending.get("plan", "basic")
            credit_used = pending.get("credit_used", 0)
            
            # Clear pending order
            session.pop("pending_order", None)
            
            # Activate subscription
            return activate_subscription(u["id"], plan, credit_used)
    
    return jsonify({"error": "Payment not completed"}), 400


def activate_subscription(user_id, plan, discount_used):
    """Activate subscription after successful payment"""
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    
    # Update user plan and reset referral discount (one-time use)
    db.execute("""
        UPDATE users 
        SET plan=?, referral_discount=0, cancelled_at=NULL 
        WHERE id=?
    """, (plan, user_id))
    db.commit()
    
    # Grant referral bonus to referrer (one-time 50% discount on next month)
    referrer_id = u["referred_by"]
    already_granted = int(u["ref_bonus_granted"] or 0)
    if referrer_id and not already_granted and int(referrer_id) != int(user_id):
        try:
            # Give referrer 50% discount on next payment (one time only)
            db.execute("UPDATE users SET referral_discount=50 WHERE id=? AND (referral_discount IS NULL OR referral_discount=0)", (referrer_id,))
            db.execute("UPDATE users SET ref_bonus_granted=1 WHERE id=?", (user_id,))
            db.commit()
        except Exception:
            pass
    
    return jsonify({"success": True, "redirect": url_for("subscribe_success", plan=plan)})


@app.route("/subscribe/success")
@login_required
def subscribe_success():
    """Payment success page"""
    plan = request.args.get("plan", "basic")
    u = current_user()
    
    base_price = PLAN_PRICES.get(plan, PLAN_PRICES["basic"])["ils"]
    
    flash("המנוי הופעל בהצלחה!", "success")
    msg = f"נרשמת לחבילת {plan.upper()} במחיר ₪{base_price}/חודש"
    
    return render_template("subscribe_thanks.html", name="תודה שהצטרפת!", message=msg)


@app.route("/start-trial", methods=["POST"])
@login_required
def start_trial():
    """מפעיל תקופת ניסיון חינמית של 7 ימים"""
    u = current_user()
    if not u:
        flash("יש להתחבר תחילה", "warning")
        return redirect(url_for("login"))
    
    # בדיקה אם כבר ניצל תקופת ניסיון
    if u["trial_used"]:
        flash("כבר ניצלת את תקופת הניסיון החינמית.", "warning")
        return redirect(url_for("profile"))
    
    # בדיקה אם כבר יש מנוי פעיל
    if u["plan"] in ("basic", "pro"):
        flash("כבר יש לך מנוי פעיל!", "info")
        return redirect(url_for("profile"))
    
    # הפעלת תקופת ניסיון
    trial_end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    db = get_db()
    db.execute("""
        UPDATE users 
        SET trial_until = ?, trial_used = 1
        WHERE id = ?
    """, (trial_end, u["id"]))
    db.commit()
    
    flash(f"🎉 תקופת הניסיון הופעלה! PRO חינם עד {trial_end}", "success")
    return redirect(url_for("profile"))


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
        flash("אימייל/שם משתמש או סיסמה שגויים", "danger")
        return render_template("login.html", email=login_id)
    
    session["uid"] = user["id"]
    return redirect(url_for("profile"))

@app.route("/referrals")
@login_required
def referrals():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    # אם יש לך הפונקציה הזו - נשמור שלמשתמש יש ref_code
    try:
        ensure_user_ref_code(user["id"])
    except Exception:
        pass

    db = get_db()

    # יתרת זיכוי (אם אין עמודה/ערך -> 0)
    try:
        credit_balance = int(user.get("credit_balance") or 0)
    except Exception:
        credit_balance = 0

    # כמה נרשמו דרך קוד ההפניה שלי
    try:
        referred_count = db.execute(
            "SELECT COUNT(*) AS c FROM users WHERE referred_by = ?",
            (user["id"],)
        ).fetchone()["c"]
    except Exception:
        referred_count = 0

    # קישור ההפניה המלא
    ref_link = url_for("signup", ref=user["ref_code"], _external=True)
    
    # הנחת רפרל (50% חד-פעמי)
    try:
        referral_discount = int(user["referral_discount"] or 0) if "referral_discount" in user.keys() else 0
    except Exception:
        referral_discount = 0

    return render_template(
        "referrals.html",
        user=user,
        ref_link=ref_link,
        credit_balance=credit_balance,
        referred_count=referred_count,
        referral_discount=referral_discount,
        title="הפניות (Referral)"
    )




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
    
    for r in reports:
        try:
            summary = json.loads(r.get("summary_json") or "{}")
            total_sales += summary.get("total_sales", 0)
            if not latest_summary and summary:
                latest_summary = summary
        except:
            pass
    
    # השוואת תקופות אם יש לפחות 2 דוחות מאותו סוג
    comparison = None
    if len(reports) >= 2:
        try:
            # מחפשים שני דוחות מאותו סוג תקופה
            df1 = load_report(reports[1]["id"], u["id"])  # דוח קודם
            df2 = load_report(reports[0]["id"], u["id"])  # דוח אחרון
            if df1 is not None and df2 is not None:
                comparison = compare_periods(df1, df2)
                comparison["report1_name"] = reports[1].get("name", "דוח קודם")
                comparison["report2_name"] = reports[0].get("name", "דוח אחרון")
        except Exception as e:
            print(f"⚠️ שגיאה בהשוואת תקופות: {e}")
    
    period_type_labels = {
        "month": "חודשים",
        "week": "שבועות",
        "day": "ימים",
        "custom": "מותאם אישית"
    }
    
    return render_template("dashboard.html",
                          user=u,
                          reports=reports,
                          reports_by_type=reports_by_type,
                          filter_type=filter_type,
                          period_type_labels=period_type_labels,
                          total_sales=total_sales,
                          total_reports=len(reports),
                          latest_summary=latest_summary,
                          comparison=comparison,
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
    
    if delete_report(report_id, u["id"]):
        flash("הדוח נמחק בהצלחה", "success")
    else:
        flash("שגיאה במחיקת הדוח", "danger")
    
    return redirect(url_for("dashboard"))


@app.route("/profile")
@login_required
def profile():
    u = current_user()
    return render_template("profile.html", user=u, active="profile", title="הפרופיל שלי")

@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    u = current_user()
    if request.method == "GET":
        return render_template("profile_edit.html", user=u, active="profile", title="עריכת פרופיל")

    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not first_name or not last_name:
        flash("נא למלא שם ושם משפחה", "danger")
        return render_template("profile_edit.html", user=u)

    # בדיקת שם משתמש (חובה)
    import re
    if not username:
        flash("שם משתמש הוא שדה חובה", "danger")
        return render_template("profile_edit.html", user=u)
    if len(username) < 4 or len(username) > 20:
        flash("שם משתמש חייב להיות בין 4-20 תווים", "danger")
        return render_template("profile_edit.html", user=u)
    if not re.match(r'^[A-Za-z0-9]+$', username):
        flash("שם משתמש יכול להכיל רק אותיות אנגליות וספרות", "danger")
        return render_template("profile_edit.html", user=u)
    # בדיקה אם שם המשתמש כבר קיים (לא אצל המשתמש הנוכחי)
    existing = get_db().execute("SELECT id FROM users WHERE LOWER(username)=? AND id!=?", (username.lower(), u["id"])).fetchone()
    if existing:
        flash("שם משתמש זה כבר תפוס", "danger")
        return render_template("profile_edit.html", user=u)

    if password:
        if password != confirm:
            flash("האימות לא תואם את הסיסמה החדשה", "danger")
            return render_template("profile_edit.html", user=u)
        # בדיקת תקינות סיסמה
        is_valid, error_msg = validate_password(password)
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

    flash("הפרופיל עודכן בהצלחה", "success")
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    flash("התנתקת בהצלחה", "success")
    return redirect(url_for("index"))


from datetime import datetime


@app.route("/signup", methods=["GET", "POST"])
def signup():
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
    if not username:
        flash("שם משתמש הוא שדה חובה", "danger")
        return render_template("signup.html", **form_data)
    if len(username) < 4 or len(username) > 20:
        flash("שם משתמש חייב להיות בין 4-20 תווים", "danger")
        return render_template("signup.html", **form_data)
    if not re.match(r'^[A-Za-z0-9]+$', username):
        flash("שם משתמש יכול להכיל רק אותיות אנגליות וספרות", "danger")
        return render_template("signup.html", **form_data)
    existing = get_db().execute("SELECT id FROM users WHERE LOWER(username)=?", (username.lower(),)).fetchone()
    if existing:
        flash("שם משתמש זה כבר תפוס", "danger")
        return render_template("signup.html", **form_data)
    
    # אם לא סומן – נחזיר הודעת שגיאה
    if not agree_terms:
        flash("חובה לאשר את תנאי השימוש ומדיניות הפרטיות כדי להירשם.", "danger")
        return render_template("signup.html", **form_data)

    # בדיקת התאמת סיסמאות
    if password != confirm_password:
        flash("הסיסמאות אינן תואמות", "danger")
        return render_template("signup.html", **form_data)

    # בדיקת תקינות סיסמה
    is_valid, error_msg = validate_password(password)
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
        flash("האימייל או שם המשתמש כבר קיימים", "danger")
        return render_template("signup.html", **form_data)

    # קבלת המשתמש החדש (בלי כניסה אוטומטית - צריך לאמת מייל)
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    
    # דואגים שלמשתמש החדש יהיה ref_code
    ensure_user_ref_code(user["id"])
    
    # טיפול בהפניה: אם היה ref בסשן, נקשר את המשתמש למפנה
    ref_code = session.pop("pending_ref", None)
    if ref_code:
        referrer = db.execute("SELECT * FROM users WHERE ref_code=?", (ref_code,)).fetchone()
        if referrer and referrer["id"] != user["id"]:
            # שומרים מי הפנה אותי + עדכון מונה אצל המפנה
            db.execute("UPDATE users SET referred_by=? WHERE id=?", (referrer["id"], user["id"]))
            db.execute("UPDATE users SET referred_count=COALESCE(referred_count,0)+1 WHERE id=?", (referrer["id"],))
            db.commit()
    
    # שליחת מייל אימות
    send_verification_email(email, verification_token)
    
    # מעבירים לדף בדיקת אימייל
    return redirect(url_for("signup_check_email", email=email))


@app.route("/signup/check-email")
def signup_check_email():
    """דף שמציג הודעה לבדוק את האימייל"""
    email = request.args.get("email", "")
    return render_template("signup_check_email.html", email=email, title="בדוק את האימייל שלך")


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
    
    flash("✅ האימייל אומת בהצלחה! ברוכים הבאים ל-OnePoweb!", "success")
    return redirect(url_for("profile"))


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
    snap = session.get("export_payload") or {}
    roi = snap.get("roi") or {}
    # הצלה: אם אין ROI בכלל – הודעה מסודרת
    has_any = bool(roi) and any([
        bool(roi.get("text")), 
        float(roi.get("monthly_gain") or 0) != 0.0, 
        float(roi.get("roi_percent") or 0) != 0.0
    ])
    return render_template(
        "roi.html",
        roi=roi,
        has_any=has_any,
        title="ROI משוער",
        active="roi",
    )


@app.route("/result")
def result():
    plots = LAST_EXPORT.get("plots", [])
    summary = LAST_EXPORT.get("summary", "")
    summary_ai = LAST_EXPORT.get("summary_ai", "")
    roi = LAST_EXPORT.get("roi", {})
    action_items = LAST_EXPORT.get("action_items", [])

    messages = []
    if not plots:
        messages.append("אין גרפים להצגה. חזור לדף הבית והעלה דוח חדש.")

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

    return render_template(
        "result.html",
        plots=plots,
        summary=summary,
        summary_ai=summary_ai,
        roi=roi,
        action_items=action_items,
        messages=messages,
        user_plan=user_plan,
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
    return render_template("error.html", code=404, msg="העמוד לא נמצא"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, msg="שגיאה בשרת"), 500

@app.route("/landing")
def landing():
    return render_template("landing.html", active="landing", title="למה OnePoweb")

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
        ensure_tables()  # כאן נוצרת/מתעדכנת הטבלה

    app.run(debug=True)

