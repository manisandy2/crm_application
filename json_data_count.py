import json


path = r"json_data_backup/Transaction_pos_202510071301.json"


with open(path, 'r') as file:
    data = json.load(file)




# # Transaction_pos is a list
# transactions = data.get("Transaction_pos", [])
#
# # Get the count of items
# print("Total transactions:", len(transactions))
#
# # If you want to count how many have pri_id
# pri_ids = [t["pri_id"] for t in transactions if "pri_id" in t]
# print("Total pri_id count:", len(pri_ids))


transactions = data.get("Transaction_pos",'')
import time
count = 1
for transaction in transactions:
    transaction["created_at"] = "2025-12-01"

    # print(transaction.append("created_at"=2025-12-01))
    count += 1
    if count == 5:
        break
    time.sleep(5)
    print(transaction)