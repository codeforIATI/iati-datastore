from os.path import dirname, join
from collections import namedtuple
import datetime

import mock
import iatikit

from . import AppTestCase, fixture_filename
from . import factories as fac

from iatilib import crawler, db, parse
from iatilib.model import Dataset, Log, Resource, Activity, DeletedActivity


registry = iatikit.data(
    join(dirname(__file__), 'fixtures', 'registry'))


class TestCrawler(AppTestCase):
    @mock.patch('iatikit.data')
    def test_fetch_package_list(self, iatikit_mock):
        data_mock = iatikit_mock.return_value
        data_mock.last_updated = datetime.datetime.utcnow()
        data_mock.datasets = [
            iatikit.Dataset("tst-a.xml"),
            iatikit.Dataset("tst-b.xml")]
        datasets = crawler.fetch_dataset_list()
        self.assertIn("tst-a", [ds.name for ds in datasets])
        self.assertIn("tst-b", [ds.name for ds in datasets])

    @mock.patch('iatikit.data')
    def test_update_adds_datasets(self, iatikit_mock):
        data_mock = iatikit_mock.return_value
        data_mock.last_updated = datetime.datetime.utcnow()
        data_mock.datasets = [iatikit.Dataset('tst-a')]
        datasets = crawler.fetch_dataset_list()
        self.assertEqual(1, datasets.count())
        data_mock.datasets = [
            iatikit.Dataset('tst-a.xml'),
            iatikit.Dataset('tst-b.xml')]
        datasets = crawler.fetch_dataset_list()
        self.assertEqual(2, datasets.count())

    @mock.patch('iatikit.data')
    def test_update_deletes_datasets(self, iatikit_mock):
        data_mock = iatikit_mock.return_value
        data_mock.last_updated = datetime.datetime.utcnow()
        data_mock.datasets = [
            iatikit.Dataset("tst-a.xml"),
            iatikit.Dataset("tst-b.xml")]
        datasets = crawler.fetch_dataset_list()
        self.assertEqual(2, datasets.count())
        data_mock.datasets = [
            iatikit.Dataset("tst-a.xml")]
        datasets = crawler.fetch_dataset_list()
        self.assertEqual(1, datasets.count())

    @mock.patch('iatikit.data')
    def test_fetch_dataset(self, iatikit_mock):
        iatikit_mock.return_value = registry
        dataset = crawler.fetch_dataset_metadata(
            Dataset(name="old-org-acts"))
        self.assertEqual(1, len(dataset.resources))
        self.assertEqual("https://old-org.nl/sites/default/files/IATI/activities.xml", dataset.resources[0].url)
        self.assertEqual("old-org", dataset.publisher)

    @mock.patch('iatikit.data')
    def test_fetch_dataset_count_commited_resources(self, iatikit_mock):
        iatikit_mock.return_value = registry
        crawler.fetch_dataset_metadata(
            Dataset(name="old-org-acts"))
        db.session.commit()
        self.assertEqual(1, Resource.query.count())

    @mock.patch('iatikit.data')
    def test_update_dataset_same_url(self, iatikit_mock):
        fac.DatasetFactory.create(
            name='tst-old',
            resources=[fac.ResourceFactory.create(
                url="https://old-org.nl/sites/default/files/" +
                    "IATI/activities.xml",
            )]
        )
        dataset_new = fac.DatasetFactory.create(
            name='old-org-acts',
            resources=[]
        )
        iatikit_mock.return_value = registry
        crawler.update_dataset(
            dataset_name='old-org-acts', ignore_hashes=False)
        # resource was not added
        self.assertEqual(0, len(dataset_new.resources))
        log = Log.query.filter_by(dataset="old-org-acts").first()
        self.assertIn('Failed to update dataset old-org-acts', log.msg)

    @mock.patch('iatikit.data')
    def test_fetch_resource_succ(self, iatikit_mock):
        iatikit_mock.return_value = registry
        dataset = fac.DatasetFactory.create(
            name='old-org-acts',
            resources=[fac.ResourceFactory.create(
                url="http://foo",
            )]
        )
        resource = crawler.fetch_resource(dataset=dataset, ignore_hashes=False)
        self.assertEqual(b"<?xml", resource.document[:5])
        self.assertEqual(None, resource.last_parsed)
        self.assertEqual(None, resource.last_parse_error)

    @mock.patch('iatikit.data')
    def test_ignore_unchanged_resource(self, iatikit_mock):
        iatikit_mock.return_value = registry
        with open(join(
                dirname(__file__),
                'fixtures', 'registry', 'data', 'old-org',
                'old-org-acts.xml'), 'rb') as f:
            document = f.read()
        dataset = fac.DatasetFactory.create(
            name='old-org-acts',
            resources=[fac.ResourceFactory.create(
                url="https://old-org.nl/sites/default/files/" +
                    "IATI/activities.xml",
                last_parsed=datetime.datetime(2000, 1, 1),
                document=document,
            )]
        )
        resource = crawler.fetch_resource(
            dataset=dataset, ignore_hashes=False)
        self.assertNotEqual(None, resource.last_parsed)

    @mock.patch('iatikit.data')
    def test_dont_ignore_unchanged_resource(self, iatikit_mock):
        """
        If ignore_hashes is set to True, then update should be triggered,
        even though the document is identical.
        """
        iatikit_mock.return_value = registry
        with open(join(
                dirname(__file__),
                'fixtures', 'registry', 'data', 'old-org',
                'old-org-acts.xml'), 'rb') as f:
            document = f.read()
        dataset = fac.DatasetFactory.create(
            name='old-org-acts',
            resources=[fac.ResourceFactory.create(
                url="https://old-org.nl/sites/default/files/" +
                    "IATI/activities.xml",
                last_parsed=datetime.datetime(2000, 1, 1),
                document=document,
            )]
        )
        resource = crawler.fetch_resource(
            dataset=dataset, ignore_hashes=True)
        self.assertEqual(None, resource.last_parsed)

    def test_parse_resource_succ(self):
        resource = Resource(document=b"<iati-activities />", url="http://foo")
        resource = crawler.parse_resource(resource)
        self.assertEqual([], list(resource.activities))
        self.assertEqual(None, resource.last_parse_error)
        now = datetime.datetime.utcnow()
        self.assertAlmostEqual(
            resource.last_parsed,
            now,
            delta=datetime.timedelta(seconds=15))

    def test_parse_resource_succ_replaces_activities(self):
        # what's in the db before the resource is updated
        act = fac.ActivityFactory.build(iati_identifier="deleted_activity")
        resource = fac.ResourceFactory.create(
            url="http://test",
            activities=[act]
        )
        # the updated resource (will remove the activities)
        resource.document = b"<iati-activities />"
        resource = crawler.parse_resource(resource)
        db.session.commit()
        self.assertEqual(None, Activity.query.get(act.iati_identifier))
        self.assertIn(
            "deleted_activity",
            [da.iati_identifier for da in DeletedActivity.query.all()]
        )

    def test_deleted_activity_removal(self):
        db.session.add(
            DeletedActivity(
                iati_identifier='test_deleted_activity',
                deletion_date=datetime.datetime(2000, 1, 1)))
        db.session.commit()
        resource = fac.ResourceFactory.create(
            url="http://test",
            document=b"""
                <iati-activities>
                  <iati-activity>
                    <iati-identifier>test_deleted_activity</iati-identifier>
                    <title>test_deleted_activity</title>
                    <reporting-org ref="GB-CHC-202918" type="21">Oxfam GB</reporting-org>
                  </iati-activity>
                </iati-activities>
            """,
        )
        self.assertIn(
            "test_deleted_activity",
            [da.iati_identifier for da in db.session.query(DeletedActivity).all()]
        )
        resource = crawler.parse_resource(resource)
        db.session.commit()
        self.assertNotIn(
            "test_deleted_activity",
            [da.iati_identifier for da in DeletedActivity.query.all()]
        )

    def test_last_changed_datetime(self):
        resource = fac.ResourceFactory.create(
            url="http://test",
            document=b"""
                <iati-activities>
                  <iati-activity>
                    <iati-identifier>test_deleted_activity</iati-identifier>
                    <title>test_deleted_activity</title>
                    <reporting-org ref="GB-CHC-202918" type="21">Oxfam GB</reporting-org>
                  </iati-activity>
                  <iati-activity>
                    <iati-identifier>test_deleted_activity_2</iati-identifier>
                    <title>test_deleted_activity_2</title>
                    <reporting-org ref="GB-CHC-202918" type="21">Oxfam GB</reporting-org>
                  </iati-activity>
                </iati-activities>
            """
        )
        crawler.parse_resource(resource)
        db.session.commit()
        db.session.query(Activity).update(
            values={'last_change_datetime': datetime.datetime(2000, 1, 1)},
            synchronize_session=False)
        db.session.commit()
        crawler.parse_resource(resource)
        acts = db.session.query(Activity).all()
        self.assertEqual(
            datetime.datetime(2000, 1, 1),
            acts[0].last_change_datetime)

    def test_parse_resource_fail(self):
        resource = Resource(document=b"", url="")
        with self.assertRaises(parse.ParserError):
            resource = crawler.parse_resource(resource)
            self.assertEqual(None, resource.last_parsed)

    @mock.patch('iatikit.data')
    def test_deleted_activities(self, iatikit_mock):
        fac.DatasetFactory.create(
            name='deleteme',
            resources=[fac.ResourceFactory.create(
                url="http://yes",
                activities=[
                    fac.ActivityFactory.build(
                        iati_identifier="deleted_activity",
                        title="orig",
                    )
                ]
            )]
        )
        self.assertIn("deleteme", [ds.name for ds in Dataset.query.all()])
        iatikit_mock.return_value = registry
        datasets = crawler.fetch_dataset_list()
        self.assertNotIn("deleteme", [ds.name for ds in datasets])
        self.assertIn(
            "deleted_activity",
            [da.iati_identifier for da in DeletedActivity.query.all()]
        )

    def test_document_metadata(self):
        res = fac.ResourceFactory.create(
            url="http://res2",
            document=open(fixture_filename("complex_example_dfid.xml")).read().encode()
        )
        result = crawler.parse_resource(res)

        self.assertEqual("1.00", result.version)


class TestResourceUpdate(AppTestCase):
    def test_activity_in_two_resources(self):
        # If an activity is reported in two resources, the one in the db
        # wins.

        # Example: Activity GB-1-111635 appears in two resources.
        # 'http://projects.dfid.gov.uk/iati/Region/798'
        # 'http://projects.dfid.gov.uk/iati/Country/CD'

        # this resouce was the first to import activity "47045-ARM-202-G05-H-00"
        fac.DatasetFactory.create(
            name='tst-a',
            resources=[fac.ResourceFactory.create(
                url=u"http://res1",
                activities=[
                    fac.ActivityFactory.build(
                        iati_identifier=u"47045-ARM-202-G05-H-00",
                        title=u"orig",
                    )
                ]
            )]
        )

        # this resource has just been retrieved, it also contains an
        # activity "47045-ARM-202-G05-H-00"
        fac.DatasetFactory.create(
            name='tst-b',
            resources=[fac.ResourceFactory.create(
                url=u"http://res2",
                document=open(fixture_filename("single_activity.xml")).read().encode()
            )]
        )

        crawler.update_activities("tst-b")
        self.assertEqual(
            u"orig",
            Activity.query.get(u"47045-ARM-202-G05-H-00").title
        )
