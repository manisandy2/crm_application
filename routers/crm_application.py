from mapping import *
from pyiceberg import types
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import IdentityTransform
from pyiceberg.exceptions import NoSuchNamespaceError, NoSuchTableError
from fastapi import APIRouter, Query, Body, HTTPException,Depends
from datetime import datetime
import uuid, json, time
import pyarrow as pa
from pyiceberg.expressions import EqualTo,And,GreaterThanOrEqual,LessThanOrEqual
from core.catalog_client import get_catalog_client,get_r2_client,security,verify_jwt
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, Depends, Request, HTTPException
from datetime import date
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed


router = APIRouter(prefix="/crm", tags=["CRM Application"])



# @router.post("/InsertOne")
# def insert_one(
#     namespace: str = Query(..., description="Namespace (e.g. 'transactions')"),
#     table_name: str = Query(..., description="Table (e.g. 'pos')"),
#     record: dict = Body(..., description="Single JSON record to insert into Iceberg"),
# ):
#     start_time = time.time()
#     # ---------------------------
#     # Iceberg Schema
#     # ---------------------------
#     # iceberg_schema = Schema(
#     #     [
#     #         Types.NestedField.required(1, "ticketId", Types.StringType()),
#     #         Types.NestedField.required(2, "createdAt", Types.TimestampType()),  # TimestampType
#     #     ]
#     # )
#
#     if not record:
#         raise HTTPException(status_code=400, detail="No records provided")
#
#     # ------------------------
#     # Step 1: Save JSON to R2
#     # ------------------------
#     try:
#         r2_client = get_r2_client()
#         ticket_id = record.get("ticketId", str(uuid.uuid4()))
#         record["ticketId"] = ticket_id
#
#         created_at = record.get("createdAt", str(uuid.uuid4()))
#
#         record["createdAt"] = created_at
#         try:
#             create_date = datetime.fromisoformat(created_at)  # full datetime
#         except ValueError:
#             # fallback if it's just a date
#             create_date = datetime.strptime(created_at[0:10], "%Y-%m-%d")
#
#         # print(create_date.year)
#         # print(create_date.month)
#         # print(create_date.day)  # not .date
#
#         r2_key = f"{namespace}/{table_name}/{create_date.year}/{create_date.month}/{create_date.day}/{ticket_id}.json"
#         r2_client.put_object(
#             Bucket=namespace,
#             Key=r2_key,
#             Body=json.dumps(record, indent=2, cls=CustomJSONEncoder).encode("utf-8"),
#             ContentType="application/json",
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to store record in R2: {str(e)}")
#
#     # ------------------------
#     # Step 2: Prepare record
#     # ------------------------
#     try:
#         # Add raw JSON string
#         record_with_raw = {**record, "raw_json": json.dumps(record, ensure_ascii=False)}
#
#         # Auto-fill required fields
#         if "ticketId" not in record_with_raw:
#             record_with_raw["ticket_id"] = str(uuid.uuid4())
#
#         if "createdAt" not in record_with_raw:
#             record_with_raw["createdAt"] = datetime.utcnow().isoformat()
#
#         # Infer schema
#         iceberg_schema, arrow_schema = infer_schema_from_record(record_with_raw)
#
#         # Convert row → Arrow table
#         converted_record = convert_row(record_with_raw, arrow_schema)
#         arrow_table = pa.Table.from_pylist([converted_record], schema=arrow_schema)
#
#         catalog = get_catalog_client()
#
#
#         # Ensure namespace exists
#         try:
#             catalog.load_namespace_properties(namespace)
#         except NoSuchNamespaceError:
#             catalog.create_namespace(namespace)
#
#         table_identifier = f"{namespace}.{table_name}"
#
#
#
#         # if isinstance(created_at, str):
#         #     try:
#         #         created_at_dt = datetime.fromisoformat(created_at)
#         #     except ValueError:
#         #         created_at_dt = datetime.strptime(created_at[:10], "%Y-%m-%d")
#         # else:
#         #     created_at_dt = created_at
#         #
#         # record["createdAt"] = created_at_dt  # ensure it's a datetime
#
#         # Partition spec
#         ticket_id_field = iceberg_schema.find_field("ticketId")
#         created_at_field = iceberg_schema.find_field("createdAt")
#         print(ticket_id_field)
#         print("Date",created_at_field.field_id)
#         print(iceberg_schema)
#         partition_spec = PartitionSpec(
#             fields=[
#                 PartitionField(
#                     source_id=ticket_id_field.field_id,
#                     field_id=1000,
#                     transform=IdentityTransform(),
#                     name="Id",
#                 ),
#                 PartitionField(
#                     source_id=created_at_field.field_id,
#                     field_id=1001,
#                     transform=IdentityTransform(),
#                     name="date",
#                 ),
#             ]
#         )
#         print("partition_spec",partition_spec.fields)
#
#         # partition_spec = PartitionSpec(
#         #     fields=[
#         #         PartitionField(
#         #             source_id=ticket_id_field.field_id,
#         #             field_id=1000,
#         #             transform=IdentityTransform(),
#         #             name="ticketId",
#         #         ),
#         #         PartitionField(
#         #             source_id=created_at_field.field_id,
#         #             field_id=1001,
#         #             transform=IdentityTransform(),
#         #             name="createdAt",
#         #         ),
#         #     ]
#         # )
#         # Partition spec
#         # ticket_id_field = iceberg_schema.find_field("ticketId")
#         # created_at_field = iceberg_schema.find_field("createdAt")
#         #
#         # partition_spec = PartitionSpec(
#         #  fields=[
#         #     PartitionField(
#         #     source_id=created_at_field.field_id,
#         #     field_id=2001,
#         #     name="year",
#         #     transform=YearTransform()
#         # ),
#         # PartitionField(
#         #     source_id=created_at_field.field_id,
#         #     field_id=2002,
#         #     name="month",
#         #     transform=MonthTransform()
#         # ),
#         # PartitionField(
#         #     source_id=created_at_field.field_id,
#         #     field_id=2003,
#         #     name="day",
#         #     transform=DayTransform()
#         # ),
#         # ])
#         # created_at_field = iceberg_schema.find_field("createdAt")
#         # next_field_id = max(f.field_id for f in iceberg_schema.fields) + 1
#         #
#         # partition_spec = PartitionSpec(
#         #     fields=[
#         #         PartitionField(
#         #             source_id=created_at_field.field_id,
#         #             field_id=next_field_id,
#         #             name="year",
#         #             transform=YearTransform(),
#         #         ),
#         #         PartitionField(
#         #             source_id=created_at_field.field_id,
#         #             field_id=next_field_id + 1,
#         #             name="month",
#         #             transform=MonthTransform(),
#         #         ),
#         #         PartitionField(
#         #             source_id=created_at_field.field_id,
#         #             field_id=next_field_id + 2,
#         #             name="day",
#         #             transform=DayTransform(),
#         #         ),
#         #     ]
#         # )
#
#         # Load or create table
#         try:
#             tbl = catalog.load_table(table_identifier)
#         except NoSuchTableError:
#             tbl = catalog.create_table(
#                 identifier=table_identifier,
#                 schema=iceberg_schema,
#                 partition_spec=partition_spec,
#                 properties={
#                     "write.partition.path-style": "directory"
#                 },
#
#             )
#
#         # Append record
#         tbl.append(arrow_table)
#
#         elapsed = round(time.time() - start_time, 2)
#
#         return {
#             "status": "success",
#             "namespace": namespace,
#             "table": table_name,
#             "ticketId": ticket_id,
#             "rows_written": 1,
#             "partition_by": ["ticket_id", "createdAt"],
#             "elapsed_seconds": elapsed,
#         }
#
#     except RESTError as e:
#         raise HTTPException(status_code=500, detail=f"Iceberg REST API error: {str(e)}")
#
#     except NamespaceAlreadyExistsError:
#         raise HTTPException(status_code=409, detail=f"Namespace '{namespace}' already exists")
#
#     except pa.ArrowInvalid as e:
#         raise HTTPException(status_code=400, detail=f"Arrow schema error: {str(e)}")
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def save_to_r2(
        bucket: str, key: str, record: dict, encoder=json.JSONEncoder,
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    verify_jwt(credentials.credentials)
    client = get_r2_client()
    try:
        response = client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(record, indent=2, cls=encoder).encode("utf-8"),
            ContentType="application/json",
        )
        return {
            "status": "success",
            "bucket": bucket,
            "key": key,
            "r2_response": response,
        }
    except ClientError as e:
        return {"status": "error", "message": str(e)}

