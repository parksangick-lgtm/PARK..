# 옵시디언 저장 스킬 설치 (윈도우)
#
# 사용법 - PowerShell 창에 아래 한 줄을 붙여넣고 Enter:
#   irm https://raw.githubusercontent.com/parksangick-lgtm/PARK../main/install.ps1 | iex
#
# 하는 일: 최신 파일 내려받기 -> 스킬을 홈 폴더에 복사 -> 옵시디언 볼트 자동 등록

$ErrorActionPreference = "Stop"

# 옛 윈도우의 PowerShell 은 기본 보안 연결(TLS)이 낮아 깃허브에 접속하지 못한다.
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

Write-Host ""
Write-Host "================================"
Write-Host " 옵시디언 저장 스킬 설치"
Write-Host "================================"
Write-Host ""

$zipUrl = "https://github.com/parksangick-lgtm/PARK../archive/refs/heads/main.zip"
$work   = Join-Path $env:TEMP "park-obsidian-skill"
$dest   = Join-Path $env:USERPROFILE ".claude\skills"

try {
    # 1) 최신 파일 내려받기
    Write-Host "1/3  최신 파일을 내려받는 중..."
    if (Test-Path $work) { Remove-Item -LiteralPath $work -Recurse -Force }
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    $zipPath = Join-Path $work "main.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

    # 2) 압축을 풀고 스킬 복사
    Write-Host "2/3  스킬을 복사하는 중..."
    Expand-Archive -LiteralPath $zipPath -DestinationPath $work -Force
    $srcRoot = (Get-ChildItem -LiteralPath $work -Directory | Select-Object -First 1).FullName
    if (-not $srcRoot) { throw "압축을 푼 폴더를 찾지 못했습니다." }

    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    Copy-Item -Path (Join-Path $srcRoot ".claude\skills\*") -Destination $dest -Recurse -Force

    $saverDir = Join-Path $dest "obsidian-save"
    New-Item -ItemType Directory -Path $saverDir -Force | Out-Null
    Copy-Item -Path (Join-Path $srcRoot "src\obsidian_save.py") -Destination $saverDir -Force
    Write-Host "     복사 완료: $dest"

    # 3) 파이썬을 찾아 옵시디언 볼트 등록
    Write-Host "3/3  옵시디언 볼트를 찾는 중..."
    $py = $null
    foreach ($cmd in @("py", "python", "python3")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) { $py = $cmd; break }
    }

    if ($py) {
        $saver = Join-Path $saverDir "obsidian_save.py"
        & $py $saver --set-vault auto
        Write-Host ""
        Write-Host "설치가 끝났습니다."
        Write-Host '이제 홈페이지 작업 폴더에서 "5번" 이라고 말하면 옵시디언에 저장됩니다.'
    }
    else {
        Write-Host ""
        Write-Host "[알림] 파이썬이 없어서 볼트 등록만 건너뛰었습니다. 스킬 복사는 끝났습니다."
        Write-Host "https://www.python.org/downloads/ 에서 설치한 뒤 이 명령을 다시 실행하세요."
        Write-Host '설치할 때 "Add python.exe to PATH" 를 꼭 체크하세요.'
    }
}
catch {
    Write-Host ""
    Write-Host "[오류] 설치 중 문제가 생겼습니다:"
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "이 내용을 그대로 알려주시면 원인을 찾아드리겠습니다."
}
