import os
import json
import time
import hmac
import base64
import hashlib
import logging
import requests
from typing import Optional, Dict
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import User

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "sports-aggregator-super-secret-auth-key-2026")
TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 30  # 30 days

def create_access_token(user_id: int, email: str, role: str) -> str:
    """
    Создает криптографически подписанный токен доступа (HMAC-SHA256).
    Работает без внешних зависимостей быстро и надежно.
    """
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip('=')
    
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{payload_b64}.{sig_b64}"

def verify_access_token(token: str) -> Optional[Dict]:
    """
    Проверяет подпись и срок действия токена.
    """
    if not token or '.' not in token:
        return None
        
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
            
        payload_b64, sig_b64 = parts
        
        # Проверяем подпись
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')
        
        if not hmac.compare_digest(sig_b64, expected_b64):
            return None
            
        # Декодируем полезную нагрузку
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += '=' * (4 - rem)
        payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Проверяем срок годности
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception as e:
        logger.error(f"Ошибка проверки токена: {e}")
        return None

def verify_google_id_token(credential: str) -> Optional[Dict]:
    """
    Верифицирует Google ID Token через официальный endpoint Google TokenInfo.
    """
    if not credential:
        return None
        
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.error(f"Google TokenInfo вернул статус {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        
        # Проверяем наличие ключевых полей
        if "sub" not in data or "email" not in data:
            return None
            
        return {
            "google_id": data["sub"],
            "email": data["email"].lower(),
            "name": data.get("name") or data.get("email", "").split("@")[0],
            "picture": data.get("picture"),
            "email_verified": data.get("email_verified") == "true" or data.get("email_verified") is True
        }
    except Exception as e:
        logger.error(f"Сбой при обращении к Google OAuth API: {e}")
        return None

async def authenticate_or_register_google_user(session: AsyncSession, google_info: Dict) -> User:
    """
    Находит или регистрирует пользователя в базе данных.
    """
    google_id = google_info["google_id"]
    email = google_info["email"].lower()
    name = google_info.get("name")
    picture = google_info.get("picture")

    # Ищем пользователя по google_id или email
    stmt = select(User).where((User.google_id == google_id) | (User.email == email))
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    # Список главных администраторов системы
    ADMIN_EMAILS = {"ix.bogota.ix@gmail.com"}
    is_admin = email in ADMIN_EMAILS

    now = datetime.now(timezone.utc)
    if user:
        # Обновляем профиль и время последнего входа
        user.last_login_at = now
        if is_admin:
            user.role = "admin"
        if google_id:
            user.google_id = google_id
        if name:
            user.name = name
        if picture:
            user.picture = picture
    else:
        # Создаем нового пользователя
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            picture=picture,
            role="admin" if is_admin else "user",
            is_active=True,
            created_at=now,
            last_login_at=now
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user

def verify_telegram_webapp_data(init_data: str, bot_token: str) -> Optional[Dict]:
    """
    Проверяет криптографическую подпись initData от Telegram Mini App (HMAC-SHA256).
    """
    if not init_data or not bot_token:
        return None
        
    try:
        import urllib.parse
        parsed = dict(urllib.parse.parse_qsl(init_data))
        tg_hash = parsed.pop('hash', None)
        if not tg_hash:
            return None
            
        check_str = '\n'.join(f'{k}={v}' for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode('utf-8'), hashlib.sha256).digest()
        calc_hash = hmac.new(secret_key, check_str.encode('utf-8'), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(calc_hash, tg_hash):
            return None
            
        user_raw = parsed.get("user")
        if user_raw:
            return json.loads(user_raw)
        return parsed
    except Exception as e:
        logger.error(f"Ошибка валидации Telegram WebApp initData: {e}")
        return None

async def authenticate_or_register_telegram_user(session: AsyncSession, tg_user: Dict) -> User:
    """
    Находит или регистрирует пользователя из Telegram Mini App.
    """
    tg_id = str(tg_user.get("id"))
    username = tg_user.get("username")
    first_name = tg_user.get("first_name", "")
    last_name = tg_user.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or (f"@{username}" if username else f"User {tg_id}")
    photo_url = tg_user.get("photo_url")
    
    unique_key = f"tg_{tg_id}"
    email = f"{username}@telegram.org" if username else f"{unique_key}@tma.local"

    stmt = select(User).where((User.google_id == unique_key) | (User.email == email))
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    admin_chat_id = os.getenv("TELEGRAM_CHAT_ID", "135842253")
    ADMIN_TG = {admin_chat_id, "135842253", "ixbogotaix", "bogota"}
    is_admin = tg_id in ADMIN_TG or (username and username.lower() in ADMIN_TG)

    now = datetime.now(timezone.utc)
    if user:
        user.last_login_at = now
        if is_admin:
            user.role = "admin"
        if full_name:
            user.name = full_name
        if photo_url:
            user.picture = photo_url
    else:
        user = User(
            google_id=unique_key,
            email=email,
            name=full_name,
            picture=photo_url,
            role="admin" if is_admin else "user",
            is_active=True,
            created_at=now,
            last_login_at=now
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user
