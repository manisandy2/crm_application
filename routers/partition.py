from fastapi import APIRouter,Query
from core.catalog_client import get_catalog_client

router = APIRouter(prefix="/partition", tags=["partition"])

@router.get("/filter")
def get_partition(
    namespace: str = Query(..., description="Namespace (e.g. 'Namespace')"),
    table_name: str = Query(..., description="Table name (e.g. 'Table name')")
):

    catalog = get_catalog_client()
    table = catalog.load_table(f"{namespace}.{table_name}")

    # Partition spec
    print("Partition Spec:", table.spec())

    # Partition summary
    # for p in table.scan().plan_files():
    #     print(p.partition)
    # return table.scan().plan_files()
    # return table.schema()
    # return table.spec()
    # for task in table.scan().plan_files():
    #     print("path:",task.file.file_path)
    #     print("record:",task.file.record_count)
    #     print("partition:",task.file.partition)
    return table.scan().plan_files()