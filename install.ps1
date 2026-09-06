# 옵시디언 저장 스킬 설치 (윈도우)
#
# 사용법 - PowerShell 창에 아래 한 줄을 붙여넣고 Enter:
#   curl.exe -sSL -o "$env:TEMP\ps.ps1" https://raw.githubusercontent.com/parksangick-lgtm/PARK../main/install.ps1; powershell -ExecutionPolicy Bypass -File "$env:TEMP\ps.ps1"
#
# 하는 일: 최신 파일 내려받기 -> 스킬을 홈 폴더에 복사 -> 옵시디언 볼트 자동 등록

$ErrorActionPreference = "Stop"

# PowerShell 버전과 설정에 따라, 외부 프로그램이 0 이 아닌 값으로 끝나기만 해도
# 위의 "Stop" 때문에 스크립트가 통째로 멈추기도 한다. 그러면 아래에서 직접
# 챙기는 친절한 안내 대신 시뻘건 오류만 뜬다. 종료 코드는 우리가 확인하므로
# 어느 버전에서든 멈추지 않도록 이 동작을 꺼 둔다.
$PSNativeCommandUseErrorActionPreference = $false

# 옛 윈도우의 PowerShell 은 기본 보안 연결(TLS)이 낮아 깃허브에 접속하지 못한다.
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

# 저장소 이름이 "PARK.." 처럼 점으로 끝나면 PowerShell 의 Invoke-WebRequest 가
# 주소를 정리한다며 점을 떼어내서 404 가 난다. 그래서 주소를 그대로 보내는
# curl.exe(윈도우 10 1803 이상 기본 탑재)를 먼저 쓴다.
function Get-RemoteFile($url, $outFile) {
    $curl = Join-Path $env:SystemRoot "System32\curl.exe"
    if (Test-Path $curl) {
        & $curl -sSL --fail -o $outFile $url
        if ($LASTEXITCODE -ne 0) { throw "내려받기에 실패했습니다 (curl 오류 $LASTEXITCODE)`n주소: $url" }
    }
    else {
        Write-Host "     (curl.exe 가 없어 PowerShell 로 내려받습니다)"
        Invoke-WebRequest -Uri $url -OutFile $outFile -UseBasicParsing
    }
    if (-not (Test-Path $outFile)) { throw "내려받은 파일이 없습니다: $outFile" }
}

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
    Get-RemoteFile $zipUrl $zipPath

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
    $saver = Join-Path $saverDir "obsidian_save.py"
    Write-Host "     복사 완료: $dest"

    # 3) 파이썬을 찾아 옵시디언 볼트 등록
    Write-Host "3/3  옵시디언 볼트를 찾는 중..."

    # 이름이 있는지 보는 것만으로는 부족하다. 윈도우 10/11 은 파이썬이 깔려 있지
    # 않아도 python.exe 라는 가짜 파일(마이크로소프트 스토어로 보내는 바로가기)을
    # 놔두기 때문이다. 그래서 --version 에 실제로 대답하는 것만 진짜로 친다.
    $py = $null
    foreach ($cmd in @("py", "python", "python3")) {
        if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { continue }
        $answer = ""
        try { $answer = & $cmd --version 2>$null } catch { $answer = "" }
        if ($LASTEXITCODE -eq 0 -and "$answer" -match "\d") { $py = $cmd; break }
    }

    $registered = $false
    if ($py) {
        & $py $saver --set-vault auto
        $registered = ($LASTEXITCODE -eq 0)

        # 자동으로 못 찾았을 때만 직접 물어본다(스킬설치.bat 과 같은 흐름).
        if (-not $registered) {
            Write-Host ""
            Write-Host "자동으로 찾지 못했습니다. 볼트 폴더 경로를 직접 알려주세요."
            Write-Host '(옵시디언 왼쪽 아래 볼트 이름 클릭 - "다른 보관소 열기" 에서 경로를 볼 수 있습니다)'
            $vault = Read-Host "경로 (건너뛰려면 그냥 Enter)"
            if ($vault) {
                & $py $saver --set-vault $vault
                $registered = ($LASTEXITCODE -eq 0)
            }
        }
    }

    # 볼트 등록까지 됐을 때만 끝났다고 한다. 등록에 실패했는데 성공했다고 하면,
    # 나중에 "5번" 이 안 될 때 어디가 잘못됐는지 찾을 수가 없다.
    Write-Host ""
    if ($registered) {
        Write-Host "설치가 끝났습니다."
        Write-Host '이제 홈페이지 작업 폴더에서 "5번" 이라고 말하면 옵시디언에 저장됩니다.'
    }
    elseif (-not $py) {
        Write-Host "[알림] 스킬 복사는 끝났습니다. 다만 파이썬이 없어서 볼트 등록은 못 했습니다."
        Write-Host "https://www.python.org/downloads/ 에서 설치한 뒤 이 명령을 다시 실행하세요."
        Write-Host '설치할 때 "Add python.exe to PATH" 를 꼭 체크하세요.'
    }
    else {
        Write-Host "[알림] 스킬 복사는 끝났습니다. 다만 볼트 등록은 못 했습니다."
        Write-Host '지금 상태로 "5번" 을 하면 저장할 곳을 몰라서 실패합니다.'
        Write-Host "옵시디언을 한 번 켠 뒤, 아래를 그대로 붙여넣으면 등록됩니다:"
        Write-Host "  $py `"$saver`" --set-vault auto"
    }
}
catch {
    Write-Host ""
    Write-Host "[오류] 설치 중 문제가 생겼습니다:"
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "이 내용을 그대로 알려주시면 원인을 찾아드리겠습니다."
}
