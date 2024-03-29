import json
import os
import platform
import random
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from argparse import ArgumentParser
from datetime import date, datetime, timedelta
from notifiers import get_notifier
from typing import Union, List
import copy

import ipapi
import requests
from func_timeout import FunctionTimedOut, func_set_timeout
from random_word import RandomWords
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoAlertPresentException,
                                        NoSuchElementException,
                                        SessionNotCreatedException,
                                        TimeoutException,
                                        UnexpectedAlertPresentException,
                                        JavascriptException,
                                        ElementNotVisibleException)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

# Define user-agents
PC_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.46'
MOBILE_USER_AGENT = 'Mozilla/5.0 (Linux; Android 12; SM-N9750) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 EdgA/110.0.1587.41'

POINTS_COUNTER = 0

# Global variables
FINISHED_ACCOUNTS = [] # added accounts when finished or those have same date as today date in LOGS at beginning.
ERROR = True # A flag for when error occurred.
MOBILE = True # A flag for when the account has mobile bing search, it is useful for accounts level 1 to pass mobile.
CURRENT_ACCOUNT = None # save current account into this variable when farming.
LOGS = {} # Dictionary of accounts to write in 'logs_accounts.txt'.
FAST = False # When this variable set True then all possible delays reduced.
BASE_URL = "https://rewards.bing.com"

