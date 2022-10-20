import requests
import csv
import datetime

from iatilib.model import CurrencyConversion
from iatilib import db
from iatilib import codelists

USD = codelists.by_major_version['2'].Currency.from_string("USD")

RATES_URL = "https://codeforiati.org/imf-exchangerates/imf_exchangerates.csv"

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

def convert_currency(amount, date, currency):
    """Convert currency to US dollars for given date and input currency"""
    if currency == USD: return amount
    try:
        closest = db.session.query(CurrencyConversion).filter(CurrencyConversion.currency == currency.value).filter(CurrencyConversion.date >= date).order_by(CurrencyConversion.date.asc()).first()
        if closest:
            rate = closest.rate
            return round(float(amount)/rate, 2)
        else:
            return None
    except:
        return None
