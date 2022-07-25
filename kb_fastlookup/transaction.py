from io import StringIO, BytesIO
import base64
from pickle import FALSE
import tempfile
import platform
from PIL import Image
from PIL import ImageChops
import requests
from bs4 import BeautifulSoup as bs
import platform
import tempfile
import datetime
from dateutil import parser
import os
import json
import sys
from pathlib import Path
import math, operator
from functools import reduce
import re
from seleniumrequests import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TMP_DIR = Path('/tmp' if platform.system() == 'Darwin' else tempfile.gettempdir())
CURRENT_PACKAGE_DIR = Path(__file__).parent.absolute()
os.chdir(CURRENT_PACKAGE_DIR)

# from repository 'simple_bank_korea' by Beomi at Github
def get_keypad_img():
    retries = 1
    area_hash_list = []
    area_pattern = re.compile("'(\w+)'")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get('https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F')
    driver.set_window_size(1920,1080)
    while retries <= 10:
        try:
            WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH,'//*[@id="loading_img"]'))
            )
        finally:
            try:
                WebDriverWait(driver, 10).until_not(
                    EC.presence_of_element_located((By.XPATH,'//*[@id="loading_img"]'))
                )
                break
            except TimeoutException:
                driver.get('https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F')
                retries += 1
    if driver.get_cookie('JSESSIONID'):
        JSESSIONID = driver.get_cookie('JSESSIONID').get('value')
    else:
        JSESSIONID = ''
        print('no JSESSIONID')
    if driver.get_cookie('QSID'):
        QSID = driver.get_cookie('QSID').get('value')
    else:
        QSID = ''
        print('no QSID')
    KEYPAD_USEYN = driver.find_element(By.CSS_SELECTOR, 'input[id*="KEYPAD_USEYN"]').get_attribute('value')
    quics_img = driver.find_element(By.CSS_SELECTOR, 'img[src*="quics"]')
    area_list = driver.find_elements(By.CSS_SELECTOR, 'map > area')

    for area in area_list:
        re_matched = area_pattern.findall(area.get_attribute('onmousedown'))
        if re_matched:
            area_hash_list.append(re_matched[0])

    img_url = quics_img.get_attribute('src')
    keymap = quics_img.get_attribute('usemap').replace('#divKeypad', '')[:-3]
    driver.get(img_url)
    screenshot = Image.open(BytesIO(driver.get_screenshot_as_png()))
    left = 875 - 17
    top = 414 - 42
    right = left + 205
    bottom = top + 336
    real = screenshot.crop((left, top, right, bottom))
    driver.quit()

    # Get list
    num_sequence = _get_keypad_num_list(real)

    PW_DIGITS = {}
    # FIXED
    PW_DIGITS['1'] = area_hash_list[0]
    PW_DIGITS['2'] = area_hash_list[1]
    PW_DIGITS['3'] = area_hash_list[2]
    PW_DIGITS['4'] = area_hash_list[3]
    PW_DIGITS['6'] = area_hash_list[5]

    # Floating..
    for idx, num in enumerate(num_sequence):
        if idx == 0:
            PW_DIGITS[str(num)] = area_hash_list[4]
        elif idx == 1:
            PW_DIGITS[str(num)] = area_hash_list[6]
        elif idx == 2:
            PW_DIGITS[str(num)] = area_hash_list[7]
        elif idx == 3:
            PW_DIGITS[str(num)] = area_hash_list[8]
        elif idx == 4:
            PW_DIGITS[str(num)] = area_hash_list[9]

    return {
        'JSESSIONID': JSESSIONID,
        'QSID': QSID,
        'KEYMAP': keymap,
        'PW_DIGITS': PW_DIGITS,
        'KEYPAD_USEYN': KEYPAD_USEYN
    }


def rmsdiff(im1, im2):
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
                            map(lambda h, i: h * (i ** 2), h, range(256))
                            ) / (float(im1.size[0]) * im1.size[1]))


