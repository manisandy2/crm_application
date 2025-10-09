from fastapi import APIRouter,Query,Depends
from core.catalog_client import get_r2_client,security,verify_jwt
from fastapi.security import HTTPAuthorizationCredentials

from mapping import *
router = APIRouter(prefix="", tags=["Json Data"])

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="ignore")
        return super().default(obj)

@router.get("/list")
def get_bucket_list(
    bucket_name: str = Query(..., title="Bucket Name"),
    bucket_path: str = Query("iceberg_json", description="Folder path in R2 (default: iceberg_json)"),
    credentials: HTTPAuthorizationCredentials = Depends(security)

):
    verify_jwt(credentials.credentials)
    r2_client = get_r2_client()
    prefix = f"{bucket_path}/"

    try:
        response = r2_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        print(response)

        files = []
        if "Contents" in response:
            files = [obj["Key"] for obj in response["Contents"]]

        return {
            "total_files": len(files),
            "files": files
        }

    except Exception as e:
        return {"error": str(e)}


@router.delete("/delete-files")
def delete_files(
        bucket_name: str = Query(..., title="Bucket Name"),
        bucket_path: str = Query("iceberg_json", description="Folder path in R2 (default: __r2_data_catalog)"),
        prefix_only: bool = Query(True, description="Delete all files under prefix (True) or specific file (False)"),
        file_name: str = Query(None, description="Specific file name (e.g. 'batch_0.json') if prefix_only=False"),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    verify_jwt(credentials.credentials)
    r2_client = get_r2_client()
    prefix = f"{bucket_path}/"
    print("Deleting files")
    print(f"{prefix}")
    try:
        deleted_files = []

        if prefix_only:
            response = r2_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if "Contents" in response:
                for obj in response["Contents"]:
                    print(obj["Key"])
                    r2_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
                    deleted_files.append(obj["Key"])
        else:
            if not file_name:
                return {"error": "file_name is required if prefix_only=False"}

            file_key = prefix + file_name
            r2_client.delete_object(Bucket=bucket_name, Key=file_key)
            deleted_files.append(file_key)

        return {
            "message": f"{len(deleted_files)} file(s) deleted",
            "deleted_files": deleted_files
        }

    except Exception as e:
        return {"error": str(e)}