import mock

from iatilib import console, crawler
from iatilib.model import Log
from . import AppTestCase, factories as fac


class ConsoleTestCase(AppTestCase):
    def setUp(self):
        super().setUp()
        self.runner = self.app.test_cli_runner()

    @mock.patch('subprocess.run')
    def test_build_docs(self, mock):
        command = 'make dirhtml'
        result = self.runner.invoke(console.build_docs)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, mock.call_count)
        self.assertEqual(mock.call_args.args[0], command.split(' '))

    @mock.patch('subprocess.run')
    def test_build_query_builder(self, mock):
        install_command = 'npm i'
        build_command = 'npm run generate'
        result = self.runner.invoke(console.build_query_builder)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(2, mock.call_count)
        args = [' '.join(arg_list.args[0])
                for arg_list in mock.call_args_list]
        self.assertIn(install_command, args)
        self.assertIn(build_command, args)

    def test_cleanup(self):
        fac.LogFactory.create(logger='crawler')
        fac.LogFactory.create(logger='failed_activity')
        self.assertEqual(2, len(Log.query.all()))
        result = self.runner.invoke(console.cleanup)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, len(Log.query.all()))

    @mock.patch('click.confirm')
    @mock.patch('iatilib.db.drop_all')
    def test_drop_db(self, prompt_mock, drop_all_mock):
        result = self.runner.invoke(console.drop_database)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, prompt_mock.call_count)
        self.assertEqual(1, drop_all_mock.call_count)

    @mock.patch('iatilib.rq.get_queue')
    def test_status_cmd(self, rq_mock):
        result = self.runner.invoke(crawler.status_cmd)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, rq_mock.call_count)

    @mock.patch('iatikit.download')
    def test_download_cmd(self, iatikit_mock):
        result = self.runner.invoke(crawler.download_cmd)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, iatikit_mock.data.call_count)

    @mock.patch('iatilib.crawler.fetch_dataset_list')
    def test_fetch_dataset_list_cmd(self, fetch_dataset_list_mock):
        result = self.runner.invoke(crawler.fetch_dataset_list_cmd)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, fetch_dataset_list_mock.call_count)
