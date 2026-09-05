@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ================================
echo  옵시디언 저장 스킬 설치
echo ================================
echo.
echo 스킬을 내 컴퓨터 전체에 복사합니다.
echo 그러면 홈페이지 만드는 폴더에서도 "5번" 이 작동합니다.
echo.

set "DEST=%USERPROFILE%\.claude\skills"
if not exist "%DEST%" mkdir "%DEST%"

xcopy /E /I /Y ".claude\skills" "%DEST%" >nul
if errorlevel 1 (
  echo [오류] 스킬 복사에 실패했습니다.
  pause
  exit /b 1
)
copy /Y "src\obsidian_save.py" "%DEST%\obsidian-save\obsidian_save.py" >nul

echo 스킬 복사 완료: %DEST%
echo.

rem 파이썬 실행 명령 찾기: py -3 -> py -> python 순서
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (py --version >nul 2>&1 && set "PY=py")
if not defined PY (python --version 2>nul | findstr /r "[0-9]" >nul && set "PY=python")

if not defined PY (
  echo [알림] 파이썬이 없어서 볼트 경로 등록은 건너뜁니다.
  echo https://www.python.org/downloads/ 에서 설치한 뒤 다시 실행하세요.
  pause
  exit /b 0
)

set "VAULT=%~1"
if "%VAULT%"=="" (
  echo 옵시디언 볼트 폴더 경로를 알려주세요.
  echo 폴더를 열고 주소창을 복사하거나, 폴더를 이 창에 끌어다 놓으면 됩니다.
  set /p VAULT=경로 ^(건너뛰려면 그냥 Enter^): 
)

if "%VAULT%"=="" (
  echo.
  echo 볼트 경로 등록은 건너뛰었습니다. 나중에 등록하려면:
  echo   %PY% src\obsidian_save.py --set-vault "볼트폴더경로"
  pause
  exit /b 0
)

echo.
%PY% src\obsidian_save.py --set-vault "%VAULT%"

echo.
echo 설치가 끝났습니다.
echo 이제 홈페이지 작업 폴더에서 "5번" 이라고 말하면 옵시디언에 저장됩니다.
pause
