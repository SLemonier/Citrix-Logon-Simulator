using namespace Windows.Storage
using namespace Windows.Graphics.Imaging
<#
 .Synopsis
  Logon Simulator for Citrix environment
 .Description
  Logon Simulator will open a new instance of Internet Explorer.
  Then logs on the Storefront/Gateway URL and launch a specified resource.
  Once the app has started, the script will take a screenshot and will look for a specified string using OCR.
  In case of any error, Logon simulator will generate events in Windows Event Log.
  PreRequisites.ps1 must be run prior to this script to create Event Source Log.

  Event Logs description:    
  EventID - EntryType	- Description
  
  1000 - Information    - Logon simulation succeeded to launch the resource <$ResourceToTest>.
  1001 - Error          - Citrix Workspace App is not installed. CWA is mandatory and should be installed prior to execute this script.
  1002 - Error          - No login form detected. Check $StorefrontURL URL.
  1003 - Error          - $Username or $Password is incorrect. Cannot logon to $StorefrontURL URL
  1004 - Warning        - Password is about to expire. Please change the password.
  1005 - Error          - Cannot find $ResourceToTest. Check the $username is allowed to acces the resource and if the source is available.
  1006 - Error          - An issue occured during the screenshot process. Review log file for more information.
  1007 - Error          - OCR did not find $TextToFind in the screenshot. $ResourceToTest might not be launched properly. Check $ScreenshotFile.

 .Example
 # Start logon simulator
 ./CitrixLogonSimulator.ps1
#>

##################################################################################################################################
##################################################### Custom Parameters ##########################################################
##################################################################################################################################

$EventSource = 'HG.Citrix.LogonSimulator'
$username = ""
$password = ""
$StorefrontURL = "https://"
$ResourceToTest = "Windows 10 - Qual"
$ScreenshotFile = "C:\Temp\Screenshot.bmp" #Full path is required
$TextToFind = ""
$LogFile = ".\CitrixLogonSimulator.log"

##################################################################################################################################
#################################################### Let the magic begin #########################################################
##################################################################################################################################

#Start logging
Start-Transcript -Path $LogFile

#Other Variables
$Resourcefound = $false

#Detect OS language for some text comparison
$language = (Get-WinUserLanguageList)[0].LocalizedName
if($language -match "En"){
    $PasswordIsNotExpiring = "Not now"
} elseif ($language -match "Fr"){
    $PasswordIsNotExpiring = "Pas maintenant"
} else {
    Write-Host "Display language is not fully supported. Only english and french are supported. Some feature may not work correctly." -ForegroundColor Yellow
 }

##################################################################################################################################
#################################################### Check Event Logs Source #####################################################
##################################################################################################################################

#Reusable function to write in the eventlog with Info/Warning/Error Handling
function WriteEventLog {
    Param(
        [string]$message,
        [string]$logName = 'Application',
        [string]$source = $EventSource,
        [string]$entryType,
        [int] $eventId
    )
    switch ($entryType) {
        "Warning" { $id = New-Object System.Diagnostics.EventInstance($eventId,1,2) }
        "Error" { $id = New-Object System.Diagnostics.EventInstance($eventId,1,1) }
        "Information" { $id = New-Object System.Diagnostics.EventInstance($eventId,1) }
        Default {}
    }
    $evtObject = New-Object System.Diagnostics.EventLog
    $evtObject.Log = $logName
    $evtObject.Source = $source;
    $evtObject.WriteEvent($id, @($message))
}

##################################################################################################################################
############################################## Check Logon Simulator pre-requisites ##############################################
##################################################################################################################################

Write-host "Checking pre-requisites - Citrix Workspace App... " -NoNewline    
if(Test-Path -Path "C:\Program Files (x86)\Citrix\ICA Client\wfcrun32.exe"){
    Write-host "OK" -ForegroundColor Green
} else {
    Write-host "Fail" -ForegroundColor Red
    Write-host "Citrix Workspace App is not installed. CWA is mandatory and should be installed prior to execute this script." -ForegroundColor Red
    WriteEventLog -entrytype "Error" -eventid 1001 -message "Citrix Workspace App is not installed. CWA is mandatory and should be installed prior to execute this script."
    Stop-transcript
    Exit
}

##################################################################################################################################
################################# Connect to Storefront and start an instance of $ResourceToTest #################################
##################################################################################################################################

