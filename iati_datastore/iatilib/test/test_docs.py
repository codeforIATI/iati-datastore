from os.path import dirname, realpath, join
import subprocess

from . import ClientTestCase


class TestDocs(ClientTestCase):
    def setUp(self):
        super().setUp()
        current_path = dirname(dirname(dirname(realpath(__file__))))
        cwd = join(current_path, 'docs_source')
        subprocess.run(['make', 'dirhtml'], cwd=cwd)

    def test_docs(self):
        resp = self.client.get('/docs/')
        self.assertEqual(200, resp.status_code)
        self.assertIn(
            "What is IATI Datastore?",
            resp.data.decode())


class TestDocsRedirects(ClientTestCase):
    def test_error_api_redirect(self):
        resp = self.client.get('/error/')
        self.assertEqual(302, resp.status_code)
        self.assertRegex(resp.headers['Location'], '/docs/api/error/$')


class TestFavicon(ClientTestCase):
    def test_favicon(self):
        resp = self.client.get('/favicon.ico')
        self.assertEqual(200, resp.status_code)
        self.assertRegex(resp.content_type, "^image/")