# Define browser setup function
def browserSetup(isMobile: bool, user_agent: str = PC_USER_AGENT) -> WebDriver:
    # Create Chrome browser
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions
    if ARGS.edge:
        options = EdgeOptions()
    else:
        options = ChromeOptions()
    if ARGS.session or ARGS.account_browser:
        if not isMobile:
            options.add_argument(f'--user-data-dir={Path(__file__).parent}/Profiles/{CURRENT_ACCOUNT}/PC')
        else:
            options.add_argument(f'--user-data-dir={Path(__file__).parent}/Profiles/{CURRENT_ACCOUNT}/Mobile')
    options.add_argument("user-agent=" + user_agent)
    options.add_argument('lang=' + LANG.split("-")[0])
    options.add_argument('--disable-blink-features=AutomationControlled')
    prefs = {"profile.default_content_setting_values.geolocation": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled" : False}
    if ARGS.account_browser:
        prefs["detach"] = True
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    if ARGS.headless and ARGS.account_browser is None:
        options.add_argument("--headless")
    options.add_argument('log-level=3')
    options.add_argument("--start-maximized")
    if platform.system() == 'Linux':
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    if ARGS.edge:
        browser = webdriver.Edge(options=options)
    else:
        browser = webdriver.Chrome(options=options)
    return browser

# Define login function
def login(browser: WebDriver, email: str, pwd: str, isMobile: bool = False):
    # Close welcome tab for new sessions
    if ARGS.session:
        time.sleep(2)
        if len(browser.window_handles) > 1:
            current_window = browser.current_window_handle
            for handler in browser.window_handles:
                if handler != current_window:
                    browser.switch_to.window(handler)
                    time.sleep(0.5)
                    browser.close()
            browser.switch_to.window(current_window)
    # Access to bing.com
    browser.get('https://login.live.com/')
    # Check if account is already logged in
    if ARGS.session:
        if browser.title == "We're updating our terms" or isElementExists(browser, By.ID, 'iAccrualForm'):
            time.sleep(2)
            browser.find_element(By.ID, 'iNext').click()
            time.sleep(5)
        if browser.title == 'Is your security info still accurate?' or isElementExists(browser, By.ID, 'iLooksGood'):
            time.sleep(2)
            browser.find_element(By.ID, 'iLooksGood').click()
            time.sleep(5)
        # Click No thanks on break free from password question
        if isElementExists(browser, By.ID, "setupAppDesc"):
            time.sleep(2)
            browser.find_element(By.ID, "iCancel").click()
            time.sleep(5)
        if browser.title == 'Microsoft account | Home' or isElementExists(browser, By.ID, 'navs_container'):
            prGreen('[LOGIN] Account already logged in !')
            RewardsLogin(browser)
            print('[LOGIN]', 'Ensuring login on Bing...')
            checkBingLogin(browser, isMobile)
            return
        elif browser.title == 'Your account has been temporarily suspended':
            LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your account has been locked !'
            FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
            updateLogs()
            cleanLogs()
            raise Exception(prRed('[ERROR] Your account has been locked !'))
        elif isElementExists(browser, By.ID, 'mectrl_headerPicture') or 'Sign In or Create' in browser.title:
            if isElementExists(browser, By.ID, 'i0118'):
                browser.find_element(By.ID, "i0118").send_keys(pwd)
                time.sleep(2)
                browser.find_element(By.ID, 'idSIButton9').click()
                time.sleep(5)
                prGreen('[LOGIN] Account logged in again !')
                RewardsLogin(browser)
                print('[LOGIN]', 'Ensuring login on Bing...')
                checkBingLogin(browser, isMobile)
                return
    # Wait complete loading
    waitUntilVisible(browser, By.ID, 'loginHeader', 10)
    # Enter email
    print('[LOGIN]', 'Writing email...')
    browser.find_element(By.NAME, "loginfmt").send_keys(email)
    # Click next
    browser.find_element(By.ID, 'idSIButton9').click()
    # Wait 2 seconds
    time.sleep(5 if not FAST else 2)
    # Wait complete loading
    waitUntilVisible(browser, By.ID, 'loginHeader', 10)
    # Enter password
    browser.find_element(By.ID, "i0118").send_keys(pwd)
    # browser.execute_script("document.getElementById('i0118').value = '" + pwd + "';")
    print('[LOGIN]', 'Writing password...')
    # Click next
    browser.find_element(By.ID, 'idSIButton9').click()
    # Wait 5 seconds
    time.sleep(5)
    try:
        if browser.title == "We're updating our terms" or isElementExists(browser, By.ID, 'iAccrualForm'):
            time.sleep(2)
            browser.find_element(By.ID, 'iNext').click()
            time.sleep(5)
        if browser.title == 'Is your security info still accurate?' or isElementExists(browser, By.ID, 'iLooksGood'):
            time.sleep(2)
            browser.find_element(By.ID, 'iLooksGood').click()
            time.sleep(5)
        # Click No thanks on break free from password question
        if isElementExists(browser, By.ID, "setupAppDesc"):
            time.sleep(2)
            browser.find_element(By.ID, "iCancel").click()
            time.sleep(5)
        if ARGS.session:
            # Click Yes to stay signed in.
            browser.find_element(By.ID, 'idSIButton9').click()
        else:
            # Click No.
            browser.find_element(By.ID, 'idBtn_Back').click()
    except NoSuchElementException:
        # Check for if account has been locked.
        if browser.title == "Your account has been temporarily suspended" or isElementExists(browser, By.CLASS_NAME, "serviceAbusePageContainer  PageContainer"):
            LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your account has been locked !'
            FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
            updateLogs()
            cleanLogs()
            raise Exception(prRed('[ERROR] Your account has been locked !'))
        elif browser.title == "Help us protect your account":
            prRed('[ERROR] Unusual activity detected !')
            LOGS[CURRENT_ACCOUNT]['Last check'] = 'Unusual activity detected !'
            FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
            updateLogs()
            cleanLogs()
            if ARGS.telegram or ARGS.discord:
                message = createMessage()
                sendReportToMessenger(message)
            # input('Press any key to close...')
            os._exit(0)
        else:
            LOGS[CURRENT_ACCOUNT]['Last check'] = 'Unknown error !'
            FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
            updateLogs()
            cleanLogs()
            raise Exception(prRed('[ERROR] Unknown error !'))
    # Wait 5 seconds
    time.sleep(5)
    # Click Security Check
    print('[LOGIN]', 'Passing security checks...')
    try:
        browser.find_element(By.ID, 'iLandingViewAction').click()
    except (NoSuchElementException, ElementNotInteractableException) as e:
        pass
    # Wait complete loading
    try:
        waitUntilVisible(browser, By.ID, 'KmsiCheckboxField', 10)
    except (TimeoutException) as e:
        pass
    # Click next
    try:
        browser.find_element(By.ID, 'idSIButton9').click()
        # Wait 5 seconds
        time.sleep(5)
    except (NoSuchElementException, ElementNotInteractableException) as e:
        pass
    print('[LOGIN]', 'Logged-in !')
     # Check Microsoft Rewards
    print('[LOGIN] Logging into Microsoft Rewards...')
    RewardsLogin(browser)
    # Check Login
    print('[LOGIN]', 'Ensuring login on Bing...')
    checkBingLogin(browser, isMobile)

def RewardsLogin(browser: WebDriver):
    #Login into Rewards
    browser.get(BASE_URL)
    try:
        time.sleep(10 if not FAST else 5)
        # click on sign up button if needed
        if isElementExists(browser, By.ID, "start-earning-rewards-link"):
            browser.find_element(By.ID, "start-earning-rewards-link").click()
            time.sleep(5)
            browser.refresh()
            time.sleep(5)
    except:
        pass
    time.sleep(10 if not FAST else 5)
    # Check for ErrorMessage
    try:
        browser.find_element(By.ID, 'error').is_displayed()
        # Check wheter account suspended or not
        if browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute('innerHTML') == ' Uh oh, it appears your Microsoft Rewards account has been suspended.':
            LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your account has been suspended'
            LOGS[CURRENT_ACCOUNT]["Today's points"] = 'N/A'
            LOGS[CURRENT_ACCOUNT]["Points"] = 'N/A'
            cleanLogs()
            updateLogs()
            FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
            raise Exception(prRed('[ERROR] Your Microsoft Rewards account has been suspended !'))
        # Check whether Rewards is available in your region or not
        elif browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute('innerHTML') == 'Microsoft Rewards is not available in this country or region.':
            prRed('[ERROR] Microsoft Rewards is not available in this country or region !')
            # input('[ERROR] Press any key to close...')
            os._exit(0)
    except NoSuchElementException:
        pass

@func_set_timeout(300)
def checkBingLogin(browser: WebDriver, isMobile: bool = False):
    global POINTS_COUNTER
    #Access Bing.com
    browser.get('https://bing.com/')
    # Wait 15 seconds
    time.sleep(15 if not FAST else 5)
    # try to get points at first if account already logged in
    if ARGS.session:
        try:
            if not isMobile:
                try:
                    POINTS_COUNTER = int(browser.find_element(By.ID, 'id_rc').get_attribute('innerHTML'))
                except ValueError:
                    if browser.find_element(By.ID, 'id_s').is_displayed():
                        browser.find_element(By.ID, 'id_s').click()
                        time.sleep(15 if not FAST else 7)
                        checkBingLogin(browser, isMobile)
                    time.sleep(2)
                    POINTS_COUNTER = int(browser.find_element(By.ID, "id_rc").get_attribute("innerHTML").replace(",", ""))
            else:
                browser.find_element(By.ID, 'mHamburger').click()
                time.sleep(1)
                POINTS_COUNTER = int(browser.find_element(By.ID, 'fly_id_rc').get_attribute('innerHTML'))
        except:
            pass
        else:
            return None
    #Accept Cookies
    try:
        browser.find_element(By.ID, 'bnp_btn_accept').click()
    except:
        pass
    if isMobile:
        # close bing app banner
        if isElementExists(browser, By.ID, 'bnp_rich_div'):
            try:
                browser.find_element(By.XPATH, '//*[@id="bnp_bop_close_icon"]/img').click()
            except NoSuchElementException:
                pass
        try:
            time.sleep(1)
            browser.find_element(By.ID, 'mHamburger').click()
        except:
            try:
                browser.find_element(By.ID, 'bnp_btn_accept').click()
            except:
                pass
            time.sleep(1)
            if isElementExists(browser, By.XPATH, '//*[@id="bnp_ttc_div"]/div[1]/div[2]/span'):
                browser.execute_script("""var element = document.evaluate('/html/body/div[1]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                        element.remove();""")
                time.sleep(5)
            time.sleep(1)
            try:
                browser.find_element(By.ID, 'mHamburger').click()
            except:
                pass
        try:
            time.sleep(1)
            browser.find_element(By.ID, 'HBSignIn').click()
        except:
            pass
        try:
            time.sleep(2)
            browser.find_element(By.ID, 'iShowSkip').click()
            time.sleep(3)
        except:
            if str(browser.current_url).split('?')[0] == "https://account.live.com/proofs/Add":
                prRed('[LOGIN] Please complete the Security Check on ' + CURRENT_ACCOUNT)
                FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
                LOGS[CURRENT_ACCOUNT]['Last check'] = 'Requires manual check!'
                updateLogs()
                exit()
    #Wait 5 seconds
    time.sleep(5)
    # Refresh page
    browser.get('https://bing.com/')
    # Wait 15 seconds
    time.sleep(15 if not FAST else 5)
    #Update Counter
    try:
        if not isMobile:
            try:
                POINTS_COUNTER = int(browser.find_element(By.ID, 'id_rc').get_attribute('innerHTML'))
            except:
                if browser.find_element(By.ID, 'id_s').is_displayed():
                    browser.find_element(By.ID, 'id_s').click()
                    time.sleep(15 if not FAST else 7)
                    checkBingLogin(browser, isMobile)
                time.sleep(5)
                POINTS_COUNTER = int(browser.find_element(By.ID, "id_rc").get_attribute("innerHTML").replace(",", ""))
        else:
            try:
                browser.find_element(By.ID, 'mHamburger').click()
            except:
                try:
                    browser.find_element(By.ID, 'bnp_close_link').click()
                    time.sleep(4)
                    browser.find_element(By.ID, 'bnp_btn_accept').click()
                except:
                    pass
                time.sleep(1)
                browser.find_element(By.ID, 'mHamburger').click()
            time.sleep(1)
            POINTS_COUNTER = int(browser.find_element(By.ID, 'fly_id_rc').get_attribute('innerHTML'))
    except:
        checkBingLogin(browser, isMobile)

def waitUntilVisible(browser: WebDriver, by_: By, selector: str, time_to_wait: int = 10):
    WebDriverWait(browser, time_to_wait).until(ec.visibility_of_element_located((by_, selector)))

def waitUntilClickable(browser: WebDriver, by_: By, selector: str, time_to_wait: int = 10):
    WebDriverWait(browser, time_to_wait).until(ec.element_to_be_clickable((by_, selector)))

def waitUntilQuestionRefresh(browser: WebDriver):
    tries = 0
    refreshCount = 0
    while True:
        try:
            browser.find_elements(By.CLASS_NAME, 'rqECredits')[0]
            return True
        except:
            if tries < 10:
                tries += 1
                time.sleep(0.5)
            else:
                if refreshCount < 5:
                    browser.refresh()
                    refreshCount += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False

def waitUntilQuizLoads(browser: WebDriver):
    tries = 0
    refreshCount = 0
    while True:
        try:
            browser.find_element(By.XPATH, '//*[@id="currentQuestionContainer"]')
            return True
        except:
            if tries < 10:
                tries += 1
                time.sleep(0.5)
            else:
                if refreshCount < 5:
                    browser.refresh()
                    refreshCount += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False

def findBetween(s: str, first: str, last: str) -> str:
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""

def getCCodeLangAndOffset() -> tuple:
    try:
        nfo = ipapi.location()
        lang = nfo['languages'].split(',')[0]
        geo = nfo['country']
        tz = str(round(int(nfo['utc_offset']) / 100 * 60))
        return(lang, geo, tz)
    # Due to limits that ipapi has some times it returns error so I put US and English as default, you may change it at whatever you need.
    except:
        return('en-US', 'US', '-480')

def getGoogleTrends(numberOfwords: int) -> list:
    search_terms = []
    i = 0
    while len(search_terms) < numberOfwords :
        i += 1
        r = requests.get('https://trends.google.com/trends/api/dailytrends?hl=' + LANG + '&ed=' + str((date.today() - timedelta(days = i)).strftime('%Y%m%d')) + '&geo=' + GEO + '&ns=15')
        google_trends = json.loads(r.text[6:])
        for topic in google_trends['default']['trendingSearchesDays'][0]['trendingSearches']:
            search_terms.append(topic['title']['query'].lower())
            for related_topic in topic['relatedQueries']:
                search_terms.append(related_topic['query'].lower())
        search_terms = list(set(search_terms))
    del search_terms[numberOfwords:(len(search_terms)+1)]
    return search_terms

def getRelatedTerms(word: str) -> list:
    try:
        r = requests.get('https://api.bing.com/osjson.aspx?query=' + word, headers = {'User-agent': PC_USER_AGENT})
        return r.json()[1]
    except:
        return []

def resetTabs(browser: WebDriver):
    try:
        curr = browser.current_window_handle

        for handle in browser.window_handles:
            if handle != curr:
                browser.switch_to.window(handle)
                time.sleep(0.5)
                browser.close()
                time.sleep(0.5)

        browser.switch_to.window(curr)
        time.sleep(0.5)
        browser.get(BASE_URL)
        waitUntilVisible(browser, By.ID, 'app-host', 30)
    except:
        browser.get(BASE_URL)
        waitUntilVisible(browser, By.ID, 'app-host', 30)

def getAnswerCode(key: str, string: str) -> str:
	t = 0
	for i in range(len(string)):
		t += ord(string[i])
	t += int(key[-2:], 16)
	return str(t)

def bingSearches(browser: WebDriver, numberOfSearches: int, isMobile: bool = False):
    global POINTS_COUNTER
    i = 0
    r = RandomWords()
    search_terms = r.get_random_words(limit = numberOfSearches)
    if search_terms == None:
        search_terms = getGoogleTrends(numberOfSearches)
    for word in search_terms:
        i += 1
        print('[BING]', str(i) + "/" + str(numberOfSearches))
        points = bingSearch(browser, word, isMobile)
        if points <= POINTS_COUNTER :
            relatedTerms = getRelatedTerms(word)
            for term in relatedTerms :
                points = bingSearch(browser, term, isMobile)
                if points >= POINTS_COUNTER:
                    break
        if points > 0:
            POINTS_COUNTER = points
        else:
            break

def bingSearch(browser: WebDriver, word: str, isMobile: bool):
    try:
        if not isMobile:
            browser.find_element(By.ID, 'sb_form_q').clear()
            time.sleep(1)
        else:
            browser.get('https://bing.com')
    except:
        browser.get('https://bing.com')
    time.sleep(2)
    searchbar = browser.find_element(By.ID, 'sb_form_q')
    if FAST:
        searchbar.send_keys(word)
        time.sleep(1)
    else:
        for char in word:
            searchbar.send_keys(char)
            time.sleep(0.33)
    searchbar.submit()
    time.sleep(random.randint(12, 24) if not FAST else random.randint(6, 9))
    points = 0
    try:
        if not isMobile:
            try:
                points = int(browser.find_element(By.ID, 'id_rc').get_attribute('innerHTML'))
            except ValueError:
                points = int(browser.find_element(By.ID, 'id_rc').get_attribute('innerHTML').replace(",", ""))
        else:
            try :
                browser.find_element(By.ID, 'mHamburger').click()
            except UnexpectedAlertPresentException:
                try :
                    browser.switch_to.alert.accept()
                    time.sleep(1)
                    browser.find_element(By.ID, 'mHamburger').click()
                except NoAlertPresentException :
                    pass
            time.sleep(1)
            points = int(browser.find_element(By.ID, 'fly_id_rc').get_attribute('innerHTML'))
    except:
        pass
    return points

def completePromotionalItems(browser: WebDriver):
    try:
        item = getDashboardData(browser)["promotionalItem"]
        if (item["pointProgressMax"] == 100 or item["pointProgressMax"] == 200) and item["complete"] == False and item["destinationUrl"] == BASE_URL:
            browser.find_element(By.XPATH, '//*[@id="promo-item"]/section/div/div/div/a').click()
            time.sleep(1)
            browser.switch_to.window(window_name = browser.window_handles[1])
            time.sleep(8 if not FAST else 5)
            browser.close()
            time.sleep(2)
            browser.switch_to.window(window_name = browser.window_handles[0])
            time.sleep(2)
    except:
        pass

def completeDailySetSearch(browser: WebDriver, cardNumber: int):
    time.sleep(5)
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section/div/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-daily-set-item-content/div/a/div/span').click()
    time.sleep(1)
    browser.switch_to.window(window_name = browser.window_handles[1])
    time.sleep(random.randint(13, 17) if not FAST else random.randint(6, 9))
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name = browser.window_handles[0])
    time.sleep(2)