#Create an instance of IE
$ie = New-Object -ComObject 'internetExplorer.Application'
$ie.Visible= $true #Make it visible

#Navigate to the Storefront/GW URL
$ie.Navigate($StorefrontURL)

#Wait for the page to load
While ($ie.Busy -eq $true) {Start-Sleep -Seconds 3;}

#Check if the URL is a Storefront/Gateway URL (username's field exists)
Write-Host "Checking $StorefrontURL URL... " -NoNewline
try{
    $usernamefield = $ie.document.getElementByID('username')
    Write-Host "OK" -ForegroundColor Green
} catch {
    Write-host "Fail" -ForegroundColor Red
    Write-host "No login form detected. Check $StorefrontURL URL." -ForegroundColor Red
    WriteEventLog -entrytype "Error" -eventid 1002 -message "No login form detected. Check $StorefrontURL URL."
    $ie.Quit()
    Stop-transcript
    Exit
}
 
#Fill the form to log
$usernamefield = $ie.document.getElementByID('username')
$usernamefield.value = "$username"
$passwordfield = $ie.document.getElementByID('password')
$passwordfield.value = "$password"
$Link = $ie.document.getElementByID('loginBtn')
$Link.click()
 
#Wait for the authentication 
Start-Sleep -Seconds 3
While ($ie.Busy -eq $true) {Start-Sleep -Seconds 3;}

#Check the authentication worked
Write-host "Looking for Successful authentication... " -NoNewline
$Elements= $ie.document.getElementByID('explicit-auth-screen')
foreach($Element in $Elements){
    if($Elements.outerHTML -match "incorrect"){
        Write-host "Fail" -ForegroundColor Red
        Write-host "Username or Password is incorrect. Cannot logon to $StorefrontURL URL." -ForegroundColor Red
        WriteEventLog -entrytype "Error" -eventid 1003 -message "Username or Password is incorrect. Cannot logon to $StorefrontURL URL."
        $ie.Quit()
        Stop-transcript
        Exit
    } else {
        Write-host "OK" -ForegroundColor Green
    }
}

#Handle expiring password prompt
$Link= $ie.document.getElementByID('btnPasswordContinue')
if($Link.innerText -notmatch $PasswordIsNotExpiring){
    $Link.Click()
    Write-host "Warning - Password is about to expire. Please change the password." -ForegroundColor Yellow
    WriteEventLog -entrytype "Warning" -eventid 1004 -message "Password is about to expire. Please change the password."
}
 
#Wait for the app enumeration 
While ($ie.Busy -eq $true) {Start-Sleep -Seconds 3;}

#Launch specified resource
Write-Host "Searching for $ResourceToTest... " -NoNewline
$tags = $ie.document.getElementsByTagName("img")
foreach($tag in $tags){
    if($tag.outerHTML -match $ResourceToTest){
        $Resourcefound = $true
        Write-Host "OK" -ForegroundColor Green
        Write-Host "Launching $ResourceToTest... " -NoNewline
        $tag.click()
    } 
}

#if $ResourceToTest is not found, stops the script
if($Resourcefound -eq $false){
    Write-host "Fail" -ForegroundColor Red
    Write-host "Cannot find $ResourceToTest. Check the $username is allowed to acces the resource and if the source is available." -ForegroundColor Red
    WriteEventLog -entrytype "Error" -eventid 1005 -message "Cannot find $ResourceToTest. Check the $username is allowed to acces the resource and if the source is available."
    $ie.Quit()
    Stop-transcript
    Exit
}

##################################################################################################################################
################################################## Screenshot of $ResourceToTest #################################################
##################################################################################################################################

#Waiting for app/desktop to launch
Start-Sleep -Seconds 120
Write-Host "OK" -ForegroundColor Green

