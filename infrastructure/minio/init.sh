#!/bin/sh
set -e
mc alias set local http://minio:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
mc mb --ignore-existing local/logisense-documents
mc mb --ignore-existing local/logisense-reports
mc mb --ignore-existing local/logisense-backups
mc policy set public local/logisense-reports
echo "MinIO buckets initialized."
