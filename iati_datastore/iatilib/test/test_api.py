import os
import json
from datetime import datetime
from xml.etree import ElementTree as ET
import csv
from io import StringIO

import mock

from . import factories as fac
from . import ClientTestCase
from iatilib import parse, db, model


class TestLatestApiRedirect(ClientTestCase):
    def test_latest_api_redirect(self):
        resp = self.client.get('/api/')
        self.assertEqual(302, resp.status_code)
        self.assertRegex(resp.headers['Location'], '/api/1/$')


class TestListRoutes(ClientTestCase):
    def test_list_routes(self):
        resp = self.client.get('/api/1/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual("application/json", resp.content_type)
        data = json.loads(resp.data)
        self.assertIn('http://localhost/api/1/', data)


class TestAbout(ClientTestCase):
    def test_about_http(self):
        resp = self.client.get('/api/1/about/')
        self.assertEqual(200, resp.status_code)


class TestAboutDatasets(ClientTestCase):
    def test_about(self):
        fac.DatasetFactory.create(
            name='tst-old',
            resources=[fac.ResourceFactory.create(
                url="http://foo",
            )]
        )
        resp = self.client.get('/api/1/about/dataset/')
        data = json.loads(resp.data)
        self.assertEqual(200, resp.status_code)
        self.assertIn("datasets", data)
        self.assertEqual("tst-old", data["datasets"][0])

    def test_about_details(self):
        fac.DatasetFactory.create(
            name='tst-old',
            resources=[fac.ResourceFactory.create(
                url="http://foo",
            )]
        )
        resp = self.client.get('/api/1/about/dataset/?detail=true')
        data = json.loads(resp.data)
        self.assertEqual(200, resp.status_code)
        self.assertIn("datasets", data)
        self.assertEqual('http://foo', data["datasets"][0]['url'])
        self.assertIn("ok", data)
        self.assertIn("total-count", data)

    def test_about_dataset(self):
        fac.DatasetFactory.create(
            name='tst-old',
            resources=[fac.ResourceFactory.create(
                url="http://foo",
            )]
        )
        resp = self.client.get('/api/1/about/dataset/tst-old/')
        data = json.loads(resp.data)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('tst-old', data["dataset"])
        self.assertEqual(1, data["num_resources"])
        self.assertEqual('http://foo', data["resources"][0]['url'])

    def test_about_not_a_dataset(self):
        resp = self.client.get('/api/1/about/dataset/bad-dataset-id/')
        self.assertEqual(404, resp.status_code)

    def test_about_invalid_filter(self):
        resp = self.client.get('/api/1/about/dataset/?invalid=true')
        self.assertEqual(400, resp.status_code)
        self.assertIn(
            "Invalid arguments passed as filter",
            resp.data.decode())


class TestErrorDatasets(ClientTestCase):
    def test_errors(self):
        fac.LogFactory.create()
        resp = self.client.get('/api/1/error/dataset/')
        data = json.loads(resp.data)
        self.assertEqual(200, resp.status_code)
        self.assertIn("errored_datasets", data)
        self.assertEqual(
            'bad-dataset',
            data['errored_datasets'][0]['dataset'])

    def test_errors_log(self):
        fac.LogFactory.create()
        resp = self.client.get('/api/1/error/dataset.log')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            "text/plain; charset=utf-8", resp.content_type)

    def test_error_log(self):
        fac.LogFactory.create()
        resp = self.client.get('/api/1/error/dataset.log/bad-dataset/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            "text/plain; charset=utf-8", resp.content_type)

    def test_error(self):
        fac.LogFactory.create()
        resp = self.client.get('/api/1/error/dataset/bad-dataset/')
        data = json.loads(resp.data)
        self.assertEqual(200, resp.status_code)
        self.assertIn("errors", data)
        self.assertEqual(
            'bad-dataset',
            data['errors'][0]['dataset'])
        self.assertEqual(
            'Dataset is broken',
            data['errors'][0]['msg'])


class TestDeletedActivitiesView(ClientTestCase):
    def test_deleted_activities(self):
        db.session.add(model.DeletedActivity(
            iati_identifier='test',
            deletion_date=datetime(2000, 1, 1))
        )
        db.session.commit()
        resp = self.client.get('api/1/about/deleted/')
        data = json.loads(resp.data)
        deleted_activities = data['deleted_activities']
        self.assertEqual("test", deleted_activities[0]['iati_identifier'])
        self.assertEqual("2000-01-01", deleted_activities[0]['deletion_date'])

    def test_deleted_invalid_filter(self):
        resp = self.client.get('/api/1/about/deleted/?invalid=true')
        self.assertEqual(400, resp.status_code)
        self.assertIn(
            "Invalid arguments passed as filter",
            resp.data.decode())


class TestMetaFilters(ClientTestCase):
    def test_http(self):
        resp = self.client.get('/api/1/meta/filters/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual("application/json", resp.content_type)
        self.assertIn("filters", json.loads(resp.data))


class TestEmptyDb_JSON(ClientTestCase):
    url = '/api/1/access/activity/'

    def test_http_ok(self):
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)

    def test_content_type(self):
        resp = self.client.get(self.url)
        self.assertEqual("application/json", resp.content_type)

    def tests_json_decode(self):
        resp = self.client.get(self.url)
        self.assertTrue(json.loads(resp.data))

    def test_json_ok(self):
        resp = self.client.get(self.url)
        js = json.loads(resp.data)
        self.assertTrue(js["ok"])

    def test_json_results(self):
        resp = self.client.get(self.url)
        js = json.loads(resp.data)
        self.assertEqual(js["iati-activities"], [])


class TestEmptyDb_XML(ClientTestCase):
    """
    Raw XML for empty db.

    Basic layout (see: https://github.com/okfn/iati-datastore/issues/14)
    <result>
       <page>5</page>
       ...metadata here...
       <result-activities>...concatted string...
       </result-activities>
    </result>
    """
    url = '/api/1/access/activity.xml'

    def test_http_ok(self):
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)

    def test_content_type(self):
        resp = self.client.get(self.url)
        self.assertEqual("application/xml; charset=utf-8", resp.content_type)

    def test_decode(self):
        resp = self.client.get(self.url)
        # an ElementTree node object does not test as true
        self.assertTrue(hasattr(ET.fromstring(resp.get_data(as_text=True)), "tag"))

    def test_resp_ok(self):
        resp = self.client.get(self.url)
        xml = ET.fromstring(resp.get_data(as_text=True))
        self.assertTrue(xml.find('ok').text == 'True')

    def test_results(self):
        resp = self.client.get(self.url)
        xml = ET.fromstring(resp.get_data(as_text=True))
        self.assertEqual(xml.findall('result-activities'), [])

    def test_root_element(self):
        resp = self.client.get(self.url)
        xml = ET.fromstring(resp.get_data(as_text=True))
        self.assertEqual(xml.tag, "result")


