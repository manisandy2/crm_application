
from fastapi import FastAPI, Query,Body, HTTPException,UploadFile, File
from core.catalog_client import get_catalog_client
import json,decimal,datetime,re,logging

from routers import (bucket, namespace, get_data, crm_application, table )
from core.catalog_client import create_jwt
from fastapi import Depends, FastAPI, HTTPException, status,Form
from fastapi import FastAPI, HTTPException, Request,Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta

from typing import Optional
from fastapi.responses import JSONResponse

security = HTTPBearer()

TOKEN_EXPIRE_HOURS = 1


logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="ignore")
        return super().default(obj)

app = FastAPI()


app.include_router(bucket.router)
app.include_router(namespace.router)
app.include_router(table.router)
app.include_router(crm_application.router)
app.include_router(get_data.router)

# app.include_router(json_data.router)

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ALLOWED_TABLES = ["Crm",]

# @app.get("/")
# def root():
#     tables_name = ["CRM", ]
#
#     return {"message": "API is running",
#             "version": "1.0",
#             "Tables": tables_name
#             }


def convert_row(row, column_types):

    converted = []
    for value, col_type in zip(row, column_types):
        if col_type.startswith("decimal") and value is not None:
            converted.append(str(value))
        else:
            converted.append(value)
    return converted



def normalize_mysql_type(t):
    return re.sub(r"\(.*\)", "", t).strip().lower()



# @app.post("/auth/token")
# async def get_token(request: Request):
#     app_name = request.headers.get("appName")
#     if app_name != "CRM":
#         raise HTTPException(status_code=401, detail="Invalid appName header")
#     token = create_jwt(app_name)
#     return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_EXPIRE_HOURS * 3600}

@app.post("/auth/token")
async def get_token(
        request: Request,
        app_name: Optional[str] = Header(None)

):
    if not app_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'appName' header"
        )

    if app_name != "CRM":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 'appName' header"
        )

    try:
        token = create_jwt(app_name)  # Your JWT creation logic
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token generation failed: {str(e)}"
        )

    return JSONResponse(
        content={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": TOKEN_EXPIRE_HOURS * 3600
        },
        status_code=status.HTTP_200_OK
    )