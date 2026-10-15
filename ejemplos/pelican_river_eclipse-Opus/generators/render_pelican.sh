#!/usr/bin/env bash
# Generate the SQL, then let ClickHouse compute and encode every PNG pixel.
# Usage: bash generators/render_pelican.sh [W] [H] [SAMPLES] [OUT.png]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
W=${1:-2400}
H=${2:-1500}
SAMPLES=${3:-4}
OUT=${4:-"$ROOT/images/pelican_river_eclipse.png"}

for value in "$W" "$H" "$SAMPLES"; do
    if [[ ! "$value" =~ ^[1-9][0-9]*$ ]]; then
        echo "Width, height and SAMPLES must be positive integers." >&2
        exit 2
    fi
done

SQL="$ROOT/queries/pelican_river_eclipse.sql"
python3 "$HERE/gen_pelican.py" > "$SQL"
mkdir -p "$(dirname "$OUT")"
TEMP_PNG="$(mktemp "${OUT}.tmp.XXXXXX")"
trap 'rm -f "$TEMP_PNG"' EXIT

echo "Rendering ${W}x${H}, ${SAMPLES} samples per pixel with ClickHouse..." >&2
clickhouse local \
    --output_format_image_width "$W" \
    --output_format_image_height "$H" \
    --param_SAMPLES "$SAMPLES" \
    --queries-file "$SQL" > "$TEMP_PNG"
mv "$TEMP_PNG" "$OUT"
echo "PNG: $OUT" >&2
