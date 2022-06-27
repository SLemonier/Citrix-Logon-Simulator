from time import sleep, time
from cmath import log
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import *
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from PIL import Image
from PIL import ImageGrab
import sys
import win32evtlogutil
import win32evtlog
import os
import pytesseract
import requests
import logging
import logging.config

#### PREREQUISITES

# pip install selenium
# pip install pypiwin32
# pip install requests
# pip install pyautogui
# pip install Pillow
# pip install pytesseract
# install tesseract
# add tesseract to path
# download geckodriver
# $env:py_ric_pwd =

##################################################################################################################################
##################################################### Custom Parameters ##########################################################
##################################################################################################################################

EventSource = 'Citrix.LogonSimulator'
username = "marlene.sasseur"
#password = os.getenv('py_pwd')
password = 'Pssw0rd'
#URL = "https://remote.stevenlemonier.fr"
URL = "http://stf01.homelab.local"
ResourceToTest = "Desktop"
ScreenshotFile = "Screenshot.png" #Full path is required
TextToFind = "Yep."
LogFile = "CitrixLogonSimulator.log"

##################################################################################################################################
#################################################### Let the magic begin #########################################################
##################################################################################################################################

#Other Variables
Resourcefound = False
timeout = 5

#Check logging file size
if os.path.exists(LogFile):
    if os.stat(LogFile).st_size > 5000000: #if greater than 5MB, archive LogFile
        dateLogGile = datetime.today().strftime('%Y-%m-%d') + "-CitrixLogonSimulator.log"
        os.rename(LogFile, dateLogGile) 

#configure logging
logging.basicConfig(filename=LogFile, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

#configure Windows EventLog
App_Name = EventSource
App_Event_ID_SUCCESS = 12000
App_Event_ID_INFORMATION = 12001
App_Event_ID_ERROR = 12002
App_Event_Category = 90
App_Event_Data= b"data"

##################################################################################################################################
# Log function
##################################################################################################################################

def logevent(message,App_Event_Type,App_Event_ID):
    print(message)
    logging.info(message)
    App_Event_Str = [message]
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)


##################################################################################################################################
################################# Connect to Gateway URL and start an instance of ResourceToTest #################################
##################################################################################################################################

