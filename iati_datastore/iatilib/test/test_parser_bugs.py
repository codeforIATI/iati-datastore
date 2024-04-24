import csv
import datetime
from decimal import Decimal
from unittest import TestCase

import mock
from lxml import etree as ET

from iatilib.test import db, AppTestCase, fixture_filename
from iatilib import parse, codelists as cl
from iatilib import model
from iatilib.currency_conversion import update_exchange_rates

cl2 = cl.by_major_version['2']

def read_fixture(fix_name, encoding='utf-8'):
    """Read and convert fixture from csv file"""
    return csv.reader(open(fixture_filename(fix_name)).read().strip().split("\n"), delimiter=',')

def fixture(fix_name, encoding='utf-8'):
    return open(fixture_filename(fix_name), encoding=encoding).read()


def parse_fixture(fix_name, encoding='utf-8'):
    return ET.parse(fixture_filename(fix_name))


class TestParseActivityParticipatingOrgs(AppTestCase):
    def setUp(self):
        super().setUp()
        self.activities = list(parse.document_from_file(fixture_filename("activity_with_empty_participating_org_narrative.xml")))
        self.act = self.activities[0]

    def test_participating_org(self):
        self.assertEquals(
            cl2.OrganisationRole.funding,
            self.act.participating_orgs[0].role)
        self.assertEquals(
            cl2.OrganisationType.government,
            self.act.participating_orgs[0].organisation.type)
        self.assertEquals(
            u"SE-0",
            self.act.participating_orgs[0].organisation.ref)
        self.assertEquals(
            u"Sweden",
            self.act.participating_orgs[0].organisation.name)

        self.assertEquals(
            cl2.OrganisationRole.extending,
            self.act.participating_orgs[1].role)
        self.assertEquals(
            cl2.OrganisationType.government,
            self.act.participating_orgs[1].organisation.type)
        self.assertEquals(
            u"SE-6",
            self.act.participating_orgs[1].organisation.ref)
        self.assertEquals(
            u"Swedish International Development Cooperation Agency",
            self.act.participating_orgs[1].organisation.name)

        self.assertEquals(
            cl2.OrganisationRole.implementing,
            self.act.participating_orgs[2].role)
        self.assertEquals(
            cl2.OrganisationType.government,
            self.act.participating_orgs[2].organisation.type)
        self.assertEquals(
            u"XM-DAC-12000",
            self.act.participating_orgs[2].organisation.ref)
        self.assertEquals(
            u"",
            self.act.participating_orgs[2].organisation.name)
