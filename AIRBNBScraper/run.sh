#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/app"
LOG_DIR="/var/log"
OUT_DIR="/out"

# default knobs (can be overridden with envs)
: "${HEADLESS:=1}"
: "${WINDOW_DAYS:=14}"
: "${EMAIL_NAME:=Client}"
: "${TZ:=America/Phoenix}"

# ensure dirs
mkdir -p "$LOG_DIR" "$OUT_DIR"

# If you pass any args to /run.sh, we do a one-shot run and exit.
if [ "$#" -gt 0 ]; then
  echo "One-shot mode. Args: $*"
  cd "$APP_DIR"
  # Expecting flags like: --start YYYY-MM-DD --days N --headless true|false
  exec /usr/local/bin/python -u AirBNBScraper.py "$@"
fi

# CRON MODE
echo "Container timezone: $(cat /etc/timezone 2>/dev/null || echo "$TZ")"

# write crontab from file (already copied in Dockerfile)
echo "# ===== cron/airbnb.crontab ====="
cat /etc/cron.d/airbnb
echo

# register crontab
crontab /etc/cron.d/airbnb

echo "Starting cron..."
exec cron -f

