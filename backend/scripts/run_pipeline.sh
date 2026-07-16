
set -euo pipefail

CSV_DIR="${1:-/app/data}"

echo "=== [1/3] Ingesting data from ${CSV_DIR} ==="
python -m app.ml.data_ingestion --csv-dir "${CSV_DIR}"

echo "=== [2/3] Training models ==="
python -m app.ml.train

echo "=== [3/3] Backfilling predictions and alerts ==="
python -m app.ml.backfill_predictions

echo "=== Pipeline complete. API is ready to serve real predictions. ==="