def _get_keypad_num_list(img):
    # 57x57 box
    box_5th = Image.open(Path.joinpath(CURRENT_PACKAGE_DIR, 'assets', '5.png'))
    box_7th = Image.open(Path.joinpath(CURRENT_PACKAGE_DIR, 'assets', '7.png'))
    box_8th = Image.open(Path.joinpath(CURRENT_PACKAGE_DIR, 'assets', '8.png'))
    box_9th = Image.open(Path.joinpath(CURRENT_PACKAGE_DIR, 'assets', '9.png'))
    box_0th = Image.open(Path.joinpath(CURRENT_PACKAGE_DIR, 'assets', '0.png'))

    box_dict = {
        '5': box_5th,
        '7': box_7th,
        '8': box_8th,
        '9': box_9th,
        '0': box_0th,
    }

    # 57x57 box
    crop_5th = img.crop(box=(74, 99, 131, 156))
    crop_7th = img.crop(box=(16, 157, 73, 214))
    crop_8th = img.crop(box=(74, 157, 131, 214))
    crop_9th = img.crop(box=(132, 157, 189, 214))
    crop_0th = img.crop(box=(74, 215, 131, 272))

    crop_list = [crop_5th, crop_7th, crop_8th, crop_9th, crop_0th]

    keypad_num_list = []

    for idx, crop in enumerate(crop_list):
        for key, box in box_dict.items():
            try:
                diff = rmsdiff(crop, box)
                if diff < 62:
                    keypad_num_list += [key]
            except Exception as e:
                print(e)
    return keypad_num_list