Write-host "Taking a screenshot... " -NoNewline
try{
    #Ajout des classes .Net
    Add-Type -AssemblyName System.Windows.Forms
    Add-type -AssemblyName System.Drawing

    #Gather Screen resolution 
    $Screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $Width = $Screen.Width
    $Height = $Screen.Height
    $Left = $Screen.Left
    $Top = $Screen.Top

    # Create bitmap object
    $bitmap = New-Object System.Drawing.Bitmap $Width, $Height
    $graphic = [System.Drawing.Graphics]::FromImage($bitmap)

    # Capture screen and save file
    $graphic.CopyFromScreen($Left, $Top, 0, 0, $bitmap.Size)
    if(Test-Path -Path $ScreenshotFile){
        Remove-item -Path $ScreenshotFile -force | Out-Null
    }
    $bitmap.Save($ScreenshotFile)
    Write-Host "OK" -ForegroundColor Green
    Write-Host "Screenshot saved to $ScreenshotFile."
} catch {
    Write-host "Fail" -ForegroundColor Red
    Write-host "An issue occured during the screenshot process. Review log file for more information." -ForegroundColor Red
    WriteEventLog -entrytype "Error" -eventid 1006 -message "An issue occured during the screenshot process. Review log file for more information."
    $ie.Quit()
    Stop-Process -Name CDViewer -force
    Stop-transcript
    Exit
}

##################################################################################################################################
############################################################### OCR ##############################################################
##################################################################################################################################

Write-Host "Searching for $TextToFind in the screenshot using OCR... " -NoNewline
try {
    #Ajout des classes .Net
    Add-Type -AssemblyName System.Runtime.WindowsRuntime

    #Charging OCR Engine
    $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()

     # .Net method needs a full path, or at least might not have the same relative path root as PowerShell
     $p = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($p)

     # PowerShell doesn't have built-in support for Async operations,
    # but all the WinRT methods are Async.
    # This function wraps a way to call those methods, and wait for their results.
    $getAwaiterBaseMethod = [WindowsRuntimeSystemExtensions].GetMember('GetAwaiter').
    Where({
            $PSItem.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
        }, 'First')[0]

    Function Await {
        param($AsyncTask, $ResultType)

        $getAwaiterBaseMethod.
        MakeGenericMethod($ResultType).
        Invoke($null, @($AsyncTask)).
        GetResult()
    }

    $params = @{
        AsyncTask  = [StorageFile]::GetFileFromPathAsync($ScreenshotFile)
        ResultType = [StorageFile]
    }
    $storageFile = Await @params
    
    $params = @{
        AsyncTask  = $storageFile.OpenAsync([FileAccessMode]::Read)
        ResultType = [Streams.IRandomAccessStream]
    }
    $fileStream = Await @params
    
    $params = @{
        AsyncTask  = [BitmapDecoder]::CreateAsync($fileStream)
        ResultType = [BitmapDecoder]
    }
    $bitmapDecoder = Await @params

    $params = @{
        AsyncTask = $bitmapDecoder.GetSoftwareBitmapAsync()
        ResultType = [SoftwareBitmap]
    }
    $softwareBitmap = Await @params

    # Run the OCR
    $OCR = Await $ocrEngine.RecognizeAsync($softwareBitmap) ([Windows.Media.Ocr.OcrResult])
    if($OCR.Text -match $TextToFind){
        Write-Host "OK" -ForegroundColor Green
    } else {
        Write-host "Fail" -ForegroundColor Red
        Write-host "OCR did not find $TextToFind in the screenshot. $ResourceToTest might not be launched properly. Check $ScreenshotFile." -ForegroundColor Red
        WriteEventLog -entrytype "Error" -eventid 1007 -message "OCR did not find $TextToFind in the screenshot. $ResourceToTest might not be launched properly. Check $ScreenshotFile."
        $ie.Quit()
        Stop-Process -Name CDViewer -force
        Stop-transcript
        Exit
    }

} catch {
    Write-host "Fail" -ForegroundColor Red
    Write-host "OCR did not find $TextToFind in the screenshot. $ResourceToTest might not be launched properly. Check $ScreenshotFile." -ForegroundColor Red
    WriteEventLog -entrytype "Error" -eventid 1007 -message "OCR did not find $TextToFind in the screenshot. $ResourceToTest might not be launched properly. Check $ScreenshotFile."
    $ie.Quit()
    Stop-Process -Name CDViewer -force
    Stop-transcript
    Exit
}

Write-host "Citrix Logon Simulator completed successfully the simulation. $TexToFind was found in $ResourceToTest." -ForegroundColor Green
WriteEventLog -entrytype "Information" -eventid 1000 -message "Citrix Logon Simulator completed successfully the simulation. $TexToFind was found in $ResourceToTest."


##################################################################################################################################
######################################################### Cleaning instances #####################################################
##################################################################################################################################

Stop-Process -Name CDViewer -force
$ie.Quit()
Stop-transcript