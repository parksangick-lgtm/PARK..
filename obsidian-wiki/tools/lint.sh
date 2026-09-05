#!/usr/bin/env bash
# lint — 위키 건강검진. 보고만 하고 파일은 절대 고치지 않습니다.
# 사용법:  bash tools/lint.sh
cd "$(dirname "$0")/.." || exit 1
WARN=0
note() { echo "  ⚠️  $*"; WARN=$((WARN+1)); }
# 백틱 코드 표기와 따옴표 안의 예시 문구를 지운다 (규칙 설명문을 오탐하지 않기 위함)
strip() { sed 's/`[^`]*`//g; s/"[^"]*"//g' "$1"; }


# 검사 대상: wiki/ 의 실제 노트 + 최상위 index/log (README·템플릿 제외)
targets() { find wiki -name "*.md" ! -name "README.md"; echo "index.md"; echo "log.md"; }

echo "=== lint: 위키 건강검진 ==="

echo; echo "[1] 검증 안 된 추측이 wiki 에 있는가"
# 백틱(`) 과 따옴표 안의 예시 문구는 규칙 설명이므로 검사에서 제외한다
targets | while read -r f; do
  strip "$f" | grep -nE '추정입니다|아마도|~일 듯|확실하지 않' | while IFS= read -r hit; do
    note "$f : $hit"
  done
done; echo "  (검출 없으면 통과)"

echo; echo "[2] 출처(source) 없는 결정"
targets | while read -r f; do
  src=$(grep -m1 '^source:' "$f" | sed 's/^source:[[:space:]]*//')
  if   [ -z "$src" ];                        then note "$f : source 비어있음"
  elif [ ! -e "$src" ] && [ ! -e "../$src" ]; then note "$f : source 경로 없음 → $src"; fi
done; echo "  (검출 없으면 통과)"

echo; echo "[3] 5-필터 미기재"
targets | while read -r f; do
  fl=$(grep -m1 '^filters:' "$f" | sed 's/^filters:[[:space:]]*//')
  { [ -z "$fl" ] || [ "$fl" = "[]" ]; } && note "$f : filters 비어있음 → 5-필터 재적용 필요"
done; echo "  (검출 없으면 통과)"

echo; echo "[4] 오래된 규칙 (updated 기준 180일 초과)"
CUT=$(date -d '180 days ago' +%Y-%m-%d 2>/dev/null || date -v-180d +%Y-%m-%d)
targets | while read -r f; do
  u=$(grep -m1 '^updated:' "$f" | sed 's/^updated:[[:space:]]*//')
  s=$(grep -m1 '^status:'  "$f" | sed 's/^status:[[:space:]]*//')
  [ -n "$u" ] && [ "$u" \< "$CUT" ] && [ "$s" = "확정" ] && note "$f : $u 이후 미갱신 → 재확인 요청"
done; echo "  (기준일 $CUT / 검출 없으면 통과)"

echo; echo "[5] 끊어진 위키링크"
find . -name "*.md" | while read -r f; do strip "$f"; done \
  | grep -o '\[\[[^]]\+\]\]' \
  | sed 's/\[\[//; s/\]\]//; s/\\|.*//; s/|.*//' | sed 's/[[:space:]]*$//' \
  | grep -v '^$' | sort -u | while read -r l; do
      [ -e "$l.md" ] || [ -e "$l" ] || note "링크 대상 없음 → [[$l]]"
    done; echo "  (검출 없으면 통과)"

echo; echo "[6] 고아 노트 (index.md 에서 링크 안 됨)"
find wiki -name "*.md" ! -name "README.md" | while read -r f; do
  base="${f%.md}"
  grep -q "$base" index.md || note "$f : index.md 에 등록 안 됨"
done; echo "  (검출 없으면 통과)"

echo; echo "[7] 중복 제목"
targets | xargs grep -h '^title:' 2>/dev/null | sort | uniq -d | while read -r t; do
  note "제목 중복 → $t"
done; echo "  (검출 없으면 통과)"

echo; echo "=== 끝. 수정은 사람이 승인한 뒤에만 진행합니다. ==="
