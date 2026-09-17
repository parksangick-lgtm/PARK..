# 바탕화면에 "옵시디언 스킬 설치" 아이콘을 만든다.
# 바탕화면-바로가기.bat 이 이 파일을 실행한다. 각 컴퓨터에서 한 번만 하면 된다.
#
# 왜 필요한가: 스킬을 고칠 때마다 이 폴더를 찾아 들어가 스킬설치.bat 을 눌러야 한다.
# 폴더 경로를 외우고 있을 이유가 없다.

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath('Desktop')
$target = Join-Path $repo '스킬설치.bat'

if (-not (Test-Path $target)) {
    Write-Host "스킬설치.bat 을 찾지 못했습니다: $target"
    Write-Host "이 스크립트는 park-obsidian-save 폴더 안에서 실행해야 합니다."
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $desktop '옵시디언 스킬 설치.lnk'))
$lnk.TargetPath = $target
$lnk.WorkingDirectory = $repo
$lnk.Description = '옵시디언 저장·복습 스킬을 이 컴퓨터에 설치한다 (고친 뒤 다시 누르면 갱신)'
$lnk.Save()

Write-Host '  만듦: 옵시디언 스킬 설치'
Write-Host ''
Write-Host '바탕화면을 확인하세요. (F5 로 새로고침)'
Write-Host '스킬을 고친 뒤에는 이 아이콘을 다시 눌러야 반영됩니다.'
