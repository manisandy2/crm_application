from dotenv import load_dotenv
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import  HTTPException
from fastapi.security import HTTPBearer
import os
import logging

load_dotenv("config.env")
logger = logging.getLogger(__name__)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
# TOKEN_EXPIRE_HOURS = os.getenv("JWT_TOKEN_EXPIRE_HOURS")
TOKEN_EXPIRE_HOURS = 1
security = HTTPBearer()

# ---------------- JWT Utility ----------------
def create_jwt(app_name: str):
    # expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_HOURS)
    payload = {
        "app": app_name,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("app") != "CRM":
            raise HTTPException(status_code=401, detail="Invalid appName in token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")