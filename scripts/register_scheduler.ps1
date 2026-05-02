# Windows Task Scheduler — Daily Order Report 자동 실행 등록
# 08:30 / 12:30 / 18:00 KST 매일 실행
#
# 실행 방법 (PowerShell):
#   cd "C:\Users\naked\Documents\agent\daily-order-report"
#   powershell -ExecutionPolicy Bypass -File scripts\register_scheduler.ps1
#
# 제거: scripts\unregister_scheduler.ps1 실행

$ErrorActionPreference = "Stop"

$WorkDir = "C:\Users\naked\Documents\agent\daily-order-report"
$Python = (Get-Command python.exe).Source
$LogDir = Join-Path $WorkDir "logs"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
    Write-Host "[OK] Created logs directory: $LogDir"
}

$Slots = @(
    @{Name = "DailyOrderReport-Morning";  Slot = "morning"; Time = "08:30"; Desc = "08:30 KST - Yesterday summary"},
    @{Name = "DailyOrderReport-Alert";    Slot = "alert";   Time = "09:00"; Desc = "09:00 KST - Delay + low stock alerts"},
    @{Name = "DailyOrderReport-Midday";   Slot = "midday";  Time = "12:30"; Desc = "12:30 KST - Morning cumulative"},
    @{Name = "DailyOrderReport-Evening";  Slot = "evening"; Time = "18:00"; Desc = "18:00 KST - Daily close"}
)

foreach ($s in $Slots) {
    $TaskName = $s.Name
    $LogFile = Join-Path $LogDir "$($s.Slot).log"

    # Build the action: chcp 65001 (UTF-8) + python src/main.py --slot=XXX >> logs/XXX.log
    $Cmd = "/c chcp 65001 > nul && cd /d `"$WorkDir`" && `"$Python`" src\main.py --slot=$($s.Slot) >> `"$LogFile`" 2>&1"
    $Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $Cmd

    $Trigger = New-ScheduledTaskTrigger -Daily -At $s.Time

    $Settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
        -RestartCount 2 `
        -RestartInterval (New-TimeSpan -Minutes 5) `
        -DontStopOnIdleEnd `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries

    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    # Remove existing if any
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
        -Description $s.Desc | Out-Null

    Write-Host "[OK] Registered: $TaskName ($($s.Time) KST daily) → log: $LogFile"
}

Write-Host ""
Write-Host "=== Done ==="
Write-Host "View tasks:  Get-ScheduledTask -TaskName 'DailyOrderReport-*'"
Write-Host "Run now:     Start-ScheduledTask -TaskName 'DailyOrderReport-Morning'"
Write-Host "View logs:   Get-Content '$LogDir\morning.log' -Tail 30"
Write-Host "Remove all:  scripts\unregister_scheduler.ps1"
