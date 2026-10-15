#!/usr/bin/env bash
# Geometry is generated in Python; ClickHouse alone renders and encodes the PNG.
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

width="${1:-2400}"
height="${2:-1500}"
samples="${3:-4}"
output="${4:-images/pelican_river_eclipse.png}"
for value in "$width" "$height" "$samples"; do
    if [[ ! "$value" =~ ^[1-9][0-9]*$ ]]; then
        printf 'Width, height and samples must be positive integers.\n' >&2
        exit 2
    fi
done
if (( samples > 64 )); then
    printf 'Use 1–64 samples per pixel (4 recommended).\n' >&2
    exit 2
fi
command -v clickhouse >/dev/null
command -v python3 >/dev/null
mkdir -p -- "$(dirname -- "$output")"
temporary_sql="$(mktemp "$repo_dir/queries/.pelican.XXXXXX.sql")"
temporary_png="$(mktemp "${output}.XXXXXX")"
trap 'rm -f -- "$temporary_sql" "$temporary_png"' EXIT

python3 generators/gen_pelican.py > "$temporary_sql"
mv -- "$temporary_sql" queries/pelican_river_eclipse.sql
printf 'ClickHouse → %s × %s, %s samples/pixel → %s\n' "$width" "$height" "$samples" "$output" >&2
clickhouse local \
    --max_query_size 10000000 \
    --output_format_image_width "$width" \
    --output_format_image_height "$height" \
    --param_SAMPLES "$samples" \
    --queries-file queries/pelican_river_eclipse.sql > "$temporary_png"
mv -- "$temporary_png" "$output"
printf 'PNG completed: %s\n' "$output" >&2
