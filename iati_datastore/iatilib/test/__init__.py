import os
import unittest
from io import StringIO

from lxml import etree as lxml_etree
from xml.etree import ElementTree as xml_etree


from iatilib.frontend.app import create_app
from iatilib import db
from iatilib.config import Config
from iatilib.model import Stats


def create_db():
    db.create_all()
    db.session.add(Stats(label='activities', count=0))
    db.session.add(Stats(label='transactions', count=0))
    db.session.add(Stats(label='budgets', count=0))
    db.session.commit()


_app = None


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_SQLALCHEMY_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres")
    RQ_CONNECTION_CLASS = "fakeredis.FakeStrictRedis"


class AppTestCaseNoDb(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.addTypeEqualityFunc(lxml_etree.Element, self.assertXMLEqual)
        self.addTypeEqualityFunc(xml_etree.Element, self.assertXMLEqual)

    def setUp(self):
        global _app
        if _app is None:
            _app = create_app(TestConfig)
            _app.app_context().push()

        self.app = _app
        if os.environ.get("SA_ECHO", "False") == "True":
            db.engine.echo = True

    def assertXMLEqual(self, x1, x2, msg=None):
        sio = StringIO()
        if not xml_compare(x1, x2, sio.write):
            if msg is None:
                msg = sio.getvalue()
            raise self.failureException(msg)


class AppTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.addTypeEqualityFunc(lxml_etree.Element, self.assertXMLEqual)
        self.addTypeEqualityFunc(xml_etree.Element, self.assertXMLEqual)

    def setUp(self):
        global _app
        if _app is None:
            _app = create_app(TestConfig)
            _app.app_context().push()

        self.app = _app
        if os.environ.get("SA_ECHO", "False") == "True":
            db.engine.echo = True
        create_db()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.session._unique_cache = {}

    def assertXMLEqual(self, x1, x2, msg=None):
        sio = StringIO()
        if not xml_compare(x1, x2, sio.write):
            if msg is None:
                msg = sio.getvalue()
            raise self.failureException(msg)


class ClientTestCase(AppTestCase):
    def setUp(self):
        super().setUp()
        self.client = self.app.test_client()


# From formencode
# https://bitbucket.org/ianb/formencode/raw/f59f8bb59a8c9b4176a45e4a03533e26367363f3/formencode/doctest_xml_compare.py
def xml_compare(x1, x2, reporter=None):
    if x1.tag != x2.tag:
        if reporter:
            reporter('Tags do not match: %s and %s' % (x1.tag, x2.tag))
        return False
    for name, value in x1.attrib.items():
        if x2.attrib.get(name) != value:
            if reporter:
                reporter('Attributes do not match: %s=%r, %s=%r'
                         % (name, value, name, x2.attrib.get(name)))
            return False
    for name in x2.attrib.keys():
        if name not in x1.attrib:
            if reporter:
                reporter('x2 has an attribute x1 is missing: %s'
                         % name)
            return False
    if not text_compare(x1.text, x2.text):
        if reporter:
            reporter('text: %r != %r' % (x1.text, x2.text))
        return False
    if not text_compare(x1.tail, x2.tail):
        if reporter:
            reporter('tail: %r != %r' % (x1.tail, x2.tail))
        return False
    cl1 = list(x1)
    cl2 = list(x2)
    if len(cl1) != len(cl2):
        if reporter:
            reporter('children length differs, %i != %i'
                     % (len(cl1), len(cl2)))
        return False
    i = 0
    for c1, c2 in zip(cl1, cl2):
        i += 1
        if not xml_compare(c1, c2, reporter=reporter):
            if reporter:
                reporter('children %i do not match: %s'
                         % (i, c1.tag))
            return False
    return True


def text_compare(t1, t2):
    if not t1 and not t2:
        return True
    if t1 == '*' or t2 == '*':
        return True
    return (t1 or '').strip() == (t2 or '').strip()


def fixture_filename(fix_name):
    return os.path.join(os.path.dirname(__file__), "fixtures", fix_name)
