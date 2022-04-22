# KB Fastlookup [![PyPI version](https://badge.fury.io/py/simple-bank-korea.svg)](https://badge.fury.io/py/simple-bank-korea) [![Build Status](https://travis-ci.org/Beomi/simple_bank_korea.svg?branch=master)](https://travis-ci.org/Beomi/simple_bank_korea) [![codecov.io](https://codecov.io/github/Beomi/simple_bank_korea/coverage.svg?branch=master)](https://codecov.io/github/Beomi/simple_bank_korea?branch=master)


## Simplest Transaction Crawler for KB Kookmin Bank
## Original Repository by @Beomi

Requirements:

- bs4 (BeautifulSoup4)
- requests
- python-dateutil
- selenium
- pillow (PIL)
- webdriver_manager (using Chrome)

## KB (Kookmin Bank)

Currently supports KB국민은행(Kookmin Bank) only.

### Before Use

You must activate '빠른조회' service for each banks.

> check this: https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F#

You can only use service('빠른조회')-registered bank accounts.

### Usage

Import functions from each bank:

```python
from simple_bank_korea.kb import get_transactions

# get_transactions returns list of dicts
# like this:
# [{'transaction_by': '', 'date': datetime.datetime(2017, 9, 11, 12, 39, 42), 'amount': 50, 'balance': 394}]

# example
transaction_list = get_transactions(
        bank_num='47380204123456',
        birthday='941021',
        password='5432',
        # days=30, # Optional, default is 30
        # LOG_PATH='/Users/beomi/phantom.log' # Optional, default is os.path.devnull (no log)
    )

for trs in transaction_list:
    print(trs['date'], trs['amount'], trs['transaction_by'])
```

`get_transactions()` needs `bank_num`, `birthday` and `password`. and optionally you can use `days` arg for specific days from today.(default is 30days(1month))

#### Require Args

- `bank_num`: Your account number. (String)
- `birthday`: Your birthday with birth year(if 1994/10/21, do '941021'), 6 digits. (String)
- `password`: Your bank account password. (String)

#### Optional Args

- `days`: Days you want to get datas. Default is 30 days. (Integer)

#### Return types

`get_transactions()` returns list of dicts, and each dict has `date`, `amount`, `balance` and `transaction_by`.

- `get_transactions()`: returns list of transaction dicts.

- `date`: datetime
- `amount`: int
- `balance`: int
- `transaction_by`: str


## Update Log

Forked from Beomi/simple_bank_korea

0.1.0 (2022-04-22)
- Append next page list if transaction list > 100.

0.0.1 (2022-03-25)
- Changed to Chrome because PhantomJS is deprecated and Selenium is no longer supports PhantomJS)
- Thanks to @goldiutl at original repository's issue section, processing screenshot (for virtual keypad) adapted for Chrome.
- Added WebDriverWait, because the script crawls even at the loading screen.
- Added ChromeDriverManager in case of not existing chromedriver, and responded to to-be depreciated executable_path stuff
- In case of no transaction log, added try / except at parsing date. If no transactions, get_transaction function returns string "내역 없음"
- Removed PhantomJS related script, because it is used no more.
