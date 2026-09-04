# 註冊 Windows 工作排程器，每 30 分鐘自動抓一次新文章並翻譯/解析。
# 用 PowerShell 執行:
#   powershell -ExecutionPolicy Bypass -File .\scripts\register_task.ps1

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $PSScriptRoot
$PythonExe  = (Get-Command python).Source
$ScriptPath = Join-Path $ProjectDir "src\check_new.py"
$TaskName   = "EnglishReadingCoach-Fetch"

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory $ProjectDir

# 每天固定時間觸發一次，之後每 30 分鐘重複，持續 24 小時（等於全天每 30 分鐘跑一次）。
$Trigger = New-ScheduledTaskTrigger -Daily -At 07:00am
$Trigger.Repetition = (New-ScheduledTaskTrigger -Once -At 07:00am `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration (New-TimeSpan -Days 1)).Repetition

$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force `
    -Description "英文新聞學習平台：每 30 分鐘抓一次新文章，翻譯成中文並解析單字/文法"

Write-Host "已註冊工作排程 '$TaskName'。"
Write-Host "可用『工作排程器』(Task Scheduler) 圖形介面查看/停用，或執行："
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