# @router.post("/InsertOne")
# def insert_one(
#     namespace: str = Query(..., description="Namespace (e.g. 'transactions')"),
#     table_name: str = Query(..., description="Table (e.g. 'pos')"),
#     record: dict = Body(..., description="Single JSON record to insert into Iceberg"),
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):
#     verify_jwt(credentials.credentials)
#     start_time = time.time()
#
#     try:
#         verify_jwt(credentials.credentials)
#     except Exception as e:
#         raise HTTPException(
#             status_code=401,
#             detail=f"Invalid token: {str(e)}"
#         )
#
#     if not record:
#         raise HTTPException(status_code=400, detail="No records provided")
#
#     ticket_id = record.get("ticketId", str(uuid.uuid4()))
#     record["ticketId"] = ticket_id
#
#     created_at = record.get("createdAt", datetime.utcnow().isoformat())
#     record["createdAt"] = created_at
#
#     # Partition fields
#     record["year"] = int(created_at[:4])
#     record["month"] = int(created_at[5:7])
#     record["day"] = int(created_at[8:10])
#
#
#     try:
#
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
#         catalog = get_catalog_client()
#         try:
#             catalog.load_namespace_properties(namespace)
#         except NoSuchNamespaceError:
#             catalog.create_namespace(namespace)
#
#         table_identifier = f"{namespace}.{table_name}"
#
#         try:
#             tbl = catalog.load_table(table_identifier)
#         except NoSuchTableError:
#             partition_spec = PartitionSpec(
#                 fields=[
#                     PartitionField(
#                         source_id=iceberg_schema.find_field("year").field_id,
#                         field_id=2001,
#                         transform=IdentityTransform(),
#                         name="year",
#                     ),
#                     PartitionField(
#                         source_id=iceberg_schema.find_field("month").field_id,
#                         field_id=2002,
#                         transform=IdentityTransform(),
#                         name="month",
#                     ),
#                     PartitionField(
#                         source_id=iceberg_schema.find_field("day").field_id,
#                         field_id=2003,
#                         transform=IdentityTransform(),
#                         name="day",
#                     ),
#                 ]
#             )
#
#             tbl = catalog.create_table(
#                 identifier=table_identifier,
#                 schema=iceberg_schema,
#                 partition_spec=partition_spec,
#                 properties={"write.partition.path-style": "directory"},
#             )
#
#
#         schema_obj = tbl.schema()
#         arrow_table = arrow_table.select([f.name for f in schema_obj.fields])
#
#
#         tbl.append(arrow_table)
#
#         elapsed = round(time.time() - start_time, 2)
#         return {
#             "status_code": 200,
#             "status": "success",
#             "namespace": namespace,
#             "table": table_name,
#             "ticketId": ticket_id,
#             "rows_written": len(arrow_table),
#             # "partition_by": ["year", "month", "day"],
#             "elapsed_seconds": elapsed,
#         }
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# json data 100000
@router.post("/InsertOne_day_wise")
def insert_one(
    namespace: str = Query(..., description="Namespace (e.g. 'transactions')"),
    table_name: str = Query(..., description="Table (e.g. 'pos')"),
    default_date: str = Query(..., description="Date (e.g. '2021-05-01')"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    verify_jwt(credentials.credentials)
    start_time = time.time()

    path = r"json_data_backup/Transaction_pos_202510071301.json"

    try:
        with open(path, 'r') as file:
            data = json.load(file)

        transactions = data.get("Transaction_pos", [])
        if not isinstance(transactions, list):
            raise HTTPException(status_code=400, detail="Invalid JSON format: 'Transaction_pos' must be a list")

        transactions = transactions[:100000]  # For test
        # default_date = "2025-12-10"
        enriched_records = []
        for transaction in transactions:
            created_at = transaction.get("createdAt", datetime.strptime(default_date, "%Y-%m-%d").isoformat())
            transaction.update({
                "createdAt":datetime.strptime(default_date, "%Y-%m-%d").isoformat(),
                # "createdAt": created_at,
                "year": int(created_at[:4]),
                "month": int(created_at[5:7]),
                "day": int(created_at[8:10]),
                # "created_at": datetime.strptime("2025-12-01", "%Y-%m-%d").isoformat()
            })
            # print(transaction)
            record_with_raw = {**transaction, "raw_json": json.dumps(transaction, ensure_ascii=False)}
            enriched_records.append(record_with_raw)

        if not enriched_records:
            raise HTTPException(status_code=400, detail="No valid records found")

        # Infer schemas dynamically
        iceberg_schema, arrow_schema = infer_schema_from_record(enriched_records[0])

        # Add partition fields if missing
        for col_name in ["year", "month", "day"]:
            try:
                iceberg_schema.find_field(col_name)
            except KeyError:
                iceberg_schema = iceberg_schema.add_column(col_name, types.IntegerType())

        arrow_table = pa.Table.from_pylist(enriched_records, schema=arrow_schema)

        catalog = get_catalog_client()
        try:
            catalog.load_namespace_properties(namespace)
        except NoSuchNamespaceError:
            catalog.create_namespace(namespace)

        table_identifier = f"{namespace}.{table_name}"

        try:
            tbl = catalog.load_table(table_identifier)
        except NoSuchTableError:
            partition_spec = PartitionSpec(
                fields=[
                    PartitionField(source_id=iceberg_schema.find_field("year").field_id, field_id=2001, transform=IdentityTransform(), name="year"),
                    PartitionField(source_id=iceberg_schema.find_field("month").field_id, field_id=2002, transform=IdentityTransform(), name="month"),
                    PartitionField(source_id=iceberg_schema.find_field("day").field_id, field_id=2003, transform=IdentityTransform(), name="day"),
                ]
            )
            tbl = catalog.create_table(
                identifier=table_identifier,
                schema=iceberg_schema,
                partition_spec=partition_spec,
                properties={"write.partition.path-style": "directory"},
            )

        # Align columns and append data
        arrow_table = arrow_table.select([f.name for f in tbl.schema().fields])
        tbl.append(arrow_table)

        elapsed = round(time.time() - start_time, 2)
        return {
            "status_code": 200,
            "status": "success",
            "namespace": namespace,
            "table": table_name,
            "rows_written": len(enriched_records),
            "elapsed_seconds": elapsed,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/InsertOne_month_wise")
def insert_one(
    namespace: str = Query(..., description="Namespace (e.g. 'transactions')"),
    table_name: str = Query(..., description="Table (e.g. 'pos')"),
    default_date: str = Query(..., description="Date (e.g. '2021-05-01')"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    verify_jwt(credentials.credentials)
    start_time = time.time()

    path = r"json_data_backup/Transaction_pos_202510071301.json"

    try:
        with open(path, 'r') as file:
            data = json.load(file)

        transactions = data.get("Transaction_pos", [])
        if not isinstance(transactions, list):
            raise HTTPException(status_code=400, detail="Invalid JSON format: 'Transaction_pos' must be a list")

        transactions = transactions[:100000]  # For test
        # default_date = "2025-12-10"
        enriched_records = []
        for transaction in transactions:
            created_at = transaction.get("createdAt", datetime.strptime(default_date, "%Y-%m-%d").isoformat())
            transaction.update({
                "createdAt":datetime.strptime(default_date, "%Y-%m-%d").isoformat(),
                # "createdAt": created_at,
                "year": int(created_at[:4]),
                "month": int(created_at[5:7]),
                # "day": int(created_at[8:10]),
                # "created_at": datetime.strptime("2025-12-01", "%Y-%m-%d").isoformat()
            })
            # print(transaction)
            record_with_raw = {**transaction, "raw_json": json.dumps(transaction, ensure_ascii=False)}
            enriched_records.append(record_with_raw)

        if not enriched_records:
            raise HTTPException(status_code=400, detail="No valid records found")

        # Infer schemas dynamically
        iceberg_schema, arrow_schema = infer_schema_from_record(enriched_records[0])

        # Add partition fields if missing
        # for col_name in ["year", "month", "day"]:
        for col_name in ["year", "month"]:
            try:
                iceberg_schema.find_field(col_name)
            except KeyError:
                iceberg_schema = iceberg_schema.add_column(col_name, types.IntegerType())

        arrow_table = pa.Table.from_pylist(enriched_records, schema=arrow_schema)

        catalog = get_catalog_client()
        try:
            catalog.load_namespace_properties(namespace)
        except NoSuchNamespaceError:
            catalog.create_namespace(namespace)

        table_identifier = f"{namespace}.{table_name}"

        try:
            tbl = catalog.load_table(table_identifier)
        except NoSuchTableError:
            partition_spec = PartitionSpec(
                fields=[
                    PartitionField(source_id=iceberg_schema.find_field("year").field_id, field_id=2001, transform=IdentityTransform(), name="year"),
                    PartitionField(source_id=iceberg_schema.find_field("month").field_id, field_id=2002, transform=IdentityTransform(), name="month"),
                    # PartitionField(source_id=iceberg_schema.find_field("day").field_id, field_id=2003, transform=IdentityTransform(), name="day"),
                ]
            )
            tbl = catalog.create_table(
                identifier=table_identifier,
                schema=iceberg_schema,
                partition_spec=partition_spec,
                properties={"write.partition.path-style": "directory"},
            )

        # Align columns and append data
        arrow_table = arrow_table.select([f.name for f in tbl.schema().fields])
        tbl.append(arrow_table)

        elapsed = round(time.time() - start_time, 2)
        return {
            "status_code": 200,
            "status": "success",
            "namespace": namespace,
            "table": table_name,
            "rows_written": len(enriched_records),
            "elapsed_seconds": elapsed,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# @router.get("/Inspect")
# def table_inspect(
#     namespace: str = Query(..., description="Namespace (e.g. 'Namespace')"),
#     table_name: str = Query(..., description="Table name (e.g. 'Table name')")
# ):
#     try:
#         catalog = get_catalog_client()
#         table = catalog.load_table((namespace, table_name))
#
#         snapshots = list(table.snapshots())
#
#         snapshot_data = []
#         for s in snapshots:
#             snapshot_data.append({
#                 "snapshot_id": getattr(s, "snapshot_id", None),
#                 "parent_snapshot_id": getattr(s, "parent_snapshot_id", None),
#                 "timestamp_ms": getattr(s, "timestamp_ms", None),
#                 "manifest_list": getattr(s, "manifest_list", None),
#                 "summary": getattr(s, "summary", {})
#             })
#
#         return {
#             "namespace": namespace,
#             "table_name": table.name,
#             "records_count": len(snapshots),
#             "snapshots": snapshot_data
#         }
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to inspect table: {str(e)}")
#
# @router.get("/filter")
# def get_data(namespace: str = Query(..., description="Namespace (e.g. 'Namespace')"),
#     table_name: str = Query(..., description="Table name (e.g. 'Table name')")
# ):
#     try:
#         catalog = get_catalog_client()
#         table = catalog.load_table((namespace, table_name))
#     except Exception as e:
#
#         raise HTTPException(status_code=500, detail="Error loading table from catalog")
#
#     try:
#         scan = table.scan()
#         files = [task.file.file_path for task in scan.plan_files()]
#     except Exception as e:
#
#         raise HTTPException(status_code=500, detail="Error scanning table files")
#
#     try:
#         snapshots = list(table.snapshots())
#         snapshot_data = []
#         for s in snapshots:
#             ts = getattr(s, "timestamp_ms", None)
#             snapshot_data.append({
#                 "snapshot_id": getattr(s, "snapshot_id", None),
#                 "parent_snapshot_id": getattr(s, "parent_snapshot_id", None),
#                 "timestamp_ms": ts,
#                 "manifest_list": getattr(s, "manifest_list", None),
#                 "date_time": datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d %H:%M:%S") if ts else None,
#                 "summary": getattr(s, "summary", {})
#             })
#     except Exception as e:
#
#         raise HTTPException(status_code=500, detail="Error retrieving snapshot data")
#
#     return {
#         "namespace": namespace,
#         "table_name": f"{namespace}.{table_name}",
#         "records_count": len(snapshots),
#         "snapshots": snapshot_data,
#         "parquet_files": files
#     }

# @router.get("/filter-data")
# def get_filtered_data(
#     namespace: str = Query(..., description="Namespace (e.g. 'CRM_Application')"),
#     table_name: str = Query(..., description="Table name (e.g. 'Serial')"),
#     columns: list[str] = Query(..., description="Columns to filter on (comma-separated or multiple query params)"),
#     values: list[str] = Query(..., description="Values to match (in same order as columns)")
# ):
#     start_time = time.time()
#
#     try:
#         if len(columns) != len(values):
#             return {
#                 "status": "error",
#                 "error_code": "MISMATCHED_COLUMNS_VALUES",
#                 "message": "Number of columns and values must match",
#                 "data": []
#             }
#
#         catalog = get_catalog_client()
#         table = catalog.load_table((namespace, table_name))
#
#         schema_fields = {f.name for f in table.schema().fields}
#         for col in columns:
#             if col not in schema_fields:
#                 return {
#                     "status": "error",
#                     "error_code": "COLUMN_NOT_FOUND",
#                     "message": f"Column '{col}' not found in schema",
#                     "data": []
#                 }
#
#         filter_expr = None
#         for col, val in zip(columns, values):
#             expr = EqualTo(col, val)
#             filter_expr = expr if filter_expr is None else And (filter_expr, expr)
#
#
#         # Apply filter
#         scan = table.scan(row_filter=filter_expr)
#         # print(scan.to_arrow())
#
#         rows = []
#         arrow_table = scan.to_arrow()
#
#         for batch in arrow_table.to_batches():
#             rows.extend(batch.to_pylist())
#
#         elapsed = round(time.time() - start_time, 2)
#         print("Data len:",len(rows))
#
#         try:
#             if len(rows) == 0:
#                 return {"status": "error", "error_code": "NO_DATA", "message": "No data found"}
#         except Exception as e:
#             return {"status": "error", "error_code": "NO_DATA", "message": str(e)}
#
#         # metadata = {
#         #     "namespace": namespace,
#         #     "table": table_name,
#         #     "filters": dict(zip(columns, values)),
#         #     "snapshot_id": table.current_snapshot().snapshot_id if table.current_snapshot() else None,
#         #     "execution_time_seconds": [round(elapsed, 2),"seconds"]
#         # }
#         return {
#             "status": "success",
#             # "metadata": metadata,
#             "count": len(scan.to_arrow()),
#             "data": scan.to_arrow().to_pylist(),
#             "status_Code": 200,
#         }
#
#
#     except Exception as e:
#         return {
#             "status": "error",
#             "error_code": "INTERNAL_SERVER_ERROR",
#             "message": f"Error filtering data: {str(e)}",
#             "data": []
#         }
#


class DeleteSnapshotRequest(BaseModel):
    snapshot_id: str

@router.get("/Inspect")
def table_inspect(
    namespace: str = Query(..., description="Namespace (e.g. 'Namespace')"),
    table_name: str = Query(..., description="Table name (e.g. 'Table name')"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    verify_jwt(credentials.credentials)
    try:
        catalog = get_catalog_client()
        table = catalog.load_table((namespace, table_name))

        snapshots = list(table.snapshots())

        snapshot_data = []
        for s in snapshots:
            snapshot_data.append({
                "snapshot_id": getattr(s, "snapshot_id", None),
                "parent_snapshot_id": getattr(s, "parent_snapshot_id", None),
                "timestamp_ms": getattr(s, "timestamp_ms", None),
                "manifest_list": getattr(s, "manifest_list", None),
                "summary": getattr(s, "summary", {})
            })

        return {
            "namespace": namespace,
            "table_name": table.name,
            "records_count": len(snapshots),
            "snapshots": snapshot_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inspect table: {str(e)}")


@router.delete("/DeleteSnapshot")
def delete_snapshot(
    namespace: str = Query(..., description="Namespace (e.g. 'Namespace')"),
    table_name: str = Query(..., description="Table name (e.g. 'Table name')"),
    req: DeleteSnapshotRequest = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    verify_jwt(credentials.credentials)
    try:
        catalog = get_catalog_client()
        table = catalog.load_table((namespace, table_name))

        # Rollback to the snapshot (remove all snapshots after it)
        ops = table.manage_snapshots()
        ops.rollback_to(req.snapshot_id)
        ops.commit()

        return {
            "message": f"Rollback to snapshot {req.snapshot_id} completed successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback: {str(e)}")
########### version 01 ####################
# @router.get("/")
# def dynamic_filter(
#     namespace: str = Query(..., description="Namespace (e.g. 'crm')"),
#     table_name: str = Query(..., description="Table name (e.g. 'serial_number_requests')"),
#     columns: list[str] = Query(..., description="Columns to filter on (comma-separated or multiple query params)"),
#     values: list[str] = Query(..., description="Values to match (in same order as columns)"),
#
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):
#
#     verify_jwt(credentials.credentials)
#     try:
#         verify_jwt(credentials.credentials)
#     except Exception as e:
#         raise HTTPException(
#             status_code=401,
#             detail=f"Invalid token: {str(e)}"
#         )
#
#     start_time = time.time()
#
#     # Handle comma-separated inputs
#     if len(columns) == 1 and ',' in columns[0]:
#         columns = [c.strip() for c in columns[0].split(',')]
#     if len(values) == 1 and ',' in values[0] and len(columns) > 1:
#         values = [v.strip() for v in values[0].split(',')]
#
#     try:
#         # Check lengths
#         if len(columns) != len(values):
#             raise HTTPException(
#                 status_code=400,
#                 detail={
#                     "status": "error",
#                     "error_code": "MISMATCHED_COLUMNS_VALUES",
#                     "message": "Number of columns and values must match",
#                     "data": [],
#                     "status_code": 400
#                 }
#             )
#
#         # Load table
#         # catalog = get_catalog_client()
#         # table = catalog.load_table((namespace, table_name))
#         try:
#             catalog = get_catalog_client()
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail={
#                     "status": "error",
#                     "error_code": "CATALOG_CONNECTION_FAILED",
#                     "message": f"Failed to connect to catalog: {str(e)}",
#                     "data": [],
#                     "status_code": 500
#                 }
#             )
#         try:
#             table = catalog.load_table((namespace, table_name))
#         except Exception as e:
#             raise HTTPException(
#                 status_code=404,
#                 detail={
#                     "status": "error",
#                     "error_code": "TABLE_NOT_FOUND",
#                     "message": f"Table '{namespace}.{table_name}' not found or could not be loaded: {str(e)}",
#                     "data": [],
#                     "status_code": 404
#                 }
#             )
#
#         # Validate columns
#         schema_fields = {f.name for f in table.schema().fields}
#         for col in columns:
#             if col not in schema_fields:
#                 raise HTTPException(
#                     status_code=404,
#                     detail={
#                         "status": "error",
#                         "error_code": "COLUMN_NOT_FOUND",
#                         "message": f"Column '{col}' not found in schema",
#                         "data": [],
#                         "status_code": 404
#                     }
#                 )
#         filters = None
#         for col, val in zip(columns, values):
#             if col == "createdAt" and ',' in val:
#                 start_date, end_date = [v.strip() for v in val.split(',')]
#                 condition = And(
#                     GreaterThanOrEqual(col, start_date),
#                     LessThanOrEqual(col, end_date)
#                 )
#             else:
#                 condition = EqualTo(col, val)
#             filters = condition if filters is None else And(filters, condition)
#
#         # # Apply filter
#         scan = table.scan(row_filter=filters)
#         arrow_table = scan.to_arrow()
#
#         rows = []
#         for batch in arrow_table.to_batches():
#             rows.extend(batch.to_pylist())
#
#         elapsed = round(time.time() - start_time, 2)
#
#         if len(rows) == 0:
#             raise HTTPException(
#                 status_code=404,
#                 detail={
#                     "status": "error",
#                     "error_code": "NO_DATA",
#                     "message": "No data found",
#                     "data": [],
#                     "status_code": 404
#                 }
#             )
#
#         return {
#             "status": "success",
#             "status_code": 200,
#             "count": len(scan.to_arrow()),
#             "data": scan.to_arrow().to_pylist(),
#             "execution_time_seconds": elapsed
#         }
#
#     except HTTPException as http_err:
#         # Re-raise known HTTP errors
#         raise http_err
#
#     except Exception as e:
#         # Catch any unknown errors
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "status": "error",
#                 "error_code": "INTERNAL_ERROR",
#                 "message": str(e),
#                 "data": [],
#                 "status_code": 500
#             }
#         )
####################### version 02 ###############################


# @router.get("/static")
# def static_filter(
#     request: Request,
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, ge=1),
#     page_size: int = Query(50, ge=1, le=500, description="Number of records per page"),
#     startDate: Optional[date] = Query(None, description="Start date for createdAt filter"),
#     endDate: Optional[date] = Query(None, description="End date for createdAt filter"),
#     ticketId: Optional[str] = Query(None, description="Ticket ID"),
#     productName: Optional[str] = Query(None, description="Product Name"),
#     itemCode: Optional[str] = Query(None, description="Item Code"),
#     branchName: Optional[str] = Query(None, description="Branch Name"),
#     credentials: Any = Depends(security)
# ):
#     namespace = "crm"
#     table_name = "serial_number_requests"
#
#     verify_jwt(credentials.credentials)
#     start_time = time.time()
#
#     # Connect to catalog and load table
#     try:
#         catalog = get_catalog_client()
#         table = catalog.load_table((namespace, table_name))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to load table: {str(e)}")
#
#     # Collect filters
#     filters = {}
#     if ticketId:
#         filters["ticketId"] = ticketId
#     if productName:
#         filters["productName"] = productName
#     if itemCode:
#         filters["itemCode"] = itemCode
#     if branchName:
#         filters["branchName"] = branchName
#
#     # Validate filter columns
#     schema_fields = {f.name for f in table.schema().fields}
#     for col in filters:
#         if col not in schema_fields:
#             raise HTTPException(status_code=400, detail=f"Column '{col}' not found in schema")
#
#     # Build filter expression
#     row_filter = None
#     for col, val in filters.items():
#         cond = EqualTo(col, val)
#         row_filter = cond if row_filter is None else And(row_filter, cond)
#
#     # Handle date filters
#     if startDate:
#         cond = GreaterThanOrEqual("createdAt", str(startDate))
#         row_filter = cond if row_filter is None else And(row_filter, cond)
#     if endDate:
#         cond = LessThanOrEqual("createdAt", str(endDate))
#         row_filter = cond if row_filter is None else And(row_filter, cond)
#
#     # Scan table
#     scan = table.scan(row_filter=row_filter)
#     arrow_table = scan.to_arrow()
#     rows = []
#     for batch in arrow_table.to_batches():
#         rows.extend(batch.to_pylist())
#
#     elapsed = round(time.time() - start_time, 2)
#
#     # Pagination
#     # start_idx = (page - 1) * limit
#     # end_idx = start_idx + limit
#     # paged_rows = rows[start_idx:end_idx]
#
#     # ✅ Pagination logic
#     total_count = len(rows)
#     total_pages = (total_count + page_size - 1)
#     start_index = (page - 1) * page_size
#     end_index = start_index + page_size
#     paginated_rows = rows[start_index:end_index]
#
#     elapsed = round(time.time() - start_time, 2)
#
#     # ✅ Build URLs
#     base_url = str(request.url).split("?")[0]  # endpoint path only
#     query_params = dict(request.query_params)
#
#     query_params["page_size"] = str(page_size)
#
#     next_page_url = None
#     prev_page_url = None
#
#     if page < total_pages:
#         query_params["page"] = str(page + 1)
#         next_page_url = f"{base_url}?{query_params}"
#
#     if page > 1:
#         query_params["page"] = str(page - 1)
#         prev_page_url = f"{base_url}?{query_params}"
#
#     return {
#         "status": "success",
#         "status_code": 200,
#         "page": page,
#         "page_size": page_size,
#         "total_pages": total_pages,
#         "next_page_url": next_page_url,
#         "prev_page_url": prev_page_url,
#         "data": paginated_rows,
#         "execution_time_seconds": elapsed
#     }

# @router.get("/GetOne")
# def get_one(
#     namespace: str = Query(..., description="Namespace (bucket name in R2)"),
#     table_name: str = Query(..., description="Table name"),
#     year: Optional[int] = Query(None, description="Year (YYYY)"),
#     month: int = Query(...),
#     day: int = Query(...),
#     ticket_id: str = Query(..., description="Ticket ID"),
# ):
#     r2_client = get_r2_client()
#     key = f"{namespace}/{table_name}/{year}/{month}/{day}/{ticket_id}.json"
#
#     try:
#         obj = r2_client.get_object(Bucket=namespace, Key=key)
#         body = obj["Body"].read().decode("utf-8")
#         return json.loads(body)
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=f"Object not found: {str(e)}")
# from typing import Optional, List
# from pydantic import BaseModel
#
# class RecordModel(BaseModel):
#     ticketId: str
#     createdAt: str
#     mobileNo: Optional[str] = None
#     warehouseCode: Optional[str] = None
#     productName: Optional[str] = None
#     itemCode: Optional[str] = None
#     branchName: Optional[str] = None
#
# @router.get("/GetRecords", response_model=List[RecordModel])
# def get_records(
#     namespace: str = Query(..., description="Namespace (bucket name in R2)"),
#     table_name: str = Query(..., description="Table name"),
#     year: Optional[int] = Query(None, description="Year (YYYY)"),
#     month: Optional[int] = Query(None, description="Month (MM)"),
#     day: Optional[int] = Query(None, description="Day (DD)"),
#     ticket_id: Optional[str] = Query(None, description="Ticket ID"),
#     mobile_no: Optional[str] = Query(None, description="Mobile Number"),
#     warehouse_code: Optional[str] = Query(None, description="Warehouse Code"),
#     product_name: Optional[str] = Query(None, description="Product Name"),
#     item_code: Optional[str] = Query(None, description="Item Code"),
#     branch_name: Optional[str] = Query(None, description="Branch Name"),
# ):
#     r2_client = get_r2_client()
#
#     # Prefix to narrow search (e.g. /namespace/table/year/month/day/)
#     prefix_parts = [table_name]
#     if year: prefix_parts.append(str(year))
#     if month: prefix_parts.append(str(month))
#     if day: prefix_parts.append(str(day))
#
#     prefix = "/".join(prefix_parts)
#     print(ticket_id)
#
#     try:
#         response = r2_client.list_objects_v2(Bucket=namespace, Prefix=prefix)
#         print(response)
#         records = []
#
#         if "Contents" not in response:
#             return []
#
#         for obj in response["Contents"]:
#             key = obj["Key"]
#             file_obj = r2_client.get_object(Bucket=namespace, Key=key)
#             body = file_obj["Body"].read().decode("utf-8")
#             record = json.loads(body)
#
#             # Apply filters
#             if ticket_id and record.get("ticketId") != ticket_id:
#                 continue
#             if mobile_no and record.get("mobileNo") != mobile_no:
#                 continue
#             if warehouse_code and record.get("warehouseCode") != warehouse_code:
#                 continue
#             if product_name and record.get("productName") != product_name:
#                 continue
#             if item_code and record.get("itemCode") != item_code:
#                 continue
#             if branch_name and record.get("branchName") != branch_name:
#                 continue
#
#             records.append(RecordModel(**record))
#             print("data:",records)
#
#         return records
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching records: {str(e)}")


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

class FilterParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-based)")
    limit: Optional[int] = Field(
        None, ge=1, le=MAX_PAGE_SIZE, description="Records per page (optional, defaults to 50, max 500)"
    )
    startDate: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    endDate: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    warehouseCode : Optional[str] = None
    ticketId: Optional[str] = None
    productName: Optional[str] = None
    itemCode: Optional[str] = None
    branchName: Optional[str] = None

@router.get("/filter-data")
def get_filtered_data(
    filters: FilterParams = Depends(),
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify Token
    try:
        verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail={
            "status": "error",
            "error_code": "INVALID_TOKEN",
            "message": str(e),
            "data": [],
            "status_code": 401
        })

    start_time = time.time()
    # namespace, table_name = "crm", "serial_number_requests"
    # namespace, table_name = "crm", "invoice-data02"
    # namespace, table_name = "crm", "invoice"
    # namespace, table_name = "crm", "invoice-day-wise"
    namespace, table_name = "crm", "invoice-month-wise"

    # Load Table
    try:
        catalog = get_catalog_client()
        table = catalog.load_table((namespace, table_name))
    except Exception as e:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "error_code": "TABLE_NOT_FOUND",
            "message": f"Table '{namespace}.{table_name}' not found: {e}",
            "data": [],
            "status_code": 404
        })

    # Build filter expression
    filters_expr = None
    if filters.startDate and filters.endDate:
        filters_expr = And(
            GreaterThanOrEqual("createdAt", filters.startDate),
            LessThanOrEqual("createdAt", filters.endDate),
        )

    for col, val in {
        "ticketId": filters.ticketId,
        "productName": filters.productName,
        "itemCode": filters.itemCode,
        "branchName": filters.branchName,
        "warehouseCode": filters.warehouseCode
    }.items():
        if val:
            cond = EqualTo(col, val)
            filters_expr = cond if filters_expr is None else And(filters_expr, cond)

    # Fetch data
    scan = table.scan(row_filter=filters_expr)
    arrow_table = scan.to_arrow()
    rows = [row for batch in arrow_table.to_batches() for row in batch.to_pylist()]

    # --- Multithreading for batch-to-dict conversion ---
    # def process_batch(batch):
    #     data = batch.to_pylist()
    #     for row in data:
    #         row.pop("raw_json", None)
    #     return data

    # batches = arrow_table.to_batches()
    # results = []
    # with ThreadPoolExecutor(max_workers=8) as executor:  # adjust 8 based on CPU cores
    #     futures = [executor.submit(process_batch, b) for b in batches]
    #     for future in as_completed(futures):
    #         results.extend(future.result())
    #
    # total_count = len(results)

    total_count = len(rows)
    if total_count == 0:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "error_code": "NO_DATA",
            "message": "No data found for given filters",
            "data": [],
            "status_code": 404
        })

    # Pagination
    # effective_limit = min(filters.limit or DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE)
    # total_pages = (total_count + effective_limit - 1) // effective_limit
    # start_idx = (filters.page - 1) * effective_limit
    # end_idx = start_idx + effective_limit
    # paginated_rows = rows[start_idx:end_idx]

    elapsed = round(time.time() - start_time, 2)

    # Build URLs
    # base_url = str(request.url).split("?")[0]
    # query_params = dict(request.query_params)
    #
    # next_page_url, prev_page_url = None, None
    # if filters.page < total_pages:
    #     query_params["page"] = str(filters.page + 1)
    #     next_page_url = f"{base_url}?{urlencode(query_params)}"
    # if filters.page > 1:
    #     query_params["page"] = str(filters.page - 1)
    #     prev_page_url = f"{base_url}?{urlencode(query_params)}"

    # paginated_rows.pop("raw_json",None)
    # print(paginated_rows)
    # print(paginated_rows.keys()[-1])
    # if paginated_rows:  # check list is not empty
    #     last_dict = paginated_rows[-1]  # get last dict
    #     last_key = list(last_dict.keys())[-1]  # get last key
    #     print(last_key)

    # print(list(paginated_rows[-1]))
    # Final Response
    cleaned_rows = []
    # for row in paginated_rows:
    #     if isinstance(row, dict):
    #         row.pop("raw_json", None)  # remove 'raw_json' safely
    #     cleaned_rows.append(row)

    return {
        "status": "success",
        "status_code": 200,
        "execution_seconds_min": round(elapsed / 60, 2),
        # "page": filters.page,
        # "limit": effective_limit,
        # "total_pages": total_pages,
        "total_records": total_count,
        # "next_page_url": next_page_url,
        # "prev_page_url": prev_page_url,
        # "data": cleaned_rows,

    }