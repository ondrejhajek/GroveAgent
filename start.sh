#!/bin/bash

set -e

echo "[INFO] Starting app..."

if [ ! -f ".env" ]; then
  echo "[ERROR] .env file not found"
  exit 1
fi

set -a
source .env
set +a

if [ -z "$APP_PORT" ]; then
  echo "[ERROR] APP_PORT is not set in .env"
  exit 1
fi

uvicorn main:app --host 0.0.0.0 --port "$APP_PORT"