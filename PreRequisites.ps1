<#
 .Synopsis
  Pre-requisites for Citrix Logon Simulator
 .Description
  Pre-requisites must be launched with local admin rights (to check/create EventLog Source).
 .Example
 # Start logon simulator
 ./PreRequisites.ps1
#>

##################################################################################################################################
##################################################### Custom Parameters ##########################################################
##################################################################################################################################

$EventSource = 'HG.Citrix.LogonSimulator'
$LogFile = ".\PreRequisites.log"

##################################################################################################################################
#################################################### Let the magic begin #########################################################
##################################################################################################################################

#Start logging
Start-Transcript -Path $LogFile

##################################################################################################################################
#################################################### Check Event Logs Source #####################################################
##################################################################################################################################

$eventLogSourceParams = @{
    LogName = 'Application'
    Source = $EventSource
}

Write-host "Checking $EventSource Event Log Source... " -NoNewline  
try{ 
    If(-not [System.Diagnostics.EventLog]::SourceExists($eventLogSourceParams.Source)){   
        New-EventLog @eventLogSourceParams
    } 
}
catch {
    Write-host "Fail" -ForegroundColor Red
    Write-host "Cannot check or create $EventSource Event log source. Admin rights are mandatory to do this. Run the script with elevated Powershell console." -ForegroundColor Red
    Stop-transcript
    Exit
}
Write-Host "OK" -ForegroundColor Green

Stop-transcript