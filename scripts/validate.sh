#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="logs"
HTML_LOG="${LOG_DIR}/w3c-html.log"
CSS_LOG="${LOG_DIR}/w3c-css.log"

mkdir -p "$LOG_DIR"
: > "$HTML_LOG"
: > "$CSS_LOG"

echo "Validando HTML con html-validator..."
while IFS= read -r file; do
  echo "### $file" >> "$HTML_LOG"
  npx html-validator-cli --file "$file" --format text --verbose >> "$HTML_LOG" 2>&1 || true
  echo "" >> "$HTML_LOG"
done < <(find templates -type f -name "*.html")

echo "Validando CSS con w3c-css-validator..."
while IFS= read -r file; do
  echo "### $file" >> "$CSS_LOG"
  npx css-validator "$file" >> "$CSS_LOG" 2>&1 || true
  echo "" >> "$CSS_LOG"
done < <(find static/css -type f -name "*.css")

echo "Listo. Revisa ${HTML_LOG} y ${CSS_LOG}."
