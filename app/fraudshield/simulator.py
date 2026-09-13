import os
import random
import time
import json
from datetime import datetime
from decimal import Decimal
from urllib.error import URLError
from urllib.request import Request, urlopen

INTERVAL = float(os.getenv("TXN_INTERVAL_SECONDS", "3"))
BACKEND_URL = os.getenv("BACKEND_URL", "http://api:8000")
CITIES = ["Chennai", "Mumbai", "Delhi", "Bengaluru", "Hyderabad"]
MERCHANTS = ["Amazon", "Flipkart", "Swiggy", "BookMyShow", "Reliance Digital"]
USERS = ["U001", "U002", "U003", "U004", "U005"]


def make_transaction(txn_id, user_id, amount, city, merchant, txn_time):
    return {"txn_id": txn_id, "user_id": user_id, "amount": round(amount, 2), "city": city, "merchant": merchant, "txn_time": txn_time}


def random_transaction(txn_id):
    user_id = random.choice(USERS)
    amount = random.lognormvariate(6.5, 0.65)
    city = random.choice(CITIES)
    merchant = random.choice(MERCHANTS)

    # Inject occasional random scenarios so a fresh demo produces meaningful alerts.
    anomaly = random.choices(["normal", "high_amount", "new_merchant"], weights=[0.88, 0.08, 0.04])[0]
    if anomaly == "high_amount":
        amount *= random.uniform(8, 20)
    elif anomaly == "new_merchant":
        merchant = f"New Merchant {random.randint(1, 999)}"

    return make_transaction(txn_id, user_id, amount, city, merchant, datetime.now())


def run():
    txn_id = random.randint(1000, 9999)
    while True:
        transaction = random_transaction(txn_id)
        try:
            payload = dict(transaction)
            payload["amount"] = str(Decimal(str(payload["amount"])))
            request = Request(
                f"{BACKEND_URL}/api/v1/transactions",
                data=json.dumps(payload, default=str).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=10) as response:
                response.read()
            print(f"Inserted {transaction['txn_id']} for {transaction['user_id']}", flush=True)
        except (URLError, TimeoutError, OSError) as error:
            print(f"Insert failed: {error}", flush=True)
        txn_id += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    run()
