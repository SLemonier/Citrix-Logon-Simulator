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
Gateway_URL = "https://remote.stevenlemonier.fr"
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
App_Event_ID = 12001
App_Event_Category = 90
App_Event_Type = win32evtlog.EVENTLOG_ERROR_TYPE
App_Event_Data= b"data"
#App_Event_Str = ["This is an error"]
#win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, sstrings=App_Event_Str,data=App_Event_Data)


##################################################################################################################################
################################# Connect to Gateway and start an instance of ResourceToTest #################################
##################################################################################################################################

logging.info('#####################################################################################################################################')
logging.info('#####################################################################################################################################')
logging.info('#####################################################################################################################################')

#Create an instance of Firefox
# driver = webdriver.Firefox(capabilities=firefox_capabilities)
try:
    driver = webdriver.Firefox()
    logging.info("Firefox instance started successfully")
except:
    logging.error("Cannot start Firefox")
    App_Event_Str = ["Cannot start Firefox"]
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()

#Navigate to Gateway URL
driver.get(Gateway_URL)

#Wait for the page to load
try:
    loginfield = EC.presence_of_element_located((By.ID, "login"))
    WebDriverWait(driver, timeout).until(loginfield)
    logging.info("Login field was found.")
except TimeoutException:
    driver.quit()
    logging.error("Cannot find a login field on the page.")
    App_Event_Str = ["Cannot find a login field on the page."] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()

#Trying to type login
try: 
    loginfield = driver.find_element(By.ID, "login")
    loginfield.send_keys(username)
    passwordfield = driver.find_element(By.ID, "passwd")
    passwordfield.send_keys(password)
    loginbutton = driver.find_element(By.ID, "nsg-x1-logon-button")
    loginbutton.click()
    logging.info("Logged in successfully")
except:
    driver.quit()
    logging.error("Cannot log in %s" % Gateway_URL)
    App_Event_Str = ["Cannot log in %s" % Gateway_URL] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()

#Wait for the page to load
try:
    loginfield = EC.presence_of_element_located((By.ID, "protocolhandler-welcome-useLightVersionLink"))
    WebDriverWait(driver, timeout).until(loginfield)
    logging.info("Login field was found.")
except TimeoutException:
    driver.quit()
    logging.error("Cannot find a login field on the page.")
    App_Event_Str = ["Cannot find a login field on the page."] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()

#Wait for the page to load
try:
    html5receiverbutton = EC.presence_of_element_located((By.ID, "protocolhandler-welcome-useLightVersionLink"))
    WebDriverWait(driver, timeout).until(html5receiverbutton)
    logging.info("HTML5 receiver page loaded successfully")
except TimeoutException:
    driver.quit()
    logging.error("Failed to load HTML5 receiver page")
    App_Event_Str = ["Failed to load HTML5 receiver page"] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()

#Validate HTML5 Receiver
try:
    html5receiverbutton = driver.find_element(By.ID, "protocolhandler-welcome-useLightVersionLink")
    html5receiverbutton.click()
    logging.info("HTML5 receiver selected successfully")
except:
    driver.quit()
    logging.error("Cannot select HTML5 receiver")
    App_Event_Str = ["Cannot select HTML5 receiver"] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()

#Wait for the page to load
try:
    xPathtoFind = "//img[@alt='" + ResourceToTest + "']"
    resourcebutton = EC.presence_of_element_located((By.XPATH, xPathtoFind))
    WebDriverWait(driver, timeout).until(resourcebutton)
    logging.error("Application enumeration finished successfully")
except TimeoutException:
    driver.quit()
    logging.error("Failed to load application enumeration")
    App_Event_Str = ["Failed to load application enumeration"] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()

#Start an instance of the resource
try:
    resourcebutton = driver.find_element(By.XPATH, xPathtoFind)
    resourcebutton.click()
    logging.info("%s application launched" % ResourceToTest)
except:
    driver.quit()
    logging.error("Cannot find %s" % ResourceToTest)
    App_Event_Str = ["Cannot finr %s" % ResourceToTest] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()


##################################################################################################################################
################################################### Screenshot of ResourceToTest #################################################
##################################################################################################################################

#Waiting for app/desktop to launch
sleep(30)
myScreenShot = pyautogui.screenshot()
myScreenShot.save(ScreenshotFile)
logging.info("Took a screenshot successfully")
driver.quit()


##################################################################################################################################
############################################################### OCR ##############################################################
##################################################################################################################################

try:
    OCR = pytesseract.image_to_string(Image.open(ScreenshotFile))
    logging.info("Processing OCR on screenshot file")
except:
    logging.error("OCR processing failed on screenshot file")
    App_Event_Str = ["OCR processing failed on screenshot file"] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()


if TextToFind in OCR:
    print("%s found with OCR. Application launched successfully" % TextToFind)
    logging.info("%s found with OCR. Application launched successfully" % TextToFind)
    #Generate successfull Event
    App_Event_ID = 1200
    App_Event_Type = win32evtlog.EVENTLOG_INFORMATION_TYPE
    App_Event_Str = ["%s found with OCR. Application launched successfully" % TextToFind] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()
else:
    logging.error("%s not found. %s Failed to launch" % (TextToFind, ResourceToTest))
    App_Event_Str = ["%s not found. %s Failed to launch" % (TextToFind, ResourceToTest)] 
    win32evtlogutil.ReportEvent(App_Name,App_Event_ID, eventCategory= App_Event_Category, eventType=App_Event_Type, strings=App_Event_Str,data=App_Event_Data)
    sys.exit()