def completeDailySetSurvey(browser: WebDriver, cardNumber: int):
    time.sleep(5)
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section/div/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-daily-set-item-content/div/a/div/span').click()
    time.sleep(1)
    browser.switch_to.window(window_name = browser.window_handles[1])
    time.sleep(8 if not FAST else 5)
    # Accept cookie popup
    if isElementExists(browser, By.ID, 'bnp_container'):
        browser.find_element(By.ID, 'bnp_btn_accept').click()
        time.sleep(2)
    # Click on later on Bing wallpaper app popup
    if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
        browser.find_element(By.ID, 'bnp_hfly_cta2').click()
        time.sleep(2)
    browser.find_element(By.ID, "btoption" + str(random.randint(0, 1))).click()
    time.sleep(random.randint(10, 15) if not FAST else 7)
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name = browser.window_handles[0])
    time.sleep(2)

def completeDailySetQuiz(browser: WebDriver, cardNumber: int):
    time.sleep(5)
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section[1]/div/mee-card-group[1]/div[1]/mee-card[{str(cardNumber)}]/div[1]/card-content[1]/mee-rewards-daily-set-item-content[1]/div[1]/a[1]/div[3]/span[1]').click()
    time.sleep(3)
    browser.switch_to.window(window_name = browser.window_handles[1])
    time.sleep(12 if not FAST else random.randint(5, 8))
    if not waitUntilQuizLoads(browser):
        resetTabs(browser)
        return
    # Accept cookie popup
    if isElementExists(browser, By.ID, 'bnp_container'):
        browser.find_element(By.ID, 'bnp_btn_accept').click()
        time.sleep(2)
    browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
    waitUntilVisible(browser, By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10 if not FAST else 5)
    time.sleep(3)
    numberOfQuestions = browser.execute_script("return _w.rewardsQuizRenderInfo.maxQuestions")
    numberOfOptions = browser.execute_script("return _w.rewardsQuizRenderInfo.numberOfOptions")
    for _ in range(numberOfQuestions):
        if numberOfOptions == 8:
            answers = []
            for i in range(8):
                if browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute("iscorrectoption").lower() == "true":
                    answers.append("rqAnswerOption" + str(i))
            for answer in answers:
                # Click on later on Bing wallpaper app popup
                if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
                    browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                    time.sleep(2)
                browser.find_element(By.ID, answer).click()
                time.sleep(5)
                if not waitUntilQuestionRefresh(browser):
                    return
            time.sleep(5)
        elif numberOfOptions == 4:
            correctOption = browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")
            for i in range(4):
                if browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute("data-option") == correctOption:
                    # Click on later on Bing wallpaper app popup
                    if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
                        browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                        time.sleep(2)
                    browser.find_element(By.ID, "rqAnswerOption" + str(i)).click()
                    time.sleep(5)
                    if not waitUntilQuestionRefresh(browser):
                        return
                    break
            time.sleep(5)
    time.sleep(5)
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name = browser.window_handles[0])
    time.sleep(2)

