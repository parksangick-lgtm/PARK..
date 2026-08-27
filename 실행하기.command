#!/bin/bash
cd "$(dirname "$0")" || exit 1

echo "================================"
echo " 유튜브 자동 요약"
echo "================================"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "[오류] 파이썬이 설치되어 있지 않습니다."
  echo "https://www.python.org/downloads/ 에서 설치한 뒤 다시 실행하세요."
  read -r -p "엔터를 누르면 닫힙니다..."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "최초 실행입니다. 준비 중이니 잠시만 기다려 주세요..."
  python3 -m venv .venv || exit 1
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt || exit 1
  echo "준비 완료!"
  echo
fi

if [ ! -f .env ]; then
  echo "[알림] .env 파일이 없습니다."
  echo ".env.example 을 복사해 .env 로 이름을 바꾸고 API 키를 넣어주세요."
  read -r -p "엔터를 누르면 닫힙니다..."
  exit 1
fi

URL="$1"
if [ -z "$URL" ]; then
  read -r -p "요약할 유튜브 주소를 붙여넣고 Enter: " URL
fi
if [ -z "$URL" ]; then
  echo "주소가 입력되지 않았습니다."
  read -r -p "엔터를 누르면 닫힙니다..."
  exit 1
fi

echo
echo "요약 중입니다. 30초 정도 걸립니다..."
echo
./.venv/bin/python src/summarize.py "$URL"

echo
echo "끝났습니다. summaries 폴더를 확인하세요."
read -r -p "엔터를 누르면 닫힙니다..."
