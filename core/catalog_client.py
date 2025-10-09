from dotenv import load_dotenv
from pyiceberg.catalog.rest import RestCatalog
from botocore.client import Config
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import  HTTPException
from fastapi.security import HTTPBearer
import os
import logging
import boto3

load_dotenv("config.env")
logger = logging.getLogger(__name__)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
TOKEN_EXPIRE_HOURS = 1

security = HTTPBearer()

class Creds:
    def __init__(self):
        self.CATALOG_URI = os.getenv("CATALOG_URI")
        self.WAREHOUSE = os.getenv("WAREHOUSE")
        self.TOKEN = os.getenv("TOKEN")
        self.CATALOG_NAME = os.getenv("CATALOG_NAME")

    def catalog_valid(self):
        if not all([self.CATALOG_URI, self.WAREHOUSE, self.TOKEN]):
            raise ValueError("Missing environment variables. Please check CATALOG_URI, WAREHOUSE, or TOKEN.")

        return RestCatalog(
            name=self.CATALOG_NAME,
            warehouse=self.WAREHOUSE,
            uri=self.CATALOG_URI,
            token=self.TOKEN
        )
def get_catalog_client():
    try:
        return Creds().catalog_valid()
    except Exception as e:
        logger.error(f"Failed to initialize Iceberg catalog client: {e}")
        raise HTTPException(status_code=500, detail="Cloudflare R2 client initialization failed")



class CloudflareR2Creds:
    def __init__(self):
        self.ACCOUNT_ID = os.getenv("ACCOUNT_ID")
        self.ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
        self.SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
        self.BUCKET_NAME = os.getenv("BUCKET_NAME")
        self.ENDPOINT = os.getenv("ENDPOINT")
        self.client = None



    def get_client(self):
        if not self.client:
            if not all([self.ACCESS_KEY_ID, self.SECRET_ACCESS_KEY, self.ENDPOINT]):
                raise ValueError("Missing Cloudflare R2 environment variables.")
        self.client = boto3.client(
            "s3",
            endpoint_url=self.ENDPOINT,
            aws_access_key_id=self.ACCESS_KEY_ID,
            aws_secret_access_key=self.SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto"
        )
        return self.client


def get_r2_client():
    try:
        return CloudflareR2Creds().get_client()
    except Exception as e:
        logger.error(f"Failed to initialize R2 client: {e}")
        raise HTTPException(status_code=500, detail="Cloudflare R2 client initialization failed")


# ---------------- JWT Utility ----------------
def create_jwt(app_name: str):
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    # expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_HOURS)
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