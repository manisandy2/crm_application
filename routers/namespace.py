from fastapi import APIRouter,HTTPException,Query,Depends
from core.catalog_client import get_catalog_client,verify_jwt,security
from pyiceberg.exceptions import NamespaceAlreadyExistsError,NoSuchNamespaceError
from fastapi.security import HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/namespaces", tags=["Namespaces"])

@router.get("/list")
def list_namespaces(
    credentials: HTTPAuthorizationCredentials = Depends(security)

):
    # Verify the JWT
    try:
        verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )

    catalog = get_catalog_client()
    try:
        namespaces = catalog.list_namespaces()
        logger.info("Fetched namespaces successfully.")
        return {"status": "success", "data": namespaces}
    except Exception as e:
        logger.error(f"Failed to list namespaces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list namespaces: {str(e)}")
    finally:
        try:
            catalog.close()
        except Exception:
            pass

@router.post("/create")
def create_namespace(
        namespace: str = Query(..., description="Namespace (e.g. 'crm')"),
        credentials: HTTPAuthorizationCredentials = Depends(security)

):
    # Verify the JWT
    try:
        verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    catalog = get_catalog_client()
    try:
        catalog.create_namespace(namespace)
        # logger.info(f"Namespace '{namespace}' created successfully.")
        return {"status": "success", "message": f"Namespace '{namespace}' created successfully."}
    except NamespaceAlreadyExistsError:
        # logger.warning(f"Namespace '{namespace}' already exists.")
        raise HTTPException(status_code=409, detail=f"Namespace '{namespace}' already exists.")
    except Exception as e:
        # logger.error(f"Failed to create namespace '{namespace}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create namespace '{namespace}': {str(e)}")
    finally:
        try:
            catalog.close()
        except Exception:
            pass

@router.post("/rename")
def rename_namespace(
    old_namespace: str = Query(..., description="Existing namespace name (e.g. 'crm')"),
    new_namespace: str = Query(..., description="New namespace name (e.g. 'crm_v2')"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify the JWT
    try:
        verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    catalog = get_catalog_client()
    try:
        # Get all tables inside old namespace
        tables = catalog.list_tables(old_namespace)
        # Create the new namespace
        catalog.create_namespace(new_namespace)

        # Move (rename) each table to the new namespace
        for table in tables:
            old_table_name = f"{old_namespace}.{table}"
            new_table_name = f"{new_namespace}.{table}"
            catalog.rename_table(old_table_name, new_table_name)

        # Delete old namespace
        catalog.drop_namespace(old_namespace)

        return {
            "status": "success",
            "message": f"Namespace renamed from '{old_namespace}' to '{new_namespace}' successfully.",
            "migrated_tables": tables
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename namespace: {str(e)}")

    finally:
        try:
            catalog.close()
        except Exception:
            pass

@router.delete("/delete")
def delete_namespace(namespace: str = Query(..., description="Namespace to delete")):
    catalog = get_catalog_client()
    try:
        catalog.drop_namespace(namespace)
        logger.info(f"Namespace '{namespace}' deleted successfully.")
        return {"status": "success", "message": f"Namespace '{namespace}' deleted successfully."}
    except NoSuchNamespaceError:
        logger.warning(f"Namespace '{namespace}' does not exist.")
        raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' does not exist.")
    except Exception as e:
        logger.error(f"Failed to delete namespace '{namespace}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete namespace '{namespace}': {str(e)}")
    finally:
        try:
            catalog.close()
        except Exception:
            pass

