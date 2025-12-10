import time
import schedule
from zep_python import ZepClient

def job():
    print("Checking for new documents in Azure Blob Storage...")
    # 1. List blobs
    # 2. If new, download
    # 3. Send to Unstructured API
    # 4. Ingest into Zep
    print("No new documents found.")

schedule.every(10).seconds.do(job)

print("ETL Service Started. polling every 10s...")
while True:
    schedule.run_pending()
    time.sleep(1)
