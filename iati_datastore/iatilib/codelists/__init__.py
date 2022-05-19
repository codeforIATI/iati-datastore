"""
Load IATI codelists into enums.

IATI define a farly large number of codelists. These are maintained as
CSV files, and the csv files are checked-in as part of the project.
This module build enum types for all the codelists at import time.

For more info on the enum type, see:
http://techspot.zzzeek.org/2011/01/14/the-enum-recipe/
"""

import os
import codecs
import warnings
import copy

import csv
from unidecode import unidecode

from .enum import DeclEnum


def iati_url(name):
    return {
        '1': ("https://codelists.codeforiati.org/api/1/clv2/csv/en/" +
              "%s.csv" % (name)),
        '2': ("https://codelists.codeforiati.org/api/clv2/csv/en/" +
              "%s.csv" % (name)),
    }


# Run "iati download-codelists" after adding an entry here to download the
# codelist file
urls = {}
urls['1'] = {
    "OrganisationType": iati_url("OrganisationType"),
    "OrganisationRole": iati_url("OrganisationRole"),
    "Country": iati_url("Country"),
    "TransactionType": iati_url("TransactionType"),
    "Currency": iati_url("Currency"),
    "Sector": iati_url("Sector"),
    "Vocabulary": iati_url("Vocabulary"),
    "BudgetType": iati_url("BudgetType"),
    "Region": iati_url("Region"),
    "FlowType": iati_url("FlowType"),
    "FinanceType": iati_url("FinanceType"),
    "AidType": iati_url("AidType"),
    "TiedStatus": iati_url("TiedStatus"),
    "DisbursementChannel": iati_url("DisbursementChannel"),
    "PolicyMarker": iati_url("PolicyMarker"),
    "PolicySignificance": iati_url("PolicySignificance"),
    "ActivityStatus": iati_url("ActivityStatus"),
    "CollaborationType": iati_url("CollaborationType"),
    "RelatedActivityType": iati_url("RelatedActivityType"),
    "Language": iati_url("Language"),
}
urls['2'] = copy.copy(urls['1'])
urls['2']['Vocabulary'] = iati_url("SectorVocabulary")

data_dir = os.path.dirname(__file__)


def ident(name):
    "(Python) identifier for `name`"
    return ''.join(s for s in unidecode(name) if s.isalnum() or s.isspace())\
        .replace(" ", "_").lower()


def codelist_reader(itr):
    _ = next(itr)
    for line in itr:
        yield line[:2]


by_major_version = {}
for major_version in ['1', '2']:
    by_major_version[major_version] = type('Codelists'+major_version, (object,), {})
    for name in urls[major_version].keys():
        try:
            with codecs.open(os.path.join(data_dir, major_version, "%s.csv" % name)) as cl_file:
                reader = codelist_reader(csv.reader(cl_file))
                enums = {ident(name): (code, name) for code, name in reader}
                codelist = type(name, (DeclEnum,), enums)
                setattr(by_major_version[major_version], name, codelist)
                if major_version == '1':
                    globals()[name] = codelist
        except IOError as exc:
            warnings.warn(str(exc))
