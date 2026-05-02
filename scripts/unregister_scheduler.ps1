# Windows Task Scheduler — Daily Order Report 작업 제거
#
# 실행:
#   powershell -ExecutionPolicy Bypass -File scripts\unregister_scheduler.ps1

$Tasks = @("DailyOrderReport-Morning", "DailyOrderReport-Alert", "DailyOrderReport-Midday", "DailyOrderReport-Evening")

foreach ($t in $Tasks) {
    $existing = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $t -Confirm:$false
        Write-Host "[OK] Removed: $t"
    } else {
        Write-Host "[SKIP] Not found: $t"
    }
}

Write-Host ""
Write-Host "=== Done ==="
