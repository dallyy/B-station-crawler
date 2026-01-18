Param(
    [string]$TaskName = "BiliScraperWeekly",
    [string]$ScriptPath = "$PSScriptRoot\..\run_weekly.bat",
    [string]$StartIn = "$PSScriptRoot\..\",
    [string]$DayOfWeek = "Mon",
    [string]$Time = "03:00"
)

Write-Host "Registering scheduled task '$TaskName' to run $ScriptPath weekly on $DayOfWeek at $Time"

if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script not found: $ScriptPath"
    exit 1
}

# Prompt for credentials to allow 'Run whether user is logged on or not'
$cred = Get-Credential -Message "Enter the account the task should run as (password required to save credentials)"

$action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $StartIn
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $Time
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $cred.UserName -LogonType Password -RunLevel Highest

$task = New-ScheduledTask -Action $action -Principal $principal -Trigger $trigger -Settings $settings -Description "Weekly Bili scraper task"

Register-ScheduledTask -TaskName $TaskName -InputObject $task -User $cred.UserName -Password $cred.GetNetworkCredential().Password

Write-Host "Scheduled task '$TaskName' registered."