def get_transactions(bank_num, birthday, password, days=30, start_date=None, cache=False):
    def _get_transactions(VIRTUAL_KEYPAD_INFO, bank_num, birthday, password, days, start_date):
        PW_DIGITS = VIRTUAL_KEYPAD_INFO['PW_DIGITS']
        KEYMAP = VIRTUAL_KEYPAD_INFO['KEYMAP']
        JSESSIONID = VIRTUAL_KEYPAD_INFO['JSESSIONID']
        QSID = VIRTUAL_KEYPAD_INFO['QSID']
        KEYPAD_USEYN = VIRTUAL_KEYPAD_INFO['KEYPAD_USEYN']

        today_list = []
        month_before_list = []

        bank_num = str(bank_num)
        birthday = str(birthday)
        password = str(password)
        hexed_pw = ''
        days = int(days)
        for p in password:
            hexed_pw += PW_DIGITS[str(p)]

        today = datetime.datetime.today()
        today_list.append(today)
        if start_date == None:
            month_before = today - datetime.timedelta(days=days)
            month_before_list.append(month_before)
        else:
            start_date = str(start_date)
            start_date = datetime.datetime.strptime(start_date, '%Y%m%d')
            days = (today - start_date).days #int
            assert days >= 0
            bunch, remnant = divmod(days, 180)
            if bunch > 0:
                for i in range(bunch, -1, -1):
                    if i == bunch:
                        month_before = today - datetime.timedelta(days=180)
                        month_before_list.append(month_before)
                    elif i == 0:
                        today_list.append(month_before)
                        month_before_list.append(start_date)
                    else:
                        today_list.append(month_before)
                        month_before = month_before - datetime.timedelta(days=180)
                        month_before_list.append(month_before)
            else:
                month_before = start_date
                month_before_list.append(month_before)

        #basic data when crawling
        cookies = {
            '_KB_N_TIKER': 'N',
            'JSESSIONID': JSESSIONID,
            'QSID': QSID,
            'delfino.recentModule': 'G3',
        }

        headers = {
            'Pragma': 'no-cache',
            'Origin': 'https://obank.kbstar.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4,la;q=0.2,da;q=0.2',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded;  charset=UTF-8',
            'Accept': 'text/html, */*; q=0.01',
            'Cache-Control': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': 'https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F',
            'DNT': '1',
        }

        params = (
            ('chgCompId', 'b028770'),
            ('baseCompId', 'b028702'),
            ('page', 'C025255'),
            ('cc', 'b028702:b028770'),
        )

        transaction_list = []

        for today, month_before in zip(today_list, month_before_list):
            this_year = today.strftime('%Y')
            this_month = today.strftime('%m')
            this_day = today.strftime('%d')
            this_all = today.strftime('%Y%m%d')
            month_before_year = month_before.strftime('%Y')
            month_before_month = month_before.strftime('%m')
            month_before_day = month_before.strftime('%d')
            month_before_all = month_before.strftime('%Y%m%d')
            breakthrough = True
            while breakthrough == True:
                data = [
                    ('KEYPAD_TYPE_{}'.format(KEYMAP), '3'),
                    ('KEYPAD_HASH_{}'.format(KEYMAP), hexed_pw),
                    ('KEYPAD_USEYN_{}'.format(KEYMAP), KEYPAD_USEYN),
                    ('KEYPAD_INPUT_{}'.format(KEYMAP), '\uBE44\uBC00\uBC88\uD638'),
                    ('signed_msg', ''),
                    ('\uC694\uCCAD\uD0A4', ''),
                    ('\uACC4\uC88C\uBC88\uD638', bank_num),
                    ('\uC870\uD68C\uC2DC\uC791\uC77C\uC790', month_before_all),
                    ('\uC870\uD68C\uC885\uB8CC\uC77C', this_all),
                    ('\uACE0\uAC1D\uC2DD\uBCC4\uBC88\uD638', ''),
                    ('\uBE60\uB978\uC870\uD68C', 'Y'),
                    ('\uC870\uD68C\uACC4\uC88C', bank_num),
                    ('\uBE44\uBC00\uBC88\uD638', password),
                    ('USEYN_CHECK_NAME_{}'.format(KEYMAP), 'Y'),
                    ('\uAC80\uC0C9\uAD6C\uBD84', '2'),
                    ('\uC8FC\uBBFC\uC0AC\uC5C5\uC790\uBC88\uD638', birthday),
                    ('\uC870\uD68C\uC2DC\uC791\uB144', month_before_year),
                    ('\uC870\uD68C\uC2DC\uC791\uC6D4', month_before_month),
                    ('\uC870\uD68C\uC2DC\uC791\uC77C', month_before_day),
                    ('\uC870\uD68C\uB05D\uB144', this_year),
                    ('\uC870\uD68C\uB05D\uC6D4', this_month),
                    ('\uC870\uD68C\uB05D\uC77C', this_day),
                    ('\uC870\uD68C\uAD6C\uBD84', '2'),
                    ('\uC751\uB2F5\uBC29\uBC95', '2'),
                ]

                r = requests.post('https://obank.kbstar.com/quics', headers=headers, params=params, cookies=cookies, data=data)
                soup = bs(r.text, 'html.parser')

                transactions = soup.select('#pop_contents > table.tType01 > tbody > tr')
                if len(transactions) >= 200:
                    tdn = transactions[-2].select('td')
                    yes = tdn[0].text
                    yes = yes[:10] + ' ' + yes[10:]
                    _yse = parser.parse(yes)
                    this_year = _yse.strftime('%Y')
                    this_month = _yse.strftime('%m')
                    this_day = _yse.strftime('%d')
                    this_all = _yse.strftime('%Y%m%d')
                    breakthrough = True
                else:
                    breakthrough = False

                for idx, value in enumerate(transactions):
                    tds = value.select('td')
                    if not idx % 2:
                        _date = tds[0].text
                        _date = _date[:10] + ' ' + _date[10:]
                        try:
                            date = parser.parse(_date)  # 날짜: datetime
                        except:
                            continue
                        amount = -int(tds[3].text.replace(',', '')) or int(tds[4].text.replace(',', ''))  # 입금 / 출금액: int
                        balance = int(tds[5].text.replace(',', ''))  # 잔고: int
                        detail = dict(date=date, amount=amount, balance=balance)
                    else:
                        transaction_by = tds[0].text.strip()  # 거래자(입금자 등): str
                        tmp = dict(transaction_by=transaction_by)
                        transaction_list.append({**detail, **tmp})
        
        # eliminate duplicates
        newlist = []
        for x in transaction_list:
            if x not in newlist:
                newlist.append(x)
        return newlist

        # data = [
        #     ('KEYPAD_TYPE_{}'.format(KEYMAP), '3'),
        #     ('KEYPAD_HASH_{}'.format(KEYMAP), hexed_pw),
        #     ('KEYPAD_USEYN_{}'.format(KEYMAP), KEYPAD_USEYN),
        #     ('KEYPAD_INPUT_{}'.format(KEYMAP), '\uBE44\uBC00\uBC88\uD638'),
        #     ('signed_msg', ''),
        #     ('\uC694\uCCAD\uD0A4', ''),
        #     ('\uACC4\uC88C\uBC88\uD638', bank_num),
        #     ('\uC870\uD68C\uC2DC\uC791\uC77C\uC790', month_before_all),
        #     ('\uC870\uD68C\uC885\uB8CC\uC77C', this_all),
        #     ('\uACE0\uAC1D\uC2DD\uBCC4\uBC88\uD638', ''),
        #     ('\uBE60\uB978\uC870\uD68C', 'Y'),
        #     ('\uC870\uD68C\uACC4\uC88C', bank_num),
        #     ('\uBE44\uBC00\uBC88\uD638', password),
        #     ('USEYN_CHECK_NAME_{}'.format(KEYMAP), 'Y'),
        #     ('\uAC80\uC0C9\uAD6C\uBD84', '2'),
        #     ('\uC8FC\uBBFC\uC0AC\uC5C5\uC790\uBC88\uD638', birthday),
        #     ('\uC870\uD68C\uC2DC\uC791\uB144', month_before_year),
        #     ('\uC870\uD68C\uC2DC\uC791\uC6D4', month_before_month),
        #     ('\uC870\uD68C\uC2DC\uC791\uC77C', month_before_day),
        #     ('\uC870\uD68C\uB05D\uB144', this_year),
        #     ('\uC870\uD68C\uB05D\uC6D4', this_month),
        #     ('\uC870\uD68C\uB05D\uC77C', this_day),
        #     ('\uC870\uD68C\uAD6C\uBD84', '2'),
        #     ('\uC751\uB2F5\uBC29\uBC95', '2'),
        # ]
        
        # # chrome_options = webdriver.ChromeOptions()
        # # chrome_options.add_argument('--no-sandbox')
        # # chrome_options.add_argument('--window-size=1920,1080')
        # # # chrome_options.add_argument('--headless')
        # # chrome_options.add_argument('--disable-gpu')
        # # chrome_options.add_argument("--start-maximized")
        # # chrome_options.add_argument("--disable-dev-shm-usage")
        # # driver = Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        # # driver.get('https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F')
        # # ak = driver.request('POST', 'https://obank.kbstar.com/quics', headers=headers, cookies=cookies, params=params, data=data)
        # r = requests.post('https://obank.kbstar.com/quics', headers=headers, params=params, cookies=cookies, data=data)
        # # html = ak.text
        # soup = bs(r.text, 'html.parser')

        # transactions = soup.select('#pop_contents > table.tType01 > tbody > tr')
        # transaction_list = []

        # for idx, value in enumerate(transactions):
        #     tds = value.select('td')
        #     if not idx % 2:
        #         _date = tds[0].text
        #         _date = _date[:10] + ' ' + _date[10:]
        #         try:
        #             date = parser.parse(_date)  # 날짜: datetime
        #         except:
        #             return "내역 없음"
        #         amount = -int(tds[3].text.replace(',', '')) or int(tds[4].text.replace(',', ''))  # 입금 / 출금액: int
        #         balance = int(tds[5].text.replace(',', ''))  # 잔고: int
        #         detail = dict(date=date, amount=amount, balance=balance)
        #     else:
        #         transaction_by = tds[0].text.strip()  # 거래자(입금자 등): str
        #         tmp = dict(transaction_by=transaction_by)
        #         transaction_list.append({**detail, **tmp})
        # return transaction_list

    # Caching
    VIRTUAL_KEYPAD_INFO_JSON = os.path.join(TMP_DIR, 'kb_{}.json'.format(bank_num))
    if cache:
        if os.path.exists(VIRTUAL_KEYPAD_INFO_JSON):
            fp = open(VIRTUAL_KEYPAD_INFO_JSON)
            VIRTUAL_KEYPAD_INFO = json.load(fp)
            fp.close()
        else:
            VIRTUAL_KEYPAD_INFO = get_keypad_img()
            fp = open(VIRTUAL_KEYPAD_INFO_JSON, 'w+')
            json.dump(VIRTUAL_KEYPAD_INFO, fp)
            fp.close()
    else:
        VIRTUAL_KEYPAD_INFO = get_keypad_img()

    result = _get_transactions(VIRTUAL_KEYPAD_INFO, bank_num, birthday, password, days, start_date)
    if result:
        return result
    else:
        print('Session Expired! Get new touch keys..')
        NEW_VIRTUAL_KEYPAD_INFO = get_keypad_img()
        if cache:
            fp = open(VIRTUAL_KEYPAD_INFO_JSON, 'w+')
            json.dump(NEW_VIRTUAL_KEYPAD_INFO, fp)
            fp.close()
        return _get_transactions(NEW_VIRTUAL_KEYPAD_INFO, bank_num, birthday, password, days, start_date)
        