def completeDailySetVariableActivity(browser: WebDriver, cardNumber: int):
    time.sleep(2)
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section/div/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-daily-set-item-content/div/a/div/span').click()
    time.sleep(1)
    browser.switch_to.window(window_name = browser.window_handles[1])
    time.sleep(8 if not FAST else 5)
    # Accept cookie popup
    if isElementExists(browser, By.ID, 'bnp_container'):
        browser.find_element(By.ID, 'bnp_btn_accept').click()
        time.sleep(2)
    try :
        browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        waitUntilVisible(browser, By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 3)
    except (NoSuchElementException, TimeoutException):
        try:
            counter = str(browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[:-1][1:]
            numberOfQuestions = max([int(s) for s in counter.split() if s.isdigit()])
            for question in range(numberOfQuestions):
                # Click on later on Bing wallpaper app popup
                if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
                    browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                    time.sleep(2)

                browser.execute_script(f'document.evaluate("//*[@id=\'QuestionPane{str(question)}\']/div[1]/div[2]/a[{str(random.randint(1, 3))}]/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
                time.sleep(8)
            time.sleep(5)
            browser.close()
            time.sleep(2)
            browser.switch_to.window(window_name=browser.window_handles[0])
            time.sleep(2)
            return
        except NoSuchElementException:
            time.sleep(random.randint(5, 9))
            browser.close()
            time.sleep(2)
            browser.switch_to.window(window_name = browser.window_handles[0])
            time.sleep(2)
            return
    time.sleep(3)
    correctAnswer = browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")
    if browser.find_element(By.ID, "rqAnswerOption0").get_attribute("data-option") == correctAnswer:
        browser.find_element(By.ID, "rqAnswerOption0").click()
    else :
        browser.find_element(By.ID, "rqAnswerOption1").click()
    time.sleep(10)
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name = browser.window_handles[0])
    time.sleep(2)

def completeDailySetThisOrThat(browser: WebDriver, cardNumber: int):
    time.sleep(2)
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section/div/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-daily-set-item-content/div/a/div/span').click()
    time.sleep(1)
    browser.switch_to.window(window_name=browser.window_handles[1])
    time.sleep(15 if not FAST else random.randint(5, 8))
    # Accept cookie popup
    if isElementExists(browser, By.ID, 'bnp_container'):
        browser.find_element(By.ID, 'bnp_btn_accept').click()
        time.sleep(2)
    if not waitUntilQuizLoads(browser):
        resetTabs(browser)
        return
    browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
    waitUntilVisible(browser, By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10 if not FAST else 5)
    time.sleep(5)
    for _ in range(10):
        # Click on later on Bing wallpaper app popup
        if isElementExists(browser, By.ID, 'b_notificationContainer_bop'):
            browser.find_element(By.ID, 'bnp_hfly_cta2').click()
            time.sleep(2)

        answerEncodeKey = browser.execute_script("return _G.IG")

        answer1 = browser.find_element(By.ID, "rqAnswerOption0")
        answer1Title = answer1.get_attribute('data-option')
        answer1Code = getAnswerCode(answerEncodeKey, answer1Title)

        answer2 = browser.find_element(By.ID, "rqAnswerOption1")
        answer2Title = answer2.get_attribute('data-option')
        answer2Code = getAnswerCode(answerEncodeKey, answer2Title)

        correctAnswerCode = browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")

        if (answer1Code == correctAnswerCode):
            answer1.click()
            time.sleep(15 if not FAST else 7)
        elif (answer2Code == correctAnswerCode):
            answer2.click()
            time.sleep(15 if not FAST else 7)

    time.sleep(5)
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name=browser.window_handles[0])
    time.sleep(2)

def getDashboardData(browser: WebDriver) -> dict:
    dashboard = findBetween(browser.find_element(By.XPATH, '/html/body').get_attribute('innerHTML'), "var dashboard = ", ";\n        appDataModule.constant(\"prefetchedDashboard\", dashboard);")
    dashboard = json.loads(dashboard)
    return dashboard

def completeDailySet(browser: WebDriver):
    print('[DAILY SET]', 'Trying to complete the Daily Set...')
    d = getDashboardData(browser)
    error = False
    todayDate = datetime.today().strftime('%m/%d/%Y')
    todayPack = []
    for date, data in d['dailySetPromotions'].items():
        if date == todayDate:
            todayPack = data
    for activity in todayPack:
        try:
            if activity['complete'] == False:
                cardNumber = int(activity['offerId'][-1:])
                if activity['promotionType'] == "urlreward":
                    print('[DAILY SET]', 'Completing search of card ' + str(cardNumber))
                    completeDailySetSearch(browser, cardNumber)
                if activity['promotionType'] == "quiz":
                    if activity['pointProgressMax'] == 50 and activity['pointProgress'] == 0:
                        print('[DAILY SET]', 'Completing This or That of card ' + str(cardNumber))
                        completeDailySetThisOrThat(browser, cardNumber)
                    elif (activity['pointProgressMax'] == 40 or activity['pointProgressMax'] == 30) and activity['pointProgress'] == 0:
                        print('[DAILY SET]', 'Completing quiz of card ' + str(cardNumber))
                        completeDailySetQuiz(browser, cardNumber)
                    elif activity['pointProgressMax'] == 10 and activity['pointProgress'] == 0:
                        searchUrl = urllib.parse.unquote(urllib.parse.parse_qs(urllib.parse.urlparse(activity['destinationUrl']).query)['ru'][0])
                        searchUrlQueries = urllib.parse.parse_qs(urllib.parse.urlparse(searchUrl).query)
                        filters = {}
                        for filter in searchUrlQueries['filters'][0].split(" "):
                            filter = filter.split(':', 1)
                            filters[filter[0]] = filter[1]
                        if "PollScenarioId" in filters:
                            print('[DAILY SET]', 'Completing poll of card ' + str(cardNumber))
                            completeDailySetSurvey(browser, cardNumber)
                        else:
                            print('[DAILY SET]', 'Completing quiz of card ' + str(cardNumber))
                            completeDailySetVariableActivity(browser, cardNumber)
        except:
            error = True
            resetTabs(browser)
    if not error:
        prGreen("[DAILY SET] Completed the Daily Set successfully !")
    else:
        prYellow("[DAILY SET] Daily Set did not completed successfully ! Streak not increased")
    LOGS[CURRENT_ACCOUNT]['Daily'] = True
    updateLogs()

def getAccountPoints(browser: WebDriver) -> int:
    return getDashboardData(browser)['userStatus']['availablePoints']

