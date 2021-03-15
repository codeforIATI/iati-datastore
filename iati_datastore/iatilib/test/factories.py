import datetime

import factory

from iatilib import codelists
from iatilib import db
from iatilib.model import (
    Activity, Transaction, Organisation, SectorPercentage, CountryPercentage,
    Participation, Budget, Resource, RegionPercentage, PolicyMarker,
    RelatedActivity, Dataset, Log
)

from factory.alchemy import SQLAlchemyModelFactory as Factory


class TestFactory(Factory):
    class Meta:
        abstract = False
        sqlalchemy_session = db.session

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        entity = model_class(*args, **kwargs)
        db.session.add(entity)
        db.session.commit()
        db.session.refresh(entity)
        return entity


def create_activity():
    raise Exception("create_activity")


class ResourceFactory(TestFactory):
    class Meta:
        model = Resource
    url = u"http://test.com"


class CountryPercentageFactory(TestFactory):
    class Meta:
        model = CountryPercentage
    country = codelists.Country.united_states_of_america_the
    name = ""
    percentage = 0


class RegionPercentageFactory(TestFactory):
    class Meta:
        model = RegionPercentage
    region = codelists.Region.europe_regional
    percentage = 0


class SectorPercentageFactory(TestFactory):
    class Meta:
        model = SectorPercentage
    sector = codelists.Sector.teacher_training
    percentage = 0


class OrganisationFactory(TestFactory):
    class Meta:
        model = Organisation
    ref = factory.Sequence(lambda n: u'test-org-{0}'.format(n))
    name = u"test org"


class ParticipationFactory(TestFactory):
    class Meta:
        model = Participation
    organisation = factory.SubFactory(OrganisationFactory)
    role = codelists.OrganisationRole.funding


class PolicyMarkerFactory(TestFactory):
    class Meta:
        model = PolicyMarker
    code = codelists.PolicyMarker.gender_equality


class RelatedActivityFactory(TestFactory):
    class Meta:
        model = RelatedActivity
    ref = "test_ref"


class ActivityFactory(TestFactory):
    class Meta:
        model = Activity
    iati_identifier = factory.Sequence(lambda n: u'test-act-{0}'.format(n))
    raw_xml = u"<test />"
    major_version = '1'


class TransactionFactory(TestFactory):
    class Meta:
        model = Transaction
    activity = factory.SubFactory(ActivityFactory)
    type = codelists.TransactionType.commitment
    value_currency = codelists.Currency.us_dollar
    value_amount = 0
    value_date = datetime.date(1972, 1, 1)
    date = datetime.date(1973, 2, 2)


class BudgetFactory(TestFactory):
    class Meta:
        model = Budget
    activity = factory.SubFactory(ActivityFactory)
    type = codelists.BudgetType.original
    value_amount = 0


class DatasetFactory(TestFactory):
    class Meta:
        model = Dataset
    name = 'test_dataset'
    is_open = True


class LogFactory(TestFactory):
    class Meta:
        model = Log
    created_at = datetime.datetime(1970, 1, 1, 12, 0, 0)
    dataset = 'bad-dataset'
    msg = 'Dataset is broken'
