
from fastapi import FastAPI, Query,Body, HTTPException,UploadFile, File
from core.catalog_client import get_catalog_client
import json
import decimal
import datetime
import re
import logging

from routers import (bucket,namespace,get_data,crm_application,table,json_data)
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
app.include_router(json_data.router)

ALLOWED_TABLES = ["Crm",]

@app.get("/")
def root():
    tables_name = ["CRM", ]

    return {"message": "API is running",
            "version": "1.0",
            "Tables": tables_name
            }


def convert_row(row, column_types):
    """Convert MySQL row values to types PyArrow accepts."""
    converted = []
    for value, col_type in zip(row, column_types):
        if col_type.startswith("decimal") and value is not None:
            # Always convert to string to keep precision and satisfy PyArrow
            converted.append(str(value))
        else:
            converted.append(value)
    return converted



def normalize_mysql_type(t):
    return re.sub(r"\(.*\)", "", t).strip().lower()