def completePunchCard(browser: WebDriver, url: str, childPromotions: dict):
    browser.get(url)
    for child in childPromotions:
        if child['complete'] == False:
            if child['promotionType'] == "urlreward":
                browser.execute_script("document.getElementsByClassName('offer-cta')[0].click()")
                time.sleep(1)
                browser.switch_to.window(window_name = browser.window_handles[1])
                time.sleep(random.randint(5, 8)) if FAST else time.sleep(random.randint(13, 17))
                browser.close()
                time.sleep(2)
                browser.switch_to.window(window_name = browser.window_handles[0])
                time.sleep(2)
            if child['promotionType'] == "quiz" and child['pointProgressMax'] >= 50 :
                browser.find_element(By.XPATH, '//*[@id="rewards-dashboard-punchcard-details"]/div[2]/div[2]/div[7]/div[3]/div[1]/a').click()
                time.sleep(1)
                browser.switch_to.window(window_name = browser.window_handles[1])
                time.sleep(15)
                try:
                    browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
                except:
                    pass
                time.sleep(5)
                waitUntilVisible(browser, By.XPATH, '//*[@id="currentQuestionContainer"]', 10 if not FAST else 5)
                numberOfQuestions = browser.execute_script("return _w.rewardsQuizRenderInfo.maxQuestions")
                AnswerdQuestions = browser.execute_script("return _w.rewardsQuizRenderInfo.CorrectlyAnsweredQuestionCount")
                numberOfQuestions -= AnswerdQuestions
                for question in range(numberOfQuestions):
                    answer = browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")
                    browser.find_element(By.XPATH, f'//input[@value="{answer}"]').click()
                    time.sleep(15 if not FAST else 7)
                time.sleep(5)
                browser.close()
                time.sleep(2)
                browser.switch_to.window(window_name=browser.window_handles[0])
                time.sleep(2)
                browser.refresh()
                break
            elif child['promotionType'] == "quiz" and child['pointProgressMax'] < 50:
                browser.execute_script("document.getElementsByClassName('offer-cta')[0].click()")
                time.sleep(1)
                browser.switch_to.window(window_name = browser.window_handles[1])
                time.sleep(8)
                counter = str(browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[:-1][1:]
                numberOfQuestions = max([int(s) for s in counter.split() if s.isdigit()])
                for question in range(numberOfQuestions):
                    browser.execute_script('document.evaluate("//*[@id=\'QuestionPane' + str(question) + '\']/div[1]/div[2]/a[' + str(random.randint(1, 3)) + ']/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
                    time.sleep(10 if not FAST else 5)
                time.sleep(5)
                browser.close()
                time.sleep(2)
                browser.switch_to.window(window_name = browser.window_handles[0])
                time.sleep(2)
                browser.refresh()
                break

def completePunchCards(browser: WebDriver):
    print('[PUNCH CARDS]', 'Trying to complete the Punch Cards...')
    punchCards = getDashboardData(browser)['punchCards']
    for punchCard in punchCards:
        try:
            if punchCard['parentPromotion'] != None and punchCard['childPromotions'] != None and punchCard['parentPromotion']['complete'] == False and punchCard['parentPromotion']['pointProgressMax'] != 0:
                url = punchCard['parentPromotion']['attributes']['destination']
                if browser.current_url.startswith('https://rewards.'):
                    path = url.replace('https://rewards.microsoft.com', '')
                    new_url = 'https://rewards.microsoft.com/dashboard/'
                    userCode = path[11:15]
                    dest = new_url + userCode + path.split(userCode)[1]
                else:
                    path = url.replace('https://account.microsoft.com/rewards/dashboard/','')
                    new_url = 'https://account.microsoft.com/rewards/dashboard/'
                    userCode = path[:4]
                    dest = new_url + userCode + path.split(userCode)[1]
                completePunchCard(browser, url, punchCard['childPromotions'])
        except:
            resetTabs(browser)
    time.sleep(2)
    browser.get(BASE_URL)
    time.sleep(2)
    LOGS[CURRENT_ACCOUNT]['Punch cards'] = True
    updateLogs()
    prGreen('[PUNCH CARDS] Completed the Punch Cards successfully !')

def completeMorePromotionSearch(browser: WebDriver, cardNumber: int):
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-more-activities-card/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-more-activities-card-item/div/a/div/span').click()
    time.sleep(1)
    browser.switch_to.window(window_name = browser.window_handles[1])
    time.sleep(random.randint(13, 17) if not FAST else random.randint(5, 8))
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name = browser.window_handles[0])
    time.sleep(2)

def completeMorePromotionQuiz(browser: WebDriver, cardNumber: int):
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-more-activities-card/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-more-activities-card-item/div/a/div/span').click()
    time.sleep(1)
    browser.switch_to.window(window_name=browser.window_handles[1])
    time.sleep(8 if not FAST else 5)
    if not waitUntilQuizLoads(browser):
        resetTabs(browser)
        return
    CurrentQuestionNumber = browser.execute_script("return _w.rewardsQuizRenderInfo.currentQuestionNumber")
    if CurrentQuestionNumber == 1 and isElementExists(browser, By.XPATH, '//*[@id="rqStartQuiz"]'):
        browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
    waitUntilVisible(browser, By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10 if not FAST else 5)
    time.sleep(3)
    numberOfQuestions = browser.execute_script("return _w.rewardsQuizRenderInfo.maxQuestions")
    Questions = numberOfQuestions - CurrentQuestionNumber + 1
    numberOfOptions = browser.execute_script("return _w.rewardsQuizRenderInfo.numberOfOptions")
    for _ in range(Questions):
        if numberOfOptions == 8:
            answers = []
            for i in range(8):
                if browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute("iscorrectoption").lower() == "true":
                    answers.append("rqAnswerOption" + str(i))
            for answer in answers:
                browser.find_element(By.ID, answer).click()
                time.sleep(5)
                if not waitUntilQuestionRefresh(browser):
                    return
            time.sleep(5)
        elif numberOfOptions == 4:
            correctOption = browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")
            for i in range(4):
                if browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute("data-option") == correctOption:
                    browser.find_element(By.ID, "rqAnswerOption" + str(i)).click()
                    time.sleep(5)
                    if not waitUntilQuestionRefresh(browser):
                        return
                    break
            time.sleep(5)
    time.sleep(5)
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name=browser.window_handles[0])
    time.sleep(2)

