from . import ClientTestCase


class TestLatestApiRedirect(ClientTestCase):
    def test_builder_errors(self):
        resp = self.client.get(
            '/build/api/1/access/nonsense/')
        self.assertEqual(404, resp.status_code)
        resp = self.client.get(
            '/build/api/1/access/activity/nonsense.xml')
        self.assertEqual(404, resp.status_code)
        resp = self.client.get(
            '/build/api/1/access/activity/by_country.nonsense')
        self.assertEqual(404, resp.status_code)

    def test_builder_activity_xml(self):
        url_from = '/build/api/1/access/activity.xml'
        url_to = '/'
        resp = self.client.get(url_from)
        self.assertEqual(302, resp.status_code)
        self.assertTrue(resp.headers['Location'].endswith(url_to))

    def test_builder_transaction_by_country_csv(self):
        url_from = '/build/api/1/access/transaction/by_country.csv'
        url_to = '/?breakdown=transaction&grouping=%2Fby_country&format=csv'
        resp = self.client.get(url_from)
        self.assertEqual(302, resp.status_code)
        self.assertTrue(resp.headers['Location'].endswith(url_to))
