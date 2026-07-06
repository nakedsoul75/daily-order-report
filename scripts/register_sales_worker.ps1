# Windows Task Scheduler — 매출 수집 워커 상주 등록 (bks-os "수집 요청" → 거의 즉시 반영)
#
# 로그인 시 자동 시작해 계속 떠 있으면서 15초마다 sales_sync_request 큐를 확인,
# 요청이 들어오면 그 날짜 매출을 수집해 daily_sales 에 기록한다.
# → bks-os 영업·매출 화면에서 '수집 요청' 누르면 ~15초 내 화면에 자동 표시.
#
# 실행 (PowerShell):
#   cd "C:\Users\naked\Documents\agent\daily-order-report"
#   powershell -ExecutionPolicy Bypass -File scripts\register_sales_worker.ps1
#
# 제거:  Unregister-ScheduledTask -TaskName "BksSalesWorker" -Confirm:$false
# 즉시 시작: Start-ScheduledTask -TaskName "BksSalesWorker"
# 로그 보기: Get-Content ".\logs\sales_worker.log" -Tail 40

$ErrorActionPreference = "Stop"

$WorkDir = "C:\Users\naked\Documents\agent\daily-order-report"
$Python = (Get-Command python.exe).Source
$LogDir = Join-Path $WorkDir "logs"
$TaskName = "BksSalesWorker"
$Interval = 15   # 폴링 주기(초)

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
    Write-Host "[OK] Created logs directory: $LogDir"
}

$LogFile = Join-Path $LogDir "sales_worker.log"
# chcp 65001 (UTF-8) + 상주 --watch. 로그는 append.
$Cmd = "/c chcp 65001 > nul && cd /d `"$WorkDir`" && `"$Python`" sales_sync_worker.py --watch --interval $Interval >> `"$LogFile`" 2>&1"
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $Cmd

# 로그인 시 시작 + (혹시 죽으면) 즉시 재시작. 상주형이라 실행시간 제한 없음(0).
$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[INFO] Removed existing task: $TaskName"
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "bks-os 매출 수집 워커 — sales_sync_request 큐 폴링 → daily_sales" | Out-Null

Write-Host "[OK] Registered: $TaskName (로그인 시 상주, ${Interval}초 폴링) → log: $LogFile"
Write-Host ""
Write-Host "=== Done ==="
Write-Host "지금 시작:   Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "로그 보기:   Get-Content '$LogFile' -Tail 40"
Write-Host "제거:        Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
