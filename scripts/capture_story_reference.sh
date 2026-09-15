#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <incident-id> [message]" >&2
  exit 2
fi

INCIDENT_ID="$1"
MESSAGE="${2:-Tell the incident story for ${INCIDENT_ID}.}"
API_BASE="${API_BASE:-http://127.0.0.1:8000}"
SESSION_ID="${SESSION_ID:-story-reference}"
OUT_ROOT="${OUT_ROOT:-docs/storyteller-references}"

SAFE_ID="$(printf '%s' "${INCIDENT_ID}" | tr '/:' '__' | tr -cd 'A-Za-z0-9._-')"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${OUT_ROOT}/${SAFE_ID}/${STAMP}"
mkdir -p "${OUT_DIR}"

URL="${API_BASE}/api/incidents/${INCIDENT_ID}/ask"
PAYLOAD_FILE="${OUT_DIR}/request.json"
RESPONSE_FILE="${OUT_DIR}/response.json"
ANSWER_FILE="${OUT_DIR}/answer.md"
STORY_FILE="${OUT_DIR}/story.json"
SPOKEN_FILE="${OUT_DIR}/spoken.txt"
NARRATIVE_FILE="${OUT_DIR}/narrative.json"
VISUAL_FILE="${OUT_DIR}/visual_explanation.json"
COMMAND_FILE="${OUT_DIR}/command.txt"

python3 - "$SESSION_ID" "$MESSAGE" > "${PAYLOAD_FILE}" <<'PY'
import json
import sys

session_id, message = sys.argv[1], sys.argv[2]
print(json.dumps({"session_id": session_id, "message": message}, separators=(",", ":")))
PY

cat > "${COMMAND_FILE}" <<EOF
API_BASE=${API_BASE} SESSION_ID=${SESSION_ID} OUT_ROOT=${OUT_ROOT} \\
scripts/capture_story_reference.sh '${INCIDENT_ID}' '${MESSAGE}'

curl -sS -X POST '${URL}' \\
  -H 'Content-Type: application/json' \\
  -d @'${PAYLOAD_FILE}'
EOF

curl -sS -X POST "${URL}" \
  -H 'Content-Type: application/json' \
  -d @"${PAYLOAD_FILE}" \
  > "${RESPONSE_FILE}"

python3 - "${RESPONSE_FILE}" "${ANSWER_FILE}" "${STORY_FILE}" "${SPOKEN_FILE}" "${NARRATIVE_FILE}" "${VISUAL_FILE}" <<'PY'
import json
import sys
from pathlib import Path

response_path = Path(sys.argv[1])
answer_path = Path(sys.argv[2])
story_path = Path(sys.argv[3])
spoken_path = Path(sys.argv[4])
narrative_path = Path(sys.argv[5])
visual_path = Path(sys.argv[6])

data = json.loads(response_path.read_text(encoding="utf-8"))
answer_path.write_text(data.get("answer", ""), encoding="utf-8")
story_path.write_text(json.dumps(data.get("story", {}), indent=2, sort_keys=True) + "\n", encoding="utf-8")
spoken_path.write_text((data.get("spoken_answer") or "") + "\n", encoding="utf-8")
narrative_path.write_text(json.dumps(data.get("narrative", {}), indent=2, sort_keys=True) + "\n", encoding="utf-8")
visual_path.write_text(json.dumps(data.get("visual_explanation", {}), indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

echo "Stored storyteller reference bundle: ${OUT_DIR}"
echo "- ${ANSWER_FILE}"
echo "- ${RESPONSE_FILE}"
echo "- ${STORY_FILE}"
echo "- ${SPOKEN_FILE}"
echo "- ${NARRATIVE_FILE}"
echo "- ${VISUAL_FILE}"
