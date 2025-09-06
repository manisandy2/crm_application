from pyiceberg.types import *
import pyarrow as pa
import decimal
import json
import datetime
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import HTTPException

type_mapping = {
    "int": LongType(),
    'bigint': LongType(),
    'varchar': StringType(),
    'char': StringType(),
    'text': StringType(),
    'longtext': StringType(),
    'date': DateType(),
    'datetime': TimestampType(),
    'timestamp': TimestampType(),
    'float': FloatType(),
    'double': DoubleType(),
    'boolean': BooleanType(),
    'tinyint': BooleanType()
}

arrow_mapping = {
    # 'int': pa.int32(),
    "int": pa.int64(),
    'bigint': pa.int64(),
    'varchar': pa.string(),
    'char': pa.string(),
    'text': pa.string(),
    'longtext': pa.string(),
    'date': pa.date32(),
    'datetime': pa.timestamp('ms'),
    'timestamp': pa.timestamp('ms'),
    'float': pa.float32(),
    'double': pa.float64(),
    'boolean': pa.bool_(),
    'tinyint': pa.bool_(),
    'bit': pa.bool_(),
    # 'decimal': lambda p=18, s=6: pa.decimal128(p, s)
    'decimal' : pa.decimal128(18, 6)
}


# def convert_row(row, column_types):
#     converted = []
#     for idx, value in enumerate(row):
#         col_type = column_types[idx]
#
#         try:
#             # DECIMAL handling
#             if col_type.startswith("decimal"):
#                 if value is None:
#                     converted.append(None)
#                 elif isinstance(value, decimal.Decimal):
#                     converted.append(str(value))
#                 elif isinstance(value, (int, float)):
#                     converted.append(str(value))
#                 elif isinstance(value, str):
#                     converted.append(str(decimal.Decimal(value)))
#                 else:
#                     raise TypeError(f"Unexpected type {type(value)} for decimal column")
#
#             # BIT handling (bytes, int, bool, string)
#             elif col_type == "bit":
#                 if value is None:
#                     converted.append(None)
#                 elif isinstance(value, (bytes, bytearray)):
#                     converted.append(int.from_bytes(value, byteorder="big") != 0)
#                 elif isinstance(value, int):
#                     converted.append(value != 0)
#                 elif isinstance(value, bool):
#                     converted.append(value)
#                 elif isinstance(value, str):
#                     v = value.strip().lower()
#                     if v in ("1", "true", "t", "yes", "y"):
#                         converted.append(True)
#                     elif v in ("0", "false", "f", "no", "n"):
#                         converted.append(False)
#                     else:
#                         raise ValueError(f"Cannot interpret string '{value}' as bit/boolean")
#                 else:
#                     raise TypeError(f"Unexpected type {type(value)} for bit column")
#
#             # Default: pass value as is
#             else:
#                 converted.append(value)
#
#         except Exception as e:
#             raise RuntimeError(
#                 f"Error converting column #{idx + 1} (type '{col_type}') value '{value}': {e}"
#             ) from e
#
#     return converted

def convert_row(row,arrow_schema):
    converted = {}
    for field in arrow_schema:
        val = row.get(field.name)
        if pa.types.is_integer(field.type):
            converted[field.name] = int(val) if val is not None else None
        elif pa.types.is_floating(field.type):
            converted[field.name] = float(val) if val is not None else None
        elif pa.types.is_boolean(field.type):
            converted[field.name] = bool(val) if val is not None else None
        else:
            converted[field.name] = str(val) if val is not None else None
    return converted

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="ignore")
        return super().default(obj)



def upload_file(r2_client, bucket, r2_key, body):
    try:
        r2_client.put_object(Bucket=bucket, Key=r2_key, Body=body)
        return r2_key
    except ClientError as e:
        raise HTTPException(status_code=400, detail=f"R2 Client error for {r2_key}: {e.response['Error']['Message']}")

    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"R2 BotoCore error for {r2_key}: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error for {r2_key}: {str(e)}")

from pyiceberg.schema import Schema

def infer_schema_from_record(record: dict):
    """
    Infer PyIceberg and PyArrow schemas from a sample record.

    Args:
        record (dict): Dictionary representing one record with field names and values.

    Returns:
        tuple: (iceberg_schema, arrow_schema)
    """
    iceberg_fields = []
    arrow_fields = []

    for idx, (name, value) in enumerate(record.items(), start=1):
        if isinstance(value, bool):
            ice_type = BooleanType()
            arrow_type = pa.bool_()
        elif isinstance(value, int):
            ice_type = LongType()
            arrow_type = pa.int64()
        elif isinstance(value, float):
            ice_type = DoubleType()
            arrow_type = pa.float64()
        else:
            ice_type = StringType()
            arrow_type = pa.string()

        # Iceberg schema field
        iceberg_fields.append(
            NestedField(field_id=idx, name=name, field_type=ice_type, required=False)
        )

        # Arrow schema field
        arrow_fields.append(pa.field(name, arrow_type, nullable=True))

    iceberg_schema = Schema(*iceberg_fields)
    arrow_schema = pa.schema(arrow_fields)

    return iceberg_schema, arrow_schema

from pyiceberg.exceptions import NoSuchTableError

def get_or_create_table(catalog, table_identifier,iceberg_schema):

    try:
        tbl = catalog.load_table(table_identifier)
        # print(f"✅ Table '{table_identifier}' loaded successfully.")
    except NoSuchTableError:
        tbl = catalog.create_table(table_identifier, schema=iceberg_schema)
        # print(f"📌 Table '{table_identifier}' created successfully.")

    return tbl


from fastapi import HTTPException

def fetch_mysql_data(mysql_creds, dbname: str, start_range: int, end_range: int):

    try:
        description = mysql_creds.get_describe(dbname)
        rows = mysql_creds.get_range(dbname, start_range, end_range)
        return description, rows
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"MySQL fetch error for db={dbname}, range=({start_range}, {end_range}): {str(e)}"
        )


def build_schemas_from_mysql(description, type_mapping, arrow_mapping):
    iceberg_fields = []
    arrow_fields = []

    for idx, column in enumerate(description):
        name = column["Field"]
        col_type = column["Type"].split("(")[0].lower()   # extract base type
        is_nullable = column["Null"].upper() == "YES"

        # MySQL key info (not used yet, but available)
        is_primary = column["Key"] == "PRI"
        is_unique = column["Key"] == "UNI"

        # Map to Iceberg + Arrow
        ice_type = type_mapping.get(col_type, StringType())
        arrow_type = arrow_mapping.get(col_type, pa.string())

        iceberg_fields.append(
            NestedField(
                field_id=idx + 1,
                name=name,
                field_type=ice_type,
                required=not is_nullable
            )
        )
        arrow_fields.append(
            pa.field(
                name,
                arrow_type,
                nullable=is_nullable
            )
        )

    iceberg_schema = Schema(*iceberg_fields)
    arrow_schema = pa.schema(arrow_fields)

    return iceberg_schema, arrow_schema