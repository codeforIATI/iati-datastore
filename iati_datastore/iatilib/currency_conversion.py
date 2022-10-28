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

def closest_rate(currency, date):
    rate_greater = (db.session.query(CurrencyConversion).filter(CurrencyConversion.currency == currency.value)
                                                .filter(CurrencyConversion.date >= date)
                                                .order_by(CurrencyConversion.date.asc()).limit(1).subquery().select())
    rate_lesser = (db.session.query(CurrencyConversion).filter(CurrencyConversion.currency == currency.value)
                                               .filter(CurrencyConversion.date <= date)
                                               .order_by(CurrencyConversion.date.desc()).limit(1).subquery().select())
    rate_union = union_all(rate_lesser, rate_greater).alias()
    conversion_alias = aliased(CurrencyConversion, rate_union)
    date_diff = conversion_alias.date - date
    return db.session.query(conversion_alias).order_by(case([(date_diff < 0, -date_diff)], else_=date_diff)).first()

def convert_currency_usd(amount, date, currency):
    """Convert currency to US dollars for given date and input currency"""
    if currency == USD: return amount
    try:
        closest = closest_rate(currency, date)
        if closest:
            rate = closest.rate
            return round(float(amount)/rate, 2)
        else:
            return None
    except:
        return None

def convert_currency_eur(amount, date, currency):
    """Convert currency to Euros for given date and input currency"""
    if currency == EUR: return amount
    try:
        closest_eur = closest_rate(EUR, date)
        if closest_eur:
            rate_eur = closest_eur.rate
            if currency == USD:
                return round(rate_eur*float(amount), 2)
            else:
                closest_usd = closest_rate(currency, date)
                if closest_usd:
                    rate_usd = closest_usd.rate
                    return round(rate_eur*float(amount)/rate_usd, 2)
                else:
                    return None
        else:
            return None
    except:
        return None