def completeMorePromotionABC(browser: WebDriver, cardNumber: int):
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-more-activities-card/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-more-activities-card-item/div/a/div/span').click()
    time.sleep(1)
    browser.switch_to.window(window_name=browser.window_handles[1])
    time.sleep(8 if not FAST else 5)
    counter = str(browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[:-1][1:]
    numberOfQuestions = max([int(s) for s in counter.split() if s.isdigit()])
    for question in range(numberOfQuestions):
        browser.execute_script(f'document.evaluate("//*[@id=\'QuestionPane{str(question)}\']/div[1]/div[2]/a[{str(random.randint(1, 3))}]/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
        time.sleep(8 if not FAST else 5)
    time.sleep(5)
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name=browser.window_handles[0])
    time.sleep(2)

def completeMorePromotionThisOrThat(browser: WebDriver, cardNumber: int):
    browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-more-activities-card/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-more-activities-card-item/div/a/div/span').click()
    time.sleep(1)
    browser.switch_to.window(window_name=browser.window_handles[1])
    time.sleep(8 if not FAST else 5)
    if not waitUntilQuizLoads(browser):
        resetTabs(browser)
        return
    CrrentQuestionNumber = browser.execute_script("return _w.rewardsQuizRenderInfo.currentQuestionNumber")
    NumberOfQuestionsLeft = 10 - CrrentQuestionNumber + 1
    if CrrentQuestionNumber == 1 and isElementExists(browser, By.XPATH, '//*[@id="rqStartQuiz"]'):
        browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
    waitUntilVisible(browser, By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10 if not FAST else 5)
    time.sleep(3)
    for _ in range(NumberOfQuestionsLeft):
        answerEncodeKey = browser.execute_script("return _G.IG")

        answer1 = browser.find_element(By.ID, "rqAnswerOption0")
        answer1Title = answer1.get_attribute('data-option')
        answer1Code = getAnswerCode(answerEncodeKey, answer1Title)

        answer2 = browser.find_element(By.ID, "rqAnswerOption1")
        answer2Title = answer2.get_attribute('data-option')
        answer2Code = getAnswerCode(answerEncodeKey, answer2Title)

        correctAnswerCode = browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")

        if (answer1Code == correctAnswerCode):
            answer1.click()
            time.sleep(8 if not FAST else 5)
        elif (answer2Code == correctAnswerCode):
            answer2.click()
            time.sleep(8 if not FAST else 5)

    time.sleep(5)
    browser.close()
    time.sleep(2)
    browser.switch_to.window(window_name=browser.window_handles[0])
    time.sleep(2)

def completeMorePromotions(browser: WebDriver):
    print('[MORE PROMO]', 'Trying to complete More Promotions...')
    morePromotions = getDashboardData(browser)['morePromotions']
    i = 0
    for promotion in morePromotions:
        try:
            i += 1
            if promotion['complete'] == False and promotion['pointProgressMax'] != 0:
                if promotion['promotionType'] == "urlreward":
                    completeMorePromotionSearch(browser, i)
                elif promotion['promotionType'] == "quiz":
                    if promotion['pointProgressMax'] == 10:
                        completeMorePromotionABC(browser, i)
                    elif promotion['pointProgressMax'] == 30 or promotion['pointProgressMax'] == 40:
                        completeMorePromotionQuiz(browser, i)
                    elif promotion['pointProgressMax'] == 50:
                        completeMorePromotionThisOrThat(browser, i)
                else:
                    if promotion['pointProgressMax'] == 100 or promotion['pointProgressMax'] == 200:
                        completeMorePromotionSearch(browser, i)
            if promotion['complete'] == False and promotion['pointProgressMax'] == 100 and promotion['promotionType'] == "" \
                and promotion['destinationUrl'] == BASE_URL:
                completeMorePromotionSearch(browser, i)
        except:
            resetTabs(browser)
    LOGS[CURRENT_ACCOUNT]['More promotions'] = True
    updateLogs()
    prGreen('[MORE PROMO] Completed More Promotions successfully !')

def completeMSNShoppingGame(browser: WebDriver):

    def expandShadowElement(element, index: int = None) -> Union[List[WebElement], WebElement]:
        """Returns childrens of shadow element"""
        if index is not None:
            shadow_root = WebDriverWait(browser, 45).until(
                ec.visibility_of(browser.execute_script('return arguments[0].shadowRoot.children', element)[index])
            )
        else:
            # wait to visible one element then get the list
            WebDriverWait(browser, 45).until(
                ec.visibility_of(browser.execute_script('return arguments[0].shadowRoot.children', element)[0])
            )
            shadow_root = browser.execute_script('return arguments[0].shadowRoot.children', element)
        return shadow_root

    def getChildren(element) -> List[WebElement]:
        children = browser.execute_script('return arguments[0].children', element)
        return children

    def getSignInState() -> WebElement:
        """check wheather user is signed in or not and return the button to sign in"""
        script_to_user_pref_container = 'document.getElementsByTagName("shopping-page-base")[0]\
            .shadowRoot.children[0].children[1].children[0]\
            .shadowRoot.children[0].shadowRoot.children[0]\
            .getElementsByClassName("user-pref-container")[0]'
        WebDriverWait(browser, 60).until(ec.visibility_of(
            browser.execute_script(f'return {script_to_user_pref_container}')
            )
        )
        button = WebDriverWait(browser, 60).until(ec.visibility_of(
                browser.execute_script(
                    f'return {script_to_user_pref_container}.\
                    children[0].children[0].shadowRoot.children[0].\
                    getElementsByClassName("me-control")[0]'
                )
            )
        )
        return button

    def signIn() -> None:
        sign_in_button = getSignInState()
        sign_in_button.click()
        print("[MSN GAME] Signing in...")
        time.sleep(5)
        waitUntilVisible(browser, By.ID, 'newSessionLink', 10)
        browser.find_element(By.ID, 'newSessionLink').click()
        waitUntilVisible(browser, By.TAG_NAME, 'shopping-page-base', 60 if not FAST else 30)
        expandShadowElement(browser.find_element(By.TAG_NAME, 'shopping-page-base'), 0)
        getSignInState()

    def getGamingCard() -> WebElement:
        shopping_page_base_childs = expandShadowElement(browser.find_element(By.TAG_NAME, 'shopping-page-base'), 0)
        shopping_homepage = shopping_page_base_childs.find_element(By.TAG_NAME, 'shopping-homepage')
        msft_feed_layout = expandShadowElement(shopping_homepage, 0).find_element(By.TAG_NAME, 'msft-feed-layout')
        msn_shopping_game_pane = expandShadowElement(msft_feed_layout)
        for element in msn_shopping_game_pane:
            if element.get_attribute("gamestate") == "active":
                return element

    def clickCorrectAnswer() -> None:
        options_container = expandShadowElement(gaming_card, 1)
        options_elements = getChildren(getChildren(options_container)[1])
        # click on the correct answer in options_elements
        correct_answer = options_elements[int(gaming_card.get_attribute("_correctAnswerIndex"))]
        # hover to show the select button
        correct_answer.click()
        time.sleep(1)
        # click 'select' button
        select_button = correct_answer.find_element(By.CLASS_NAME, 'shopping-select-overlay-button')
        WebDriverWait(browser, 5).until(ec.element_to_be_clickable(select_button))
        select_button.click()

    def clickPlayAgain() -> None:
        time.sleep(random.randint(4, 6))
        options_container = expandShadowElement(gaming_card)[1]
        getChildren(options_container)[0].find_element(By.TAG_NAME, 'button').click()

    try:
        tries = 0
        print("[MSN GAME] Trying to complete MSN shopping game...")
        print("[MSN GAME] Checking if user is signed in ...")
        while tries <= 4:
            tries += 1
            browser.get("https://www.msn.com/en-us/shopping")
            waitUntilVisible(browser, By.TAG_NAME, 'shopping-page-base', 60 if not FAST else 30)
            time.sleep(15 if not FAST else 8)
            try:
                sign_in_button = getSignInState()
            except:
                if tries == 4:
                    raise ElementNotVisibleException("Sign in button did not show up")
            else:
                break
        time.sleep(5)
        if "Sign in" in sign_in_button.text:
            signIn()
        gaming_card = getGamingCard()
        print("[MSN GAME] Answering questions ...")
        for _ in range(10):
            try:
                clickCorrectAnswer()
                clickPlayAgain()
                time.sleep(random.randint(5, 7))
            except (NoSuchElementException, JavascriptException):
                break
    except:
        prYellow("[MSN GAME] Failed to complete MSN shopping game !")
        resetTabs(browser)
    else:
        prGreen("[MSN GAME] Completed MSN shopping game successfully !")
        browser.get(BASE_URL)
    finally:
        LOGS[CURRENT_ACCOUNT]["MSN shopping game"] = True
        updateLogs()

def getRemainingSearches(browser: WebDriver):
    dashboard = getDashboardData(browser)
    searchPoints = 1
    counters = dashboard['userStatus']['counters']
    if not 'pcSearch' in counters:
        return 0, 0
    progressDesktop = counters['pcSearch'][0]['pointProgress'] + counters['pcSearch'][1]['pointProgress']
    targetDesktop = counters['pcSearch'][0]['pointProgressMax'] + counters['pcSearch'][1]['pointProgressMax']
    if targetDesktop == 33 :
        #Level 1 EU
        searchPoints = 3
    elif targetDesktop == 55 :
        #Level 1 US
        searchPoints = 5
    elif targetDesktop == 102 :
        #Level 2 EU
        searchPoints = 3
    elif targetDesktop >= 170 :
        #Level 2 US
        searchPoints = 5
    remainingDesktop = int((targetDesktop - progressDesktop) / searchPoints)
    remainingMobile = 0
    if dashboard['userStatus']['levelInfo']['activeLevel'] != "Level1":
        progressMobile = counters['mobileSearch'][0]['pointProgress']
        targetMobile = counters['mobileSearch'][0]['pointProgressMax']
        remainingMobile = int((targetMobile - progressMobile) / searchPoints)
    return remainingDesktop, remainingMobile

def getRedeemGoal(browser: WebDriver):
    user_status = getDashboardData(browser)["userStatus"]
    return (user_status["redeemGoal"]["title"], user_status["redeemGoal"]["price"])

def isElementExists(browser: WebDriver, _by: By, element: str) -> bool:
    '''Returns True if given element exists else False'''
    try:
        browser.find_element(_by, element)
    except NoSuchElementException:
        return False
    return True

def accountBrowser(chosen_account: str):
    """Setup browser for chosen account"""
    global CURRENT_ACCOUNT
    for account in ACCOUNTS:
        if account["username"].lower() == chosen_account.lower():
            CURRENT_ACCOUNT = account["username"]
            break
    else:
        return None
    browserSetup(False, PC_USER_AGENT)

def argumentParser():
    '''getting args from command line'''

    def isValidTime(time: str):
        '''check the time format and return the time if it is valid, otherwise return parser error'''
        try:
            t = datetime.strptime(time, "%H:%M").strftime("%H:%M")
        except ValueError:
            parser.error("Invalid time format, use HH:MM")
        else:
            return t

    def isSessionExist(session: str):
        '''check if the session is valid and return the session if it is valid, otherwise return parser error'''
        if Path(f"{Path(__file__).parent}/Profiles/{session}").exists():
            return session
        else:
            parser.error(f"Session not found for {session}")

    parser = ArgumentParser(
        description="Microsoft Rewards Farmer V2.1",
        allow_abbrev=False,
        usage="You may use execute the program with the default config or use arguments to configure available options."
    )
    parser.add_argument('--accounts',
                        default='/config/addons_config/msrewards/accounts.json',
                        help='[Optional] Path to accounts json file',
                        required=False)
    parser.add_argument('--everyday',
                        action='store_true',
                        help='[Optional] This argument will make the script run everyday at the time you start.',
                        required=False)
    parser.add_argument('--headless',
                        help='[Optional] Enable headless browser.',
                        action = 'store_true',
                        required=False)
    parser.add_argument('--session',
                        help='[Optional] Creates session for each account and use it.',
                        action='store_true',
                        required=False)
    parser.add_argument('--error',
                        help='[Optional] Display errors when app fails.',
                        action='store_true',
                        required=False)
    parser.add_argument('--fast',
                        help="[Optional] Reduce delays where ever it's possible to make script faster.",
                        action='store_true',
                        required=False)
    parser.add_argument('--telegram',
                        metavar=('<API_TOKEN>', '<CHAT_ID>'),
                        nargs=2,
                        help='[Optional] This argument takes token and chat id to send logs to Telegram.',
                        type=str,
                        required=False)
    parser.add_argument('--discord',
                        metavar='<WEBHOOK_URL>',
                        nargs=1,
                        help='[Optional] This argument takes webhook url to send logs to Discord.',
                        type=str,
                        required=False)
    parser.add_argument('--edge',
                        help='[Optional] Use Microsoft Edge webdriver instead of Chrome.',
                        action='store_true',
                        required=False,)
    parser.add_argument('--shutdown',
                        metavar=('<TIME (SECONDS)>'),
                        help='[Optional] You can pass time in seconds to shutdown the computer after the script is done, if time not provided default is 10.',
                        nargs="?",
                        type=int,
                        const=10,
                        required=False)
    parser.add_argument('--account-browser',
                        nargs=1,
                        type=isSessionExist,
                        help='[Optional] Open browser session for chosen account.',
                        required=False)
    parser.add_argument('--start-at',
                        metavar='<HH:MM>',
                        nargs=1,
                        type=isValidTime,
                        )
    parser.add_argument('--autoexit',
                        help='[Optional] Automatically exit the script once it has completed.',
                        action='store_true',
                        required=False)

    args = parser.parse_args()
    if args.fast:
        global FAST
        FAST = True
    if len(sys.argv) > 1:
        for arg in vars(args):
            prBlue(f"[INFO] {arg}: {getattr(args, arg)}")
    return args

def logs():
    '''Read logs and check whether account farmed or not'''
    global LOGS
    shared_items =[]
    try:
        # Read datas on 'logs_accounts.txt'
        LOGS = json.load(open(f"{Path(__file__).parent}/Logs_{account_path.stem}.txt", "r"))
        LOGS.pop("Elapsed time", None)
        # sync accounts and logs file for new accounts or remove accounts from logs.
        for user in ACCOUNTS:
            shared_items.append(user['username'])
            if not user['username'] in LOGS.keys():
                LOGS[user["username"]] = {"Last check": "",
                                        "Today's points": 0,
                                        "Points": 0}
        if shared_items != LOGS.keys():
            diff = LOGS.keys() - shared_items
            for accs in list(diff):
                del LOGS[accs]

        # check that if any of accounts has farmed today or not.
        for account in LOGS.keys():
            if LOGS[account]["Last check"] == str(date.today()) and list(LOGS[account].keys()) == ['Last check', "Today's points", 'Points']:
                FINISHED_ACCOUNTS.append(account)
            elif LOGS[account]['Last check'] == 'Your account has been suspended':
                FINISHED_ACCOUNTS.append(account)
            elif LOGS[account]['Last check'] == str(date.today()) and list(LOGS[account].keys()) == [
                'Last check',
                "Today's points",
                'Points',
                'Daily',
                'Punch cards',
                'More promotions',
                'MSN shopping game',
                'PC searches'
            ]:
                continue
            else:
                LOGS[account]['Daily'] = False
                LOGS[account]['Punch cards'] = False
                LOGS[account]['More promotions'] = False
                LOGS[account]['MSN shopping game'] = False
                LOGS[account]['PC searches'] = False
            if not isinstance(LOGS[account]["Points"], int):
                LOGS[account]["Points"] = 0
        updateLogs()
        prGreen('\n[LOGS] Logs loaded successfully.\n')
    except FileNotFoundError:
        prRed(f'\n[LOGS] "Logs_{account_path.stem}.txt" file not found.')
        LOGS = {}
        for account in ACCOUNTS:
            LOGS[account["username"]] = {"Last check": "",
                                        "Today's points": 0,
                                        "Points": 0,
                                        "Daily": False,
                                        "Punch cards": False,
                                        "More promotions": False,
                                        "MSN shopping game": False,
                                        "PC searches": False}
        updateLogs()
        prGreen(f'[LOGS] "Logs_{account_path.stem}.txt" created.\n')

def updateLogs():
    _logs = copy.deepcopy(LOGS)
    for account in _logs:
        if account == "Elapsed time":
            continue
        _logs[account].pop("Redeem goal title", None)
        _logs[account].pop("Redeem goal price", None)
    with open(f'{Path(__file__).parent}/Logs_{account_path.stem}.txt', 'w') as file:
        file.write(json.dumps(_logs, indent = 4))

def cleanLogs():
    LOGS[CURRENT_ACCOUNT].pop("Daily", None)
    LOGS[CURRENT_ACCOUNT].pop("Punch cards", None)
    LOGS[CURRENT_ACCOUNT].pop("More promotions", None)
    LOGS[CURRENT_ACCOUNT].pop("MSN shopping game", None)
    LOGS[CURRENT_ACCOUNT].pop("PC searches", None)

def checkInternetConnection():
    system = platform.system()
    while True:
        try:
            if system == "Windows":
                subprocess.check_output(["ping", "-n", "1", "8.8.8.8"], timeout=5)
            elif system == "Linux":
                subprocess.check_output(["ping", "-c", "1", "8.8.8.8"], timeout=5)
            return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            prRed("[ERROR] No internet connection.")
            time.sleep(1)

def createMessage():
    today = date.today().strftime("%d/%m/%Y")
    total_earned = 0
    message = f'📅 Daily report {today}\n\n'
    for index, value in enumerate(LOGS.items(), 1):
        redeem_message = None
        if value[1].get("Redeem goal title", None):
            redeem_title = value[1].get("Redeem goal title", None)
            redeem_price = value[1].get("Redeem goal price")
            redeem_count = value[1]["Points"] // redeem_price
            if redeem_count > 1:
                redeem_message = f"🎁 Ready to redeem: {redeem_title} for {redeem_price} points ({redeem_count}x)\n\n"
            else:
                redeem_message = f"🎁 Ready to redeem: {redeem_title} for {redeem_price} points\n\n"
        if value[1]['Last check'] == str(date.today()):
            status = '✅ Farmed'
            new_points = value[1]["Today's points"]
            total_earned += new_points
            total_points = value[1]["Points"]
            message += f"{index}. {value[0]}\n📝 Status: {status}\n⭐️ Earned points: {new_points}\n🏅 Total points: {total_points}\n"
            if redeem_message:
                message += redeem_message
            else:
                message += "\n"
        elif value[1]['Last check'] == 'Your account has been suspended':
            status = '❌ Suspended'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Your account has been locked !':
            status = '⚠️ Locked'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Unusual activity detected !':
            status = '⚠️ Unusual activity detected'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        elif value[1]['Last check'] == 'Unknown error !':
            status = '⛔️ Unknow error occured'
            message += f"{index}. {value[0]}\n📝 Status: {status}\n\n"
        else:
            status = f'Farmed on {value[1]["Last check"]}'
            new_points = value[1]["Today's points"]
            total_earned += new_points
            total_points = value[1]["Points"]
            message += f"{index}. {value[0]}\n📝 Status: {status}\n⭐️ Earned points: {new_points}\n🏅 Total points: {total_points}\n"
            if redeem_message:
                message += redeem_message
            else:
                message += "\n"
    message += f"💵 Total earned points: {total_earned} (${total_earned/1300:0.02f}) (€{total_earned/1500:0.02f})"
    return message

def sendReportToMessenger(message):
    if ARGS.telegram:
        sendToTelegram(message)
    if ARGS.discord:
        sendToDiscord(message)

def sendToTelegram(message):
    t = get_notifier('telegram')
    t.notify(message=message, token=ARGS.telegram[0], chat_id=ARGS.telegram[1])

def sendToDiscord(message):
    webhook_url = ARGS.discord[0]
    if len(message) > 2000:
        messages = [message[i:i+2000] for i in range(0, len(message), 2000)]
        for ms in messages:
            content = {"username": "⭐️ Microsoft Rewards Bot ⭐️", "content": ms}
            response = requests.post(webhook_url, json=content)
    else:
        content = {"username": "⭐️ Microsoft Rewards Bot ⭐️", "content": message}
        response = requests.post(webhook_url, json=content)
    if response.status_code == 204:
        prGreen("[LOGS] Report sent to Discord.\n")
    else:
        prRed("[ERROR] Could not send report to Discord.\n")

def prRed(prt):
    print(f"\033[91m{prt}\033[00m")
def prGreen(prt):
    print(f"\033[92m{prt}\033[00m")
def prYellow(prt):
    print(f"\033[93m{prt}\033[00m")
def prBlue(prt):
    print(f"\033[94m{prt}\033[00m")
def prPurple(prt):
    print(f"\033[95m{prt}\033[00m")

def logo():
    prRed("""
    ███╗   ███╗███████╗    ███████╗ █████╗ ██████╗ ███╗   ███╗███████╗██████╗
    ████╗ ████║██╔════╝    ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗
    ██╔████╔██║███████╗    █████╗  ███████║██████╔╝██╔████╔██║█████╗  ██████╔╝
    ██║╚██╔╝██║╚════██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══╝  ██╔══██╗
    ██║ ╚═╝ ██║███████║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║
    ╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝""")
    prPurple("            by @Charlesbel upgraded by @Farshadz1997        version 2.1\n")

def farmer():
    '''fuction that runs other functions to farm.'''
    global ERROR, MOBILE, CURRENT_ACCOUNT
    try:
        for account in ACCOUNTS:
            CURRENT_ACCOUNT = account['username']
            if CURRENT_ACCOUNT in FINISHED_ACCOUNTS:
                continue
            if LOGS[CURRENT_ACCOUNT]["Last check"] != str(date.today()):
                LOGS[CURRENT_ACCOUNT]["Last check"] = str(date.today())
                updateLogs()
            prYellow('********************' + CURRENT_ACCOUNT + '********************')
            if not LOGS[CURRENT_ACCOUNT]['PC searches']:
                browser = browserSetup(False, PC_USER_AGENT)
                print('[LOGIN]', 'Logging-in...')
                login(browser, account['username'], account['password'])
                prGreen('[LOGIN] Logged-in successfully !')
                startingPoints = POINTS_COUNTER
                prGreen('[POINTS] You have ' + str(POINTS_COUNTER) + ' points on your account !')
                browser.get(BASE_URL)
                waitUntilVisible(browser, By.ID, 'app-host', 30)
                redeem_goal_title, redeem_goal_price = getRedeemGoal(browser)
                if not LOGS[CURRENT_ACCOUNT]['Daily']:
                    completeDailySet(browser)
                if not LOGS[CURRENT_ACCOUNT]['Punch cards']:
                    completePunchCards(browser)
                if not LOGS[CURRENT_ACCOUNT]['More promotions']:
                    completeMorePromotions(browser)
                if not LOGS[CURRENT_ACCOUNT]['MSN shopping game']:
                    completeMSNShoppingGame(browser)
                remainingSearches, remainingSearchesM = getRemainingSearches(browser)
                MOBILE = bool(remainingSearchesM)
                if remainingSearches != 0:
                    print('[BING]', 'Starting Desktop and Edge Bing searches...')
                    bingSearches(browser, remainingSearches)
                    prGreen('[BING] Finished Desktop and Edge Bing searches !')
                LOGS[CURRENT_ACCOUNT]['PC searches'] = True
                updateLogs()
                ERROR = False
                browser.quit()

            if MOBILE:
                browser = browserSetup(True, account.get('mobile_user_agent', MOBILE_USER_AGENT))
                print('[LOGIN]', 'Logging-in...')
                login(browser, account['username'], account['password'], True)
                prGreen('[LOGIN] Logged-in successfully !')
                if LOGS[account['username']]['PC searches'] and ERROR:
                    startingPoints = POINTS_COUNTER
                    browser.get(BASE_URL)
                    waitUntilVisible(browser, By.ID, 'app-host', 30)
                    redeem_goal_title, redeem_goal_price = getRedeemGoal(browser)
                    remainingSearches, remainingSearchesM = getRemainingSearches(browser)
                if remainingSearchesM != 0:
                    print('[BING]', 'Starting Mobile Bing searches...')
                    bingSearches(browser, remainingSearchesM, True)
                prGreen('[BING] Finished Mobile Bing searches !')
                browser.quit()

            New_points = POINTS_COUNTER - startingPoints
            prGreen('[POINTS] You have earned ' + str(New_points) + ' points today !')
            prGreen('[POINTS] You are now at ' + str(POINTS_COUNTER) + ' points !\n')

            FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
            if LOGS[CURRENT_ACCOUNT]["Points"] > 0 and POINTS_COUNTER >= LOGS[CURRENT_ACCOUNT]["Points"] :
                LOGS[CURRENT_ACCOUNT]["Today's points"] = POINTS_COUNTER - LOGS[CURRENT_ACCOUNT]["Points"]
            else:
                LOGS[CURRENT_ACCOUNT]["Today's points"] = New_points
            LOGS[CURRENT_ACCOUNT]["Points"] = POINTS_COUNTER
            if redeem_goal_title != "" and redeem_goal_price <= POINTS_COUNTER:
                prGreen(f"[POINTS] Account ready to redeem {redeem_goal_title} for {redeem_goal_price} points.")
                if ARGS.telegram or ARGS.discord:
                    LOGS[CURRENT_ACCOUNT]["Redeem goal title"] = redeem_goal_title
                    LOGS[CURRENT_ACCOUNT]["Redeem goal price"] = redeem_goal_price
            cleanLogs()
            updateLogs()

    except FunctionTimedOut:
        prRed('[ERROR] Time out raised.\n')
        ERROR = True
        browser.quit()
        farmer()
    except SessionNotCreatedException:
        prBlue('[Driver] Session not created.')
        prBlue('[Driver] Please download correct version of webdriver form link below:')
        prBlue('[Driver] https://chromedriver.chromium.org/downloads')
        # input('Press any key to close...')
        exit()
    except KeyboardInterrupt:
        ERROR = True
        browser.quit()
        # input('\n\033[94m[INFO] Farmer paused. Press enter to continue...\033[00m\n')
        farmer()
    except Exception as e:
        print(e, '\n') if ARGS.error else print('\n')
        ERROR = True
        browser.quit()
        checkInternetConnection()
        farmer()
    else:
        if ARGS.telegram or ARGS.discord:
            message = createMessage()
            sendReportToMessenger(message)
        FINISHED_ACCOUNTS.clear()

def get_accounts(ARGS):
    try:
        account_path = Path(ARGS.accounts)
        ACCOUNTS = json.load(open(account_path, "r"))
    except FileNotFoundError:
        with open(account_path, 'w') as f:
            f.write(json.dumps([{
                "username": "Your Email",
                "password": "Your Password"
            }], indent=4))
        prPurple(f"[ACCOUNT] Accounts credential file '{account_path.name}' created."\
                "\n[ACCOUNT] Edit with your credentials and save, then press any key to continue...")
        # input()
        ACCOUNTS = json.load(open(account_path, "r"))

    return ACCOUNTS

def main():
    global LANG, GEO, TZ, ARGS, ACCOUNTS, account_path
    logo()
    ARGS = argumentParser()
    account_path = Path(ARGS.accounts)
    ACCOUNTS = get_accounts(ARGS)

    LANG, GEO, TZ = getCCodeLangAndOffset()
    if ARGS.account_browser:
        prBlue(f"\n[INFO] Opening session for {ARGS.account_browser[0]}")
        accountBrowser(ARGS.account_browser[0])
        # input("Press Enter to close when you finished...")
        return None
    run_at = None
    if ARGS.start_at:
        run_at = ARGS.start_at[0]
    elif ARGS.everyday and ARGS.start_at is None:
        run_at = datetime.now().strftime("%H:%M")
        prBlue(f"\n[INFO] Starting everyday at {run_at}.")
    if run_at is not None:
        prBlue(f"\n[INFO] Farmer will start at {run_at}")
        while True:
            if datetime.now().strftime("%H:%M") == run_at:
                start = time.time()
                logs()
                farmer()
                if not ARGS.everyday:
                    break
            time.sleep(30)
    else:
        start = time.time()
        logs()
        farmer()
    end = time.time()
    delta = end - start
    hour, remain = divmod(delta, 3600)
    min, sec = divmod(remain, 60)
    print(f"The farmer takes: {hour:02.0f}:{min:02.0f}:{sec:02.0f}")
    print(f"Farmer completed on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    LOGS["Elapsed time"] = f"{hour:02.0f}:{min:02.0f}:{sec:02.0f}"
    updateLogs()
    if ARGS.shutdown:
        os.system(f'shutdown /s /t {ARGS.shutdown}')
    if ARGS.autoexit:
        os._exit(0)
    # input('Press any key to close the program...')

if __name__ == '__main__':
    main()
