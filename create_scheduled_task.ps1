$Action = New-ScheduledTaskAction -Execute "E:\CHATTER_BOX\send_scheduled_messages.bat"
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName "ChatterBoxScheduledMessages" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force 