class TestEmptyDb_ActivityCSV(ClientTestCase):
    """
    CSV for empty db
    """
    url = '/api/1/access/activity.csv'

    def test_http_ok(self):
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)

    def test_content_type(self):
        resp = self.client.get(self.url)
        self.assertEqual("text/csv; charset=utf-8", resp.content_type)

    def test_fields(self):
        resp = self.client.get(self.url)
        headers = next(csv.reader(StringIO(resp.get_data(as_text=True))))
        for exp in ["start-planned", "start-actual"]:
            self.assertIn(exp, headers)


class TestEmptyDb_TransactionCSV(ClientTestCase):
    """
    CSV for empty db
    """
    url = '/api/1/access/transaction.csv'

    def test_http_ok(self):
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)

    def test_content_type(self):
        resp = self.client.get(self.url)
        self.assertEqual("text/csv; charset=utf-8", resp.content_type)


class TestEmptyDb_BudgetCSV(ClientTestCase):
    """
    CSV for empty db
    """
    url = '/api/1/access/budget.csv'

    def test_http_ok(self):
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)

    def test_content_type(self):
        resp = self.client.get(self.url)
        self.assertEqual("text/csv; charset=utf-8", resp.content_type)


def fixture_filename(fix_name):
    return os.path.join(
            os.path.dirname(__file__), "fixtures", fix_name)


def load_fix(fix_name):
    activities = parse.document_from_file(fixture_filename(fix_name))
    db.session.add_all(activities)
    db.session.commit()


