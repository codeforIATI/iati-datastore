from datetime import datetime
import json
from io import StringIO
from iatilib import codelists
from iatilib.frontend.serialize import jsonserializer
from iatilib.test import factories, AppTestCase


class FakePage(object):
    def __init__(self, items):
        self.items = items
        self.offset = 0
        self.limit = 50

    @property
    def total(self):
        return len(self.items)


class TestJson(AppTestCase):
    maxDiff = None

    def test_transaction_json(self):
        activity = factories.ActivityFactory.create()
        factories.TransactionFactory.create(
            activity=activity,
            value_amount=411900,
            value_date=datetime(2012, 12, 31),
            date=datetime(2012, 12, 31),
            flow_type=codelists.FlowType.private_development_finance,
            finance_type=codelists.FinanceType.standard_grant,
            aid_type=codelists.AidType.general_budget_support,
            disbursement_channel=codelists.DisbursementChannel.aid_in_kind_donors_manage_funds_themselves,
            tied_status=codelists.TiedStatus.untied,
        )

        json_output = jsonserializer.datastore_json(FakePage([activity]))
        output = json.load(StringIO(''.join(json_output)))

        transactions = {
            "transaction-type": {"code": "C"},
            "value": {
                "value-date": "2012-12-31",
                "text": "4119000.00"
            },
            "transaction-date": {"iso-date": "2012-12-31"},
            "flow-type": {"code": "30"},
            "finance-type": {"code": "110"},
            "aid-type": {"code": "A01"},
            "disbursement-channel": {"code": "4"},
            "tied-status": {"code": "5"}
        }
        self.assertCountEqual(transactions, output['iati-activities'][0]['transaction'][0])

    def test_whitespace_in_identifier(self):
        raw_xml = u"""
<iati-activity>
    <iati-identifier>
        AAA
    </iati-identifier>
</iati-activity>
"""
        activity = factories.ActivityFactory.create(raw_xml=raw_xml)
        json_output = jsonserializer.json(FakePage([activity]))
        output = json.load(StringIO(''.join(json_output)))
        self.assertEqual('\n        AAA\n    ', output['iati-activities'][0]['iati-activity']['iati-identifier'])

    def test_multiline(self):
        act_one = factories.ActivityFactory.create(
            iati_identifier='AAA')
        act_two = factories.ActivityFactory.create(
            iati_identifier='ZZZ')
        json_output = json.loads(''.join(jsonserializer.json(
            FakePage([act_one, act_two]))))
        self.assertEqual(2, len(json_output['iati-activities']))

    def test_version(self):
        activity = factories.ActivityFactory.create(version='x.yy')
        json_datastore_output = json.loads(''.join(jsonserializer.datastore_json(FakePage([activity]))))
        json_output = json.loads(''.join(jsonserializer.json(FakePage([activity]))))
        self.assertEqual('x.yy', json_datastore_output['iati-activities'][0]['version'])
        # This has the "iati-extra:" because it should match the XML output
        self.assertEqual('x.yy', json_output['iati-activities'][0]['iati-extra:version'])

    def test_wrapped(self):
        activity = factories.ActivityFactory.create()
        json_datastore_output = jsonserializer.datastore_json(
                FakePage([activity]))
        json_output = jsonserializer.json(
                FakePage([activity]))
        for output in [json_datastore_output, json_output]:
            output_dict = json.loads(''.join(output))
            self.assertIn('ok', output_dict)
            self.assertIn('total-count', output_dict)
            self.assertIn('start', output_dict)
            self.assertIn('limit', output_dict)
            self.assertIn('iati-activities', output_dict)

    def test_unwrapped(self):
        activity = factories.ActivityFactory.create()
        json_datastore_output = jsonserializer.datastore_json(
                FakePage([activity]), wrapped=False)
        json_output = jsonserializer.json(
                FakePage([activity]), wrapped=False)
        for output in [json_datastore_output, json_output]:
            output_dict = json.loads(''.join(output))
            self.assertNotIn('ok', output_dict)
            self.assertNotIn('total-count', output_dict)
            self.assertNotIn('start', output_dict)
            self.assertNotIn('limit', output_dict)
            self.assertIn('iati-activities', output_dict)
