import csv
import datetime

from iatilib.test import db, AppTestCase, fixture_filename
from iatilib import model
from iatilib import codelists
from iatilib.currency_conversion import update_exchange_rates, convert_currency_usd, convert_currency_eur

def read_fixture(fix_name, encoding='utf-8'):
    """Read and convert fixture from csv file"""
    return csv.reader(open(fixture_filename(fix_name)).read().strip().split("\n"), delimiter=',')


def create_date(date_string):
    """Create date from string"""
    return datetime.datetime.strptime(date_string, "%Y-%m-%d").date()


def create_currency(code):
    """Create currency from code"""
    return codelists.by_major_version['2'].Currency.from_string(code)


class TestUpdateExchangeRates(AppTestCase):
    """Test updating exchange rates"""
    def setUp(self):
        super().setUp()
        self.data = read_fixture("imf_exchangerates.csv")
        next(self.data, None)

    def test_update(self):
        update_exchange_rates(self.data)

        self.assertEquals(db.session.query(model.CurrencyConversion).count(), 6035)
        self.assertEquals(db.session.query(model.CurrencyConversion).first().rate, 16.926)
        self.assertEquals(db.session.query(model.CurrencyConversion).first().currency, "AFN")


class TestConvertCurrencyUSD(AppTestCase):
    """Test converting currencies to USD"""
    def setUp(self):
        super().setUp()
        self.data = read_fixture("imf_exchangerates.csv")
        next(self.data, None)
        update_exchange_rates(self.data)

    def test_convert_currency(self):
        self.assertEquals(convert_currency_usd(512.87, create_date("1973-12-05"), create_currency("AFN")), 13.47)
        self.assertEquals(convert_currency_usd(11.43, create_date("1990-09-30"), create_currency("DZD")), 1.20)
        self.assertEquals(convert_currency_usd(2.55, create_date("1981-08-15"), create_currency("AOA")), 85232970.12)
        self.assertEquals(convert_currency_usd(150.00, create_date("2014-07-29"), create_currency("XCD")), 55.56)
        self.assertEquals(convert_currency_usd(72000.00, create_date("2012-01-01"), create_currency("ARS")), 16806.72)
        self.assertEquals(convert_currency_usd(12.50, create_date("2012-01-01"), create_currency("USD")), 12.50)
        self.assertEquals(convert_currency_usd(0.00, create_date("2005-12-05"), create_currency("AFN")), 0.00)
        self.assertEquals(convert_currency_usd(32.49, create_date("2017-06-01"), create_currency("ZZZ")), None)

class TestConvertCurrencyEUR(AppTestCase):
    """Test converting currencies to EUR"""
    def setUp(self):
        super().setUp()
        self.data = read_fixture("imf_exchangerates.csv")
        next(self.data, None)
        update_exchange_rates(self.data)

    def test_convert_currency(self):
        self.assertEquals(convert_currency_eur(512.87, create_date("2003-12-05"), create_currency("AFN")), 8.80)
        self.assertEquals(convert_currency_eur(111.43, create_date("2009-09-30"), create_currency("DZD")), 1.05)
        self.assertEquals(convert_currency_eur(2000.55, create_date("2011-08-15"), create_currency("AOA")), 15.03)
        self.assertEquals(convert_currency_eur(150.00, create_date("2014-07-29"), create_currency("XCD")), 41.52)
        self.assertEquals(convert_currency_eur(72000.00, create_date("2012-01-01"), create_currency("ARS")), 12989.20)
        self.assertEquals(convert_currency_eur(12.50, create_date("2012-01-01"), create_currency("EUR")), 12.50)
        self.assertEquals(convert_currency_eur(99.12, create_date("2021-06-15"), create_currency("USD")), 81.24)
        self.assertEquals(convert_currency_eur(0.00, create_date("2005-12-05"), create_currency("AFN")), 0.00)
        self.assertEquals(convert_currency_eur(32.49, create_date("2017-06-01"), create_currency("ZZZ")), None)
