import requests
import csv
import datetime

from sqlalchemy import union_all, case
from sqlalchemy.orm import aliased

from iatilib.model import CurrencyConversion
from iatilib import db
from iatilib import codelists

USD = codelists.by_major_version['2'].Currency.from_string("USD")
EUR = codelists.by_major_version['2'].Currency.from_string("EUR")

RATES_URL = "https://codeforiati.org/imf-exchangerates/imf_exchangerates.csv"

def currency_conversion_cache(cache_key='default'):
    cache = {'date': [],
             'rate': [],
             'currency': [],
             'index': {},
             'data': {}}
    data = db.session.query(CurrencyConversion).order_by(CurrencyConversion.currency.asc(), CurrencyConversion.date.asc()).all()
    for d in data:
        cache['date'].append(d.date)
        cache['rate'].append(d.rate)
        cache['currency'].append(d.currency)
    for i, c in enumerate(cache['currency']):
        if c and not c in cache['index']:
            for j in range(i, len(cache['currency'])):
                if cache['currency'][j] != c: break
            cache['index'][c] = (i, j-1)
    for c in cache['index']:
        i = cache['index'][c][0]
        j = cache['index'][c][1]
        rates = []
        for k in range(i, j):
            rates.append((cache['date'][k], cache['rate'][k]))
        cache['data'][c] = rates
    cache['date'] = None
    cache['rate'] = None
    cache['currency'] = None
    cache['cache_key'] = cache_key
    return cache

conversion_cache = None

def get_rate(currency, date, cache_key='default'):
    key = f'{cache_key}-{datetime.datetime.now().date()}'
    global conversion_cache
    if not conversion_cache or conversion_cache['cache_key'] != key:
        conversion_cache = currency_conversion_cache(cache_key=key)
    items = conversion_cache['data'][currency]
    closest = min(items, key=lambda x: abs(x[0] - date))
    return closest[1]

def download_imf_exchange_rates():
    """Download and open IMF exchange rates CSV data"""
    with requests.Session() as s:
        download = s.get(RATES_URL)
        decoded_content = download.content.decode('utf-8')
        data = csv.reader(decoded_content.splitlines(), delimiter=',')
        next(data, None)
    return data

def update_exchange_rates(data):
    """Update currency conversion database table with new """
    if db.session.query(CurrencyConversion).first():
        last = db.session.query(CurrencyConversion).order_by(CurrencyConversion.date.desc()).first()
        last_date = last.date
    else:
        last_date = datetime.datetime.strptime('1955-01-01', "%Y-%m-%d").date()
    to_add = []
    for row in data:
        date = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
        if date > last_date:
            new_rate = CurrencyConversion(date=date, rate=float(row[1]), currency=row[2], frequency=row[3],
                               source=row[4], country_code=row[5], country=row[6])
            to_add.append(new_rate)
    if to_add:
        db.session.add_all(to_add)
        db.session.commit()
    global conversion_cache
    conversion_cache = None

def closest_rate(currency, date, cache_key='default'):
    return get_rate(currency.value, date, cache_key=cache_key)

def convert_currency_usd(amount, date, currency, cache_key='default'):
    """Convert currency to US dollars for given date and input currency"""
    if currency == USD: return amount
    try:
        closest = closest_rate(currency, date, cache_key=cache_key)
        if closest:
            return round(float(amount)/closest, 2)
        else:
            return None
    except:
        return None

def convert_currency_eur(amount, date, currency, cache_key='default'):
    """Convert currency to Euros for given date and input currency"""
    if currency == EUR: return amount
    try:
        closest_eur = closest_rate(EUR, date, cache_key=cache_key)
        if closest_eur:
            if currency == USD:
                return round(closest_eur*float(amount), 2)
            else:
                closest_usd = closest_rate(currency, date, cache_key=cache_key)
                if closest_usd:
                    return round(closest_eur*float(amount)/closest_usd, 2)
                else:
                    return None
        else:
            return None
    except:
        return None
