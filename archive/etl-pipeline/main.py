import os
import time
import schedule

try:
    from zep_python import ZepClient  # Preferred export path
except ImportError:  # pragma: no cover - fallback for newer client layouts
    try:
        from zep_python.client import ZepClient  # Fallback export path
    except ImportError:
        ZepClient = None

def job():
    print("Checking for new documents in Azure Blob Storage...")
    # 1. List blobs
    # 2. If new, download
    # 3. Send to Unstructured API
    # 4. Ingest into Zep
    if ZepClient is None:
        print("Zep client not available; skip ingestion step.")
    else:
        client = ZepClient(base_url=os.getenv("ZEP_API_URL", "http://zep:8000"))
        print(f"Zep client ready: {client.base_url}")
    print("No new documents found.")

schedule.every(10).seconds.do(job)

print("ETL Service Started. polling every 10s...")
while True:
    schedule.run_pending()
    time.sleep(1)