class TestSingleActivity(ClientTestCase):
    """
    Different reprisentations of the same input activity
    """

    def test_xml_activity_count(self):
        load_fix("single_activity.xml")
        resp = self.client.get('/api/1/access/activity.xml')
        xml = ET.fromstring(resp.get_data(as_text=True))
        self.assertEqual(1, len(xml.findall('.//iati-activity')))

    def test_xml_activity_data(self):
        load_fix("single_activity.xml")
        in_xml = ET.parse(fixture_filename("single_activity.xml"))
        resp = self.client.get('/api/1/access/activity.xml')
        xml = ET.fromstring(resp.get_data(as_text=True))
        x1 = in_xml.find('.//iati-activity')
        x2 = xml.find('.//iati-activity')
        self.assertEqual(x1, x2)

    def test_csv_activity_count(self):
        load_fix("single_activity.xml")
        with self.client as client:
            resp = client.get('/api/1/access/activity.csv')
            self.assertEqual(2, resp.get_data(as_text=True).count("\n"))


class TestManyActivities(ClientTestCase):
    def test_xml_activity_count(self):
        load_fix("many_activities.xml")
        resp = self.client.get('/api/1/access/activity.xml')
        xml = ET.fromstring(resp.get_data(as_text=True))
        self.assertEqual(2, len(xml.findall('.//iati-activity')))

    def test_xml_activity_data(self):
        load_fix("many_activities.xml")
        in_xml = ET.parse(fixture_filename("many_activities.xml"))
        resp = self.client.get('/api/1/access/activity.xml')
        xml = ET.fromstring(resp.get_data(as_text=True))
        self.assertEqual(
            ET.tostring(in_xml.find('.//iati-activity')),
            ET.tostring(xml.find('.//iati-activity')))

    def test_csv_activity_count(self):
        load_fix("many_activities.xml")
        with self.client as client:
            resp = client.get('/api/1/access/activity.csv')
            reader = csv.DictReader(StringIO(resp.get_data(as_text=True)))
            self.assertEqual(2, len(list(reader)))


class TestPagination(ClientTestCase):
    def test_invalid_page(self):
        resp = self.client.get('/api/1/access/activity/?offset=-1')
        self.assertEqual(400, resp.status_code)


class ApiViewMixin(object):
    @mock.patch('iatilib.frontend.api1.validators.activity_api_args')
    def test_validator_called(self, mock):
        self.client.get(self.base_url)
        self.assertEqual(1, mock.call_count)

    def test_filter_called(self):
        with mock.patch(self.filter) as mm:
            self.client.get(self.base_url + '?recipient-country=MW')
            self.assertEqual(1, mm.call_count)

    def test_serializer_called(self):
        with mock.patch(self.serializer) as mm:
            self.client.get(self.base_url)
            self.assertEqual(1, mm.call_count)

    def test_invalid_format(self):
        resp = self.client.get(self.base_url + ".zzz")
        self.assertEqual(404, resp.status_code)

    def test_junk_before_format(self):
        url = self.base_url[:-4] + '-bad.csv'
        resp = self.client.get(url)
        self.assertEqual(404, resp.status_code)

    def test_junk_in_format(self):
        url = self.base_url[:-4] + '.bad-csv'
        resp = self.client.get(url)
        self.assertEqual(404, resp.status_code)


class TestActivityView(ClientTestCase, ApiViewMixin):
    base_url = '/api/1/access/activity.csv'
    filter = 'iatilib.frontend.api1.ActivityCSVView.filter'
    serializer = 'iatilib.frontend.api1.ActivityCSVView.serializer'


class TestActivityBySectorView(ClientTestCase, ApiViewMixin):
    base_url = '/api/1/access/activity/by_sector.csv'
    filter = 'iatilib.frontend.api1.ActivityBySectorView.filter'
    serializer = 'iatilib.frontend.api1.ActivityBySectorView.serializer'


class TestActivityByCountryView(ClientTestCase, ApiViewMixin):
    base_url = '/api/1/access/activity/by_country.csv'
    filter = 'iatilib.frontend.api1.ActivityByCountryView.filter'
    serializer = 'iatilib.frontend.api1.ActivityByCountryView.serializer'


