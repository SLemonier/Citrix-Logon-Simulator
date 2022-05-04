from cmath import log
from time import sleep, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import *
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from PIL import Image
import sys
import win32evtlogutil
import win32evtlog
import os
import pyautogui
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
#password = os.getenv('py_ric_pwd')
password = 'Pssw0rd'
URL = "https://remote.stevenlemonier.fr"
ResourceToTest = "Desktop"
ScreenshotFile = "Screenshot.bmp" #Full path is required
TextToFind = "Yep."
LogFile = "CitrixLogonSimulator.log"

##################################################################################################################################
#################################################### Let the magic begin #########################################################
##################################################################################################################################

#Other Variables
Resourcefound = False
timeout = 30

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

##################
# Log function
##################

def logevent(message,App_Event_Type,App_Event_ID):
    print(message)
    logging.info(message)
    App_Event_Str = [message]
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)


##################################################################################################################################
################################# Connect to Gateway and start an instance of ResourceToTest #################################
##################################################################################################################################

logging.info('#####################################################################################################################################')
logging.info('#####################################################################################################################################')
logging.info('#####################################################################################################################################')

#First test if URL can be resolved. No need to go further if it doesn't
try:
    httpResponse = requests.get(URL)
    logevent('%s is reachable!' % URL,win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except:
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

#Wait for the page to load
try:
    loginfield = EC.presence_of_element_located((By.ID, "login"))
    WebDriverWait(driver, timeout).until(loginfield)
    logevent("Login field was found.",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except TimeoutException:
    driver.quit()
    logevent("Cannot find a login field on the page.",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

#Trying to type login
try: 
    loginfield = driver.find_element(By.ID, "login")
    loginfield.send_keys(username)
    passwordfield = driver.find_element(By.ID, "passwd")
    passwordfield.send_keys(password)
    loginbutton = driver.find_element(By.ID, "nsg-x1-logon-button")
    loginbutton.click()
    logevent("Logged in successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except:
    driver.quit()
    logevent("Cannot log in %s" % URL,win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

#Wait for the page to load
try:
    loginfield = EC.presence_of_element_located((By.ID, "protocolhandler-welcome-useLightVersionLink"))
    WebDriverWait(driver, timeout).until(loginfield)
    logevent("Login field was found.",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except TimeoutException:
    driver.quit()
    logevent("Cannot find a login field on the page.",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

#Wait for the page to load
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
except:
    driver.quit()
    logevent("Cannot select HTML5 receiver",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

#Wait for the page to load
try:
    xPathtoFind = "//img[@alt='" + ResourceToTest + "']"
    resourcebutton = EC.presence_of_element_located((By.XPATH, xPathtoFind))
    WebDriverWait(driver, timeout).until(resourcebutton)
    logevent("Application enumeration finished successfully",win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except TimeoutException:
    driver.quit()
    logevent("Failed to load application enumeration",win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()

#Start an instance of the resource
try:
    resourcebutton = driver.find_element(By.XPATH, xPathtoFind)
    resourcebutton.click()
    logevent("%s application launched" % ResourceToTest,win32evtlog.EVENTLOG_INFORMATION_TYPE,App_Event_ID_INFORMATION)
except:
    driver.quit()
    logevent("Cannot find %s" % ResourceToTest,win32evtlog.EVENTLOG_ERROR_TYPE,App_Event_ID_ERROR)
    sys.exit()


##################################################################################################################################
################################################### Screenshot of ResourceToTest #################################################
##################################################################################################################################

#Waiting for app/desktop to launch
sleep(60)
try:
    myScreenShot = pyautogui.screenshot()
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