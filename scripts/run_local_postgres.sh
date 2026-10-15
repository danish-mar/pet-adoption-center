#!/usr/bin/env bash
set -e

PGDATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.pgdata"
LOG_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/postgres.log"
PORT=5432

action="${1:-start}"

case "$action" in
  start)
    if [ ! -d "$PGDATA_DIR" ]; then
      echo "Initializing PostgreSQL cluster in $PGDATA_DIR..."
      initdb -D "$PGDATA_DIR" -U postgres --auth=trust
    fi

    if pg_isready -p "$PORT" -h 127.0.0.1 >/dev/null 2>&1; then
      echo "PostgreSQL is already running on port $PORT."
      exit 0
    fi

    echo "Starting PostgreSQL on port $PORT..."
    pg_ctl -D "$PGDATA_DIR" -l "$LOG_FILE" -o "-p $PORT -k /tmp" start
    
    # Wait for server to become ready
    for i in {1..10}; do
      if pg_isready -p "$PORT" -h 127.0.0.1 >/dev/null 2>&1; then
        echo "PostgreSQL started successfully on port $PORT."
        exit 0
      fi
      sleep 0.5
    done
    echo "Warning: PostgreSQL failed to respond within 5 seconds. Check $LOG_FILE"
    exit 1
    ;;

  stop)
    echo "Stopping PostgreSQL..."
    if [ -d "$PGDATA_DIR" ]; then
      pg_ctl -D "$PGDATA_DIR" stop -m fast 2>/dev/null || pkill -f "postgres -D $PGDATA_DIR" || true
    fi
    echo "PostgreSQL stopped."
    ;;

  status)
    if pg_isready -p "$PORT" -h 127.0.0.1; then
      echo "PostgreSQL is running and accepting connections."
    else
      echo "PostgreSQL is not responding on port $PORT."
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|status}"
    exit 1
    ;;
esac
