from collections import namedtuple
from io import StringIO

import csv

TestWrapper = namedtuple('TestWrapper', 'items total offset limit')


def load_csv(data):
    sio = StringIO(data.decode("utf-8"))
    return list(csv.DictReader(sio))


class CSVTstMixin(object):
    def process(self, data):
        csv_str = u"".join(self.serialize(TestWrapper(data, 0, 0, 0))).encode('utf-8')
        return load_csv(csv_str)

    def serialize(self, data):
        raise Exception("Not Implemented")

    def assertField(self, mapping, row):
        assert len(mapping) == 1
        key, val = list(mapping.items())[0]
        self.assertIn(key, row)
        self.assertEqual(row[key], val)
