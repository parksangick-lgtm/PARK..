#!/usr/bin/env bash
# promote-check — wiki 승격 관문
#
#   bash tools/promote-check.sh <노트파일>
#
# wiki/ 에 넣기 **전에** 돌립니다. 통과(0)해야만 승격할 수 있습니다.
# 하나라도 걸리면 차단(1)하고, 어디로 보내야 하는지 알려줍니다.
cd "$(dirname "$0")/.." || exit 1
F="$1"
[ -f "$F" ] || { echo "사용법: bash tools/promote-check.sh <노트파일>"; exit 2; }

BLOCK=0
fail() { echo "  ❌ $1"; [ -n "$2" ] && echo "     → $2"; BLOCK=1; }
pass() { echo "  ✅ $1"; }

echo "=== wiki 승격 관문: $F ==="
echo
echo "[1단계] 승격 금지 목록 대조"

# 검증되지 않은 추측
if sed 's/`[^`]*`//g; s/"[^"]*"//g' "$F" | grep -qE '추정입니다|아마도|~일 듯|확실하지 않|것 같습니다'; then
  fail "검증되지 않은 추측이 있습니다" "conversations/ 에 '> 추정입니다' 를 붙여 남기세요"
else pass "추측 표현 없음"; fi

# 대화 원문 복붙
DUP=0
for c in conversations/*.md; do
  [ -e "$c" ] || continue
  n=$(grep -Fxf "$c" "$F" 2>/dev/null | grep -vE '^\s*$|^\||^#|^-{3}|^>' | awk 'length($0)>30' | wc -l)
  [ "$n" -ge 3 ] && { DUP=1; fail "대화 원문을 복사했습니다 ($c 와 ${n}줄 동일)" "요약·재작성 후 다시 시도하세요"; }
done
[ "$DUP" -eq 0 ] && pass "대화 복붙 아님"

echo
echo "[2단계] 5-필터 판정 기록"

FL=$(grep -m1 '^filters:' "$F" | sed 's/^filters:[[:space:]]*//')
if [ -z "$FL" ] || [ "$FL" = "[]" ]; then
  fail "filters 가 비어 있습니다" "5개 질문 중 어느 것도 통과 못 했다면 conversations/ 로 보내세요"
else
  BAD=$(echo "$FL" | tr -cd '0-9' | fold -w1 | grep -vE '^[1-5]$' | head -1)
  [ -n "$BAD" ] && fail "잘못된 필터 번호 '$BAD' (1~5만 허용)" || pass "통과 필터: $FL"
fi

grep -q '^filter_reason:[[:space:]]*[^[:space:]]' "$F" \
  && pass "판정 근거 기재됨" \
  || fail "filter_reason 이 비어 있습니다" "왜 그 필터를 통과했는지 한 줄 적으세요"

echo
echo "[3단계] 출처"

SRC=$(grep -m1 '^source:' "$F" | sed 's/^source:[[:space:]]*//')
if [ -z "$SRC" ]; then
  fail "source 가 없습니다" "Wiki 는 Raw 없이 존재할 수 없습니다. 근거 파일을 지정하세요"
elif [ ! -e "$SRC" ] && [ ! -e "../$SRC" ] && ! echo "$SRC" | grep -qE '^https?://'; then
  fail "source 경로가 존재하지 않습니다: $SRC" "먼저 ingest 로 원본을 넣으세요"
else pass "출처: $SRC"; fi

echo
if [ "$BLOCK" -eq 0 ]; then
  echo "🟢 승격 가능 — wiki/ 로 옮겨도 됩니다."
else
  echo "🔴 승격 차단 — 위 항목을 고치거나 conversations/ 에만 남기세요."
fi
exit "$BLOCK"