def logOnCitrixGateway():
    #Trying to type login
    try: 
        loginfield = driver.find_element(By.ID, "login")
        loginfield.send_keys(username)
        passwordfield = driver.find_element(By.ID, "passwd")
        passwordfield.send_keys(password)
        loginbutton = driver.find_element(By.ID, "nsg-x1-logon-button")
        loginbutton.click()
        logevent("Trying to log in",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
    except TimeoutException:
        driver.quit()
        logevent("Cannot find login to %s" % URL,win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        sys.exit()

    #Wait for the HTML5 or logon failure page to load
    try: #Check first logon failure
        loginfailed = EC.presence_of_element_located((By.ID, "access_denied_title"))
        WebDriverWait(driver, 5).until(loginfailed) #lower the timeout because access denied is pretty fast to appear
        logevent("Failed to log on %s with %s" % (URL, username),win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        driver.quit()
        sys.exit()
    except TimeoutException:
        try: #Try to locate HTML5 receiver button
            loginfield = EC.presence_of_element_located((By.ID, "protocolhandler-welcome-useLightVersionLink"))
            WebDriverWait(driver, timeout).until(loginfield)
            logevent("HTML5 receiver page loaded successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
        except:
            driver.quit()
            logevent("Failed to load HTML5 receiver page",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
            sys.exit()

    #Validate HTML5 Receiver
    try:
        html5receiverbutton = driver.find_element(By.ID, "protocolhandler-welcome-useLightVersionLink")
        html5receiverbutton.click()
        logevent("Selecting HTML5 receiver",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
    except TimeoutException:
        driver.quit()
        logevent("Cannot select HTML5 receiver",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        sys.exit()

def logonCitrixStorefront():
    #Wait for the HTML5 page to load
    try:
        html5receiverbutton = EC.presence_of_element_located((By.ID, "protocolhandler-welcome-useLightVersionLink"))
        WebDriverWait(driver, timeout).until(html5receiverbutton)
        logevent("HTML5 receiver page loaded successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
    except TimeoutException:
        driver.quit()
        logevent("Failed to load HTML5 receiver page",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        sys.exit()
    
    #Validate HTML5 Receiver
    try:
        html5receiverbutton = driver.find_element(By.ID, "protocolhandler-welcome-useLightVersionLink")
        html5receiverbutton.click()
        logevent("HTML5 receiver selected successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
    except TimeoutException:
        driver.quit()
        logevent("Cannot select HTML5 receiver",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        sys.exit()

    #Wait for the logon page to load
    try:
        loginfield = EC.presence_of_element_located((By.ID, "username")) #locate login button if it's a Citrix Gateway URL
        WebDriverWait(driver, timeout).until(loginfield)
        logevent("Logon page loaded successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
    except TimeoutException:
        driver.quit()
        logevent("Cannot load logon page",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        sys.exit()
 
    #Trying to type login
    try: 
        loginfield = driver.find_element(By.ID, "username")
        loginfield.send_keys(username)
        passwordfield = driver.find_element(By.ID, "password")
        passwordfield.send_keys(password)
        loginbutton = driver.find_element(By.ID, "loginBtn")
        loginbutton.click()
        logevent("Trying to log in",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
    except:
        driver.quit()
        logevent("Cannot type login on %s" % URL,win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        sys.exit()

    #Wait for the page to load
    try: #Check first logon failure
        xPathtoFind = "//div[@class='standaloneText label error']"
        loginfailed = EC.presence_of_element_located((By.XPATH, xPathtoFind))
        WebDriverWait(driver, timeout).until(loginfailed)
        logevent("Failed to log on %s with %s" % (URL, username),win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        driver.quit()
        sys.exit()
    except TimeoutException:
        logevent("Logged in successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)


logging.info('#####################################################################################################################################')
logging.info('#####################################################################################################################################')
logging.info('#####################################################################################################################################')

#First test if URL can be resolved. No need to go further if it doesn't
try:
    httpResponse = requests.get(URL)
    logevent('%s is reachable!' % URL,win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except TimeoutException:
    logevent("Cannot reach %s" % URL,win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

#Create an instance of Firefox
# driver = webdriver.Firefox(capabilities=firefox_capabilities)
try:
    driver = webdriver.Firefox()
    logevent("Firefox instance started successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except:
    logevent("Cannot start Firefox",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

#Navigate to Gateway URL
driver.get(URL)

#Wait for the landing page to load
try:
    loginfield = EC.presence_of_element_located((By.ID, "nsg-x1-logon-button")) #locate login button if it's a Citrix Gateway URL
    WebDriverWait(driver, timeout).until(loginfield)
    logevent("%s is a Gateway URL." % URL,win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
    #Start log on process for Citrix Gateway
    logOnCitrixGateway()
except TimeoutException:
    try:
        html5receiverbutton = EC.presence_of_element_located((By.ID, "protocolhandler-welcome-installButton")) #locate HTML5 button if it's a Citrix Storefront URL
        WebDriverWait(driver, timeout).until(html5receiverbutton)
        logevent("%s is a Storefront URL." % URL,win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
        #Start log on process for Citrix Storefront
        logonCitrixStorefront()
    except TimeoutException:
        driver.quit()
        logevent("%s is not a Citrix Gateway or Citrix Storefront landing page." % URL,win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
        sys.exit()


#Now logon process is finished, get back to common part
#Wait for the enumeration page to load
try:
    xPathtoFind = "//img[@alt='" + ResourceToTest + "']"
    resourcebutton = EC.presence_of_element_located((By.XPATH, xPathtoFind))
    WebDriverWait(driver, timeout).until(resourcebutton)
    logevent("%s has been found, application enumeration completed successfully" % ResourceToTest,win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except TimeoutException:
    driver.quit()
    logevent("%s has not been found, either the resource is not assigned to the user or application enumeration failed" % ResourceToTest,win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

#Start an instance of the resource
try:
    resourcebutton = driver.find_element(By.XPATH, xPathtoFind)
    resourcebutton.click()
    logevent("Launching %s..." % ResourceToTest,win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except:
    driver.quit()
    logevent("Cannot Launch %s" % ResourceToTest,win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()


##################################################################################################################################
################################################### Screenshot of ResourceToTest #################################################
##################################################################################################################################

#Waiting for app/desktop to launch
sleep(60)
try:
    myScreenShot = ImageGrab.grab()
    myScreenShot.save(ScreenshotFile)
    logevent("Took a screenshot successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
    driver.quit()
except:
    driver.quit()
    logevent("Cannot take a screenshot",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()


##################################################################################################################################
############################################################### OCR ##############################################################
##################################################################################################################################

try:
    OCR = pytesseract.image_to_string(Image.open(ScreenshotFile))
    logevent("Processing OCR on screenshot file",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except:
    logevent("OCR processing failed on screenshot file",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

if TextToFind in OCR:
    logevent("%s found with OCR. Application launched successfully" % TextToFind,win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_SUCCESS)
    sys.exit()
else:
    logevent("%s not found. %s Failed to launch" % (TextToFind, ResourceToTest),win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()