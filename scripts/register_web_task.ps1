# 註冊 Windows 工作排程器，讓網頁介面在你一登入 Windows 就自動啟動、常駐在背景，
# 這樣手機隨時可以連進來讀文章。
# 用 PowerShell 執行:
#   powershell -ExecutionPolicy Bypass -File .\scripts\register_web_task.ps1

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $PSScriptRoot
$PythonwExe = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $PythonwExe) { $PythonwExe = (Get-Command python).Source }
$ScriptPath = Join-Path $ProjectDir "web\app.py"
$TaskName   = "EnglishReadingCoach-WebUI"

$Action  = New-ScheduledTaskAction -Execute $PythonwExe -Argument "`"$ScriptPath`"" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Days 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force `
    -Description "英文新聞學習平台：登入時自動啟動網頁介面 (http://<這台電腦IP>:5001)，手機/電腦皆可連"

Write-Host "已註冊工作排程 '$TaskName'，下次登入 Windows 會自動啟動網頁介面。"
Write-Host ""
Write-Host "現在要立即啟動一次，不必等重新登入，可以執行："
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "要停用/移除："
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
