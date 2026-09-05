#!/usr/bin/env bash
# raw-guard — Raw 영역 불변성 보증 장치
#
#   bash tools/raw-guard.sh seal    새 원본을 지문(fingerprint)에 등록
#   bash tools/raw-guard.sh verify  원본이 변경·삭제되지 않았는지 대조
#
# 지문 = SHA256 해시. 파일이 한 글자라도 바뀌면 값이 달라집니다.
cd "$(dirname "$0")/.." || exit 1
M="raw/.manifest"

list_raw() { find raw -type f ! -name '.manifest' | LC_ALL=C sort; }

case "${1:-verify}" in
  seal)
    : > "$M"
    list_raw | while read -r f; do
      printf '%s  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$f" >> "$M"
    done
    echo "✅ 원본 $(wc -l < "$M")건을 지문에 등록했습니다. ($M)"
    ;;
  verify)
    [ -f "$M" ] || { echo "  ℹ️  지문 파일이 없습니다. 먼저 'seal' 을 실행하세요."; exit 0; }
    FAIL=0
    # 1) 변경·삭제 검사
    while read -r want f; do
      if [ ! -e "$f" ]; then
        echo "  🚨 삭제됨 → $f"; FAIL=1
      else
        got=$(sha256sum "$f" | cut -d' ' -f1)
        [ "$got" = "$want" ] || { echo "  🚨 내용이 변경됨 → $f"; FAIL=1; }
      fi
    done < "$M"
    # 2) 미등록(새로 들어온) 파일 검사
    list_raw | while read -r f; do
      grep -q "  $f\$" "$M" || echo "  ➕ 미등록 원본 → $f  (ingest 후 seal 필요)"
    done
    [ "$FAIL" -eq 0 ] && echo "  ✅ 등록된 원본이 모두 원형 그대로입니다."
    exit $FAIL
    ;;
  *) echo "사용법: bash tools/raw-guard.sh [seal|verify]"; exit 2 ;;
esac
