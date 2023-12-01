"""
Currency Module for the Bank Simulator
This Module provides up-to-date financial values for the bank.
"""

from decos import limit_by_second
from dotenv import load_dotenv
from os import getenv
from requests import get

load_dotenv()

API_KEY = getenv('API_KEY')

BASE_URL = 'https://api.freecurrencyapi.com'

CURRENCY_CODES = [
    "EUR", "USD", "JPY", "BGN", "CZK", "DKK", "GBP", "HUF", "PLN", "RON", "SEK", "CHF",
    "ISK", "NOK", "HRK", "RUB", "TRY", "AUD", "BRL", "CAD", "CNY", "HKD", "IDR",
    "ILS", "INR", "KRW", "MXN", "MYR", "NZD", "PHP", "SGD", "THB", "ZAR"
]


@limit_by_second(600)
def get_currencies():
    '''
    This method makes an api request and provides up-to-date financial data.
    '''
    endpoint = f'/v1/currencies?apikey={API_KEY}'
    url = BASE_URL + endpoint
    response = get(url).json()['data']
    data = {}

    for key, value in response.items():
        data[key] = {'name': value['name'], 'symbol': value['symbol'], 'code': value['code']}
    return data


def exchange_rate(currency1, currency2):
    '''
    This method compares given currencies and returns exchange rate between them.
    Basicly: 1 currency1 = exchange_rate(currency1, curency2) curency2
    '''
    endpoint = f'/v1/latest?apikey={API_KEY}&currencies={currency2}&base_currency={currency1}'
    url = BASE_URL + endpoint
    response = get(url).json()['data']

    return response[currency2]



