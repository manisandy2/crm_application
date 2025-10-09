# from mapping import *
# from pyiceberg import types
# from pyiceberg.partitioning import PartitionSpec, PartitionField
# from pyiceberg.transforms import IdentityTransform
# from pyiceberg.exceptions import NoSuchNamespaceError, NoSuchTableError
# from fastapi import APIRouter, Query, Body, HTTPException,Depends,status
# from datetime import datetime
# import uuid, json, time
# import pyarrow as pa
# from pyiceberg.expressions import EqualTo,And,GreaterThanOrEqual,LessThanOrEqual
# from core.catalog_client import get_catalog_client,get_r2_client,security,verify_jwt
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
#
#
#
# router = APIRouter(prefix="", tags=["R2 Bucket"])
#
# @router.post("/InsertOne")
# def insert_one(
#     namespace: str = Query(..., description="Namespace (e.g. 'transactions')"),
#     table_name: str = Query(..., description="Table (e.g. 'pos')"),
#     record: dict = Body(..., description="Single JSON record to insert into Iceberg"),
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):
#     # ───── Verify JWT ─────
#     try:
#         verify_jwt(credentials.credentials)
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
#
#     start_time = time.time()
#
#     if not record:
#         raise HTTPException(status_code=400, detail="No records provided")
#
#     # ───── Add Metadata Fields ─────
#     ticket_id = record.get("ticketId", str(uuid.uuid4()))
#     created_at = record.get("createdAt", datetime.utcnow().isoformat())
#
#     record.update({
#         "ticketId": ticket_id,
#         "createdAt": created_at,
#         "year": int(created_at[:4]),
#         "month": int(created_at[5:7]),
#         "day": int(created_at[8:10])
#     })
#
#     try:
#         # ───── Schema & Conversion ─────
#         record_with_raw = {**record, "raw_json": json.dumps(record, ensure_ascii=False)}
#         iceberg_schema, arrow_schema = infer_schema_from_record(record_with_raw)
#
#         for col_name in ["year", "month", "day"]:
#             try:
#                 iceberg_schema.find_field(col_name)
#             except KeyError:
#                 iceberg_schema = iceberg_schema.add_column(col_name, types.IntegerType())
#
#         converted_record = convert_row(record_with_raw, arrow_schema)
#         arrow_table = pa.Table.from_pylist([converted_record])
#
#         # ───── Catalog Handling ─────
#         try:
#             catalog = get_catalog_client()
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail={"error_code": "ERR_CATALOG_CLIENT", "message": str(e)}
#             )
#
#         # Ensure namespace exists
#         try:
#             catalog.load_namespace_properties(namespace)
#         except NoSuchNamespaceError:
#             try:
#                 catalog.create_namespace(namespace)
#             except Exception as e:
#                 raise HTTPException(
#                     status_code=500,
#                     detail={"error_code": "ERR_NAMESPACE_CREATE", "message": str(e)}
#                 )
#
#         # ───── Load/Create Table ─────
#         table_identifier = f"{namespace}.{table_name}"
#         try:
#             tbl = catalog.load_table(table_identifier)
#         except NoSuchTableError:
#             partition_spec = PartitionSpec(fields=[
#                 PartitionField(
#                     source_id=iceberg_schema.find_field("year").field_id,
#                     field_id=2001,
#                     transform=IdentityTransform(),
#                     name="year"
#                 ),
#                 PartitionField(
#                     source_id=iceberg_schema.find_field("month").field_id,
#                     field_id=2002,
#                     transform=IdentityTransform(),
#                     name="month"
#                 ),
#                 PartitionField(
#                     source_id=iceberg_schema.find_field("day").field_id,
#                     field_id=2003,
#                     transform=IdentityTransform(),
#                     name="day"
#                 ),
#             ]
#             )
#             try:
#                 tbl = catalog.create_table(
#                     identifier=table_identifier,
#                     schema=iceberg_schema,
#                     partition_spec=partition_spec,
#                     properties={"write.partition.path-style": "directory"},
#                 )
#             except Exception as e:
#                 raise HTTPException(
#                     status_code=500,
#                     detail={"error_code": "ERR_TABLE_CREATE", "message": str(e)}
#                 )
#
#         # ───── Append Record ─────
#         try:
#             schema_obj = tbl.schema()
#             arrow_table = arrow_table.select([f.name for f in schema_obj.fields])
#             tbl.append(arrow_table)
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail={"error_code": "ERR_APPEND_RECORD", "message": str(e)}
#             )
#
#     except HTTPException:
#         raise  # Re-raise known API errors
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={"error_code": "ERR_UNEXPECTED", "message": str(e)}
#         )
#
#     # ───── Success Response ─────
#     elapsed = round(time.time() - start_time, 2)
#     return {
#         "status": "success",
#         "namespace": namespace,
#         "table": table_name,
#         "ticketId": ticket_id,
#         "rows_written": len(arrow_table),
#         "elapsed_seconds": elapsed,
#     }