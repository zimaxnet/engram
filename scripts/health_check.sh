#!/bin/bash
URL="$1"
RETRIES=30
WAIT=10

echo "Checking health of $URL..."
for i in $(seq 1 $RETRIES); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health")
  if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Health check passed!"
    exit 0
  fi
  echo "Attempt $i/$RETRIES: Got $HTTP_CODE. Retrying in $WAIT seconds..."
  sleep $WAIT
done

echo "❌ Health check failed after $RETRIES attempts."
exit 1
