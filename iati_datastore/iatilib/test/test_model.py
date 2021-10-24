from . import AppTestCase
from . import factories as fac

from iatilib.model import Activity, Resource
from iatilib import db


class TestResource(AppTestCase):
    def test_replace_activities(self):
        # Activites are not updated in place. We only receive entire
        # docs (resources) which contain many actitivites, so to update
        # the db we remove all activites relating to a resource (plus
        # dependant objects) and replace them. These tests are me
        # working out how to do that in sqlalchemy.

        res = fac.ResourceFactory.create(
            activities=[fac.ActivityFactory.build(
                iati_identifier=u"t1",
                title=u"t1"
            )]
        )
        Activity.query.filter_by(resource_url=res.url).delete()
        # at this point res.activities has not been cleared
        res.activities = [
            fac.ActivityFactory.create(
                iati_identifier=u"t1",
                title=u"t2",
            )
        ]
        db.session.commit()
        self.assertEqual(res.activities[0].title, u"t2")
        self.assertEqual(
            Resource.query.get(res.url).activities[0].title, u"t2")

    def test_replace_activity_w_many_dependant_rows(self):
        db.engine.echo = True
        res = fac.ResourceFactory.create(
            activities=[fac.ActivityFactory.build(
                participating_orgs=[
                    fac.ParticipationFactory.build()
                ],
                recipient_country_percentages=[
                    fac.CountryPercentageFactory.build()
                ],
                transactions=[
                    fac.TransactionFactory.build()
                ],
                sector_percentages=[
                    fac.SectorPercentageFactory.build()
                ],
                budgets=[
                    fac.BudgetFactory.build()
                ],
                websites=[
                    u"http://test.com"
                ]
            )]
        )
        Activity.query.filter_by(resource_url=res.url).delete()
        self.assertEqual(
            0,
            Activity.query.filter_by(resource_url=res.url).count()
        )
        db.engine.echo = False


class TestOrganisation(AppTestCase):
    def test_organisation_repr(self):
        org = fac.OrganisationFactory.build(ref='org ref')
        self.assertEqual(str(org), "Organisation(ref='org ref')")


class TestTransaction(AppTestCase):
    def test_transaction_repr(self):
        org = fac.TransactionFactory.build(id='test-trans-0')
        self.assertEqual(str(org), "Transaction(id='test-trans-0')")


class TestLog(AppTestCase):
    def test_log_repr(self):
        org = fac.LogFactory.build(msg='hello')
        self.assertEqual(str(org), "<Log: 1970-01-01 12:00:00 - hello>")
