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