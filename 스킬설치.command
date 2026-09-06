#!/bin/bash
cd "$(dirname "$0")" || exit 1

echo "================================"
echo " 옵시디언 저장 스킬 설치"
echo "================================"
echo
echo "스킬을 내 컴퓨터 전체에 복사합니다."
echo "그러면 홈페이지 만드는 폴더에서도 \"5번\" 이 작동합니다."
echo

DEST="$HOME/.claude/skills"
mkdir -p "$DEST" || exit 1

cp -R .claude/skills/. "$DEST/" || {
  echo "[오류] 스킬 복사에 실패했습니다."
  read -r -p "엔터를 누르면 닫힙니다..."
  exit 1
}
cp src/obsidian_save.py "$DEST/obsidian-save/obsidian_save.py" || exit 1

echo "스킬 복사 완료: $DEST"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "[알림] 파이썬이 없어서 볼트 등록은 건너뜁니다."
  echo "파이썬을 설치한 뒤 이 파일을 다시 실행하세요."
  read -r -p "엔터를 누르면 닫힙니다..."
  exit 0
fi

echo "옵시디언 볼트를 찾는 중입니다..."
echo

if python3 src/obsidian_save.py --set-vault auto; then
  echo
  echo "설치가 끝났습니다."
  echo "이제 홈페이지 작업 폴더에서 \"5번\" 이라고 말하면 옵시디언에 저장됩니다."
  read -r -p "엔터를 누르면 닫힙니다..."
  exit 0
fi

echo
echo "자동으로 찾지 못했습니다. 볼트 폴더 경로를 직접 알려주세요."
echo "(옵시디언 왼쪽 아래 볼트 이름 클릭 -> \"다른 보관소 열기\" 에서 경로를 볼 수 있습니다)"
echo "(또는 볼트 폴더를 이 창에 끌어다 놓으세요)"
read -r -p "경로 (건너뛰려면 그냥 Enter): " VAULT

if [ -z "$VAULT" ]; then
  echo
  echo "볼트 등록은 건너뛰었습니다. 나중에 등록하려면:"
  echo "  python3 src/obsidian_save.py --set-vault \"볼트폴더경로\""
  read -r -p "엔터를 누르면 닫힙니다..."
  exit 0
fi

echo
python3 src/obsidian_save.py --set-vault "$VAULT"

echo
echo "설치가 끝났습니다."
echo "이제 홈페이지 작업 폴더에서 \"5번\" 이라고 말하면 옵시디언에 저장됩니다."
read -r -p "엔터를 누르면 닫힙니다..."
