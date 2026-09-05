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

echo; echo "[3] 5-필터 기재 및 값 유효성"
targets | while read -r f; do
  fl=$(grep -m1 '^filters:' "$f" | sed 's/^filters:[[:space:]]*//')
  if [ -z "$fl" ] || [ "$fl" = "[]" ]; then
    note "$f : filters 비어있음 → wiki 승격 자격 없음"
  else
    # 1~5 이외의 숫자가 있으면 잘못된 필터 번호
    bad=$(echo "$fl" | tr -cd '0-9' | fold -w1 | grep -vE '^[1-5]$' | head -1)
    [ -n "$bad" ] && note "$f : 잘못된 필터 번호 '$bad' (1~5만 허용)"
  fi
  # 판정 근거가 적혀 있는지
  grep -q '^filter_reason:' "$f" || note "$f : filter_reason 없음 → 왜 통과했는지 한 줄 필요"
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

echo; echo "[7] 중복 정보 (제목 + 본문 문장 겹침)"
targets | xargs grep -h '^title:' 2>/dev/null | sort | uniq -d | while read -r t; do
  note "제목 중복 → $t"
done
python3 tools/dupcheck.py

echo; echo "[8] 모순 (미판정 상태로 남은 것)"
grep -rn '미판정' wiki/ 2>/dev/null | while IFS= read -r h; do note "$h"; done
echo "  (검출 없으면 통과)"

echo; echo "[9] 상호참조 누락 (위키링크가 하나도 없는 노트 = 고립된 지식)"
find wiki -name "*.md" ! -name "README.md" | while read -r f; do
  grep -q '\[\[' "$f" || note "$f : 다른 노트와 연결 없음"
done; echo "  (검출 없으면 통과)"

echo; echo "[10] 조사 공백 (아직 못 채운 항목)"
find wiki -name "*.md" ! -name "README.md" | while read -r f; do
  n=$(grep -c '^\s*- \[ \]' "$f")
  [ "$n" -gt 0 ] && echo "  📋 $f : 미확인 $n 건"
done; echo "  (조사가 필요한 항목입니다 — 경고 아님)"

echo; echo "[11] Raw 불변성 (원본이 변경·삭제되지 않았는가)"
bash tools/raw-guard.sh verify | sed 's/^/  /'

echo; echo "[12] conversations → wiki 원문 복사 (재작성 없이 복붙했는가)"
for w in $(find wiki -name "*.md" ! -name "README.md"); do
  for c in $(find conversations -name "*.md" ! -name "README.md"); do
    dup=$(grep -Fxf "$c" "$w" 2>/dev/null | grep -vE '^\s*$|^\||^#|^-{3}|^>' | awk 'length($0)>30' | wc -l)
    [ "$dup" -ge 3 ] && note "$w ← $c : 동일 문장 ${dup}줄 (재작성 필요)"
  done
done; echo "  (검출 없으면 통과)"

echo; echo "=== 끝. 수정은 사람이 승인한 뒤에만 진행합니다. ==="
