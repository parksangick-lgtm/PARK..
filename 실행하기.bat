@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ================================
echo  유튜브 자동 요약
echo ================================
echo.

rem 파이썬 실행 명령 찾기: py -3 -> py -> python 순서
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (py --version >nul 2>&1 && set "PY=py")
if not defined PY (python --version 2>nul | findstr /r "[0-9]" >nul && set "PY=python")

if not defined PY (
  echo [오류] 파이썬을 찾을 수 없습니다.
  echo https://www.python.org/downloads/ 에서 설치한 뒤 다시 실행하세요.
  echo 설치할 때 "Add python.exe to PATH" 를 반드시 체크하세요.
  pause
  exit /b 1
)

if not exist .venv (
  echo 최초 실행입니다. 준비 중이니 잠시만 기다려 주세요...
  %PY% -m venv .venv || (echo [오류] 준비 실패 & pause & exit /b 1)
  call .venv\Scripts\activate.bat
  python -m pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt || (echo [오류] 설치 실패 & pause & exit /b 1)
  echo 준비 완료!
  echo.
) else (
  call .venv\Scripts\activate.bat
)

if not exist .env (
  echo [알림] .env 파일이 없습니다.
  echo .env.example 파일을 복사해 .env 로 이름을 바꾸고 API 키를 넣어주세요.
  pause
  exit /b 1
)

set "URL=%~1"
if "%URL%"=="" set /p URL=요약할 유튜브 주소를 붙여넣고 Enter: 
if "%URL%"=="" (echo 주소가 입력되지 않았습니다. & pause & exit /b 1)

echo.
echo 요약 중입니다. 30초 정도 걸립니다...
echo.
python src\summarize.py "%URL%"

echo.
echo 끝났습니다. summaries 폴더를 확인하세요.
pause