class CommonTransactionTests(object):
    def test_reporting_org(self):
        load_fix("transaction_ref.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('reporting-org-ref')
        self.assertEqual(u'GB-CHC-285776', output[1][i])

    def test_ref_output(self):
        load_fix("transaction_ref.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_ref')
        self.assertEqual(u'36258', output[1][i])
        self.assertEqual(u'', output[2][i])

    def test_transaction_value_currency(self):
        load_fix("transaction_provider.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_value_currency')
        self.assertEqual(u'GBP', output[1][i])

    def test_transaction_value_value_date(self):
        load_fix("transaction_provider.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_value_value-date')
        self.assertEqual(u'2011-08-19', output[1][i])

    def test_provider_org_ref_output(self):
        load_fix("transaction_provider.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_provider-org_ref')
        self.assertEqual(u'GB-1-201242-101', output[1][i])

    def test_provider_org_output(self):
        load_fix("transaction_provider.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_provider-org')
        self.assertEqual(u'DFID', output[1][i])

    def test_provider_org_activity_id_output(self):
        load_fix("provider-activity-id.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_provider-org_provider-activity-id')
        self.assertEqual(u'GB-1-202907', output[1][i])

    def test_receiver_org_ref_output(self):
        load_fix("transaction_provider.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_receiver-org_ref')
        self.assertEqual(u'GB-CHC-313139', output[1][i])

    def test_receiver_org_output(self):
        """receiver_org should be in transaction.csv output"""
        load_fix("provider-activity-id.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_receiver-org')
        self.assertEqual(u'Bond', output[1][i])

    def test_receiver_org_activity_id_output(self):
        load_fix("provider-activity-id.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_receiver-org_receiver-activity-id')
        self.assertEqual(u'GB-CHC-1068839-dfid_ag_11-13', output[1][i])

    def test_description(self):
        load_fix("transaction_provider.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_description')
        self.assertEqual(
                u'Funds received from DFID for activities in Aug- Sept 2011',
                output[1][i]
        )

    def test_flow_type(self):
        load_fix("transaction_fields_code_lists.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_flow-type_code')
        self.assertEqual(u'30', output[1][i])

    def test_finance_type(self):
        load_fix("transaction_fields_code_lists.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_finance-type_code')
        self.assertEqual(u'110', output[1][i])

    def test_aid_type(self):
        load_fix("transaction_fields_code_lists.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_aid-type_code')
        self.assertEqual(u'B01', output[1][i])

    def test_tied_status(self):
        load_fix("transaction_fields_code_lists.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_tied-status_code')
        self.assertEqual(u'5', output[1][i])

    def test_disbursement_channel_status(self):
        load_fix("transaction_fields_code_lists.xml")
        output = list(csv.reader(StringIO(self.client.get(self.base_url).get_data(as_text=True))))
        csv_headers = output[0]
        i = csv_headers.index('transaction_disbursement-channel_code')
        self.assertEqual(u'2', output[1][i])


class TestTransactionView(ClientTestCase, ApiViewMixin, CommonTransactionTests):
    base_url = '/api/1/access/transaction.csv'
    filter = 'iatilib.frontend.api1.TransactionsView.filter'
    serializer = 'iatilib.frontend.api1.TransactionsView.serializer'


class TestTransactionByCountryView(ClientTestCase, ApiViewMixin, CommonTransactionTests):
    base_url = '/api/1/access/transaction/by_country.csv'
    filter = 'iatilib.frontend.api1.TransactionsByCountryView.filter'
    serializer = 'iatilib.frontend.api1.TransactionsByCountryView.serializer'


class TestTransactionBySectorView(ClientTestCase, ApiViewMixin, CommonTransactionTests):
    base_url = '/api/1/access/transaction/by_sector.csv'
    filter = 'iatilib.frontend.api1.TransactionsBySectorView.filter'
    serializer = 'iatilib.frontend.api1.TransactionsBySectorView.serializer'


class TestBudgetView(ClientTestCase):
    base_url = '/api/1/access/budget.csv'
    filter = 'iatilib.frontend.api1.dsfilter.budgets'
    serializer = 'iatilib.frontend.api1.serialize.budget_csv'


class TestBudgetByCountryView(ClientTestCase, ApiViewMixin):
    base_url = '/api/1/access/budget/by_country.csv'
    filter = 'iatilib.frontend.api1.BudgetsByCountryView.filter'
    serializer = 'iatilib.frontend.api1.BudgetsByCountryView.serializer'


class TestBudgetBySectorView(ClientTestCase, ApiViewMixin):
    base_url = '/api/1/access/budget/by_sector.csv'
    filter = 'iatilib.frontend.api1.BudgetsBySectorView.filter'
    serializer = 'iatilib.frontend.api1.BudgetsBySectorView.serializer'
