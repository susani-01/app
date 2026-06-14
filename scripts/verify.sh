#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"

echo "Verifying API at ${BASE_URL}..."

check_json() {
  local path="$1"
  local expected_status="$2"
  local body
  body="$(curl -fsS "${BASE_URL}${path}")"
  python3 -c "
import json, sys
body = json.loads(sys.argv[1])
assert body.get('status') == sys.argv[2], body
" "$body" "$expected_status"
  echo "OK ${path}"
}

check_json "/health" "success"
check_json "/ready" "success"
check_json "/work_division" "success"
check_json "/classification?cnstwk_div_cd=A" "success"
curl -fsS -G "${BASE_URL}/item" \
  --data-urlencode "cnstwk_div_cd=A" \
  --data-urlencode "q=가설" \
  --data-urlencode "size=2" | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('status') == 'success', body
"
echo "OK /item search"
check_json "/item/AAA162303500" "success"

not_found="$(curl -fsS "${BASE_URL}/item/NOT_A_REAL_CODE")"
python3 -c "
import json, sys
body = json.loads(sys.argv[1])
assert body['status'] == 'failure'
" "$not_found"
echo "OK /item/{code} not-found envelope"

curl -fsS -o /dev/null "${BASE_URL}/openapi.json"
echo "OK /openapi.json"

curl -fsS -o /dev/null "${BASE_URL}/docs"
echo "OK /docs"

echo "All smoke checks passed."
