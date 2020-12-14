from click.testing import CliRunner
import mock

from iatilib import console
from . import AppTestCase


class ConsoleTestCase(AppTestCase):
    def setUp(self):
        super().setUp()
        self.runner = self.app.test_cli_runner()

    @mock.patch('subprocess.run')
    def test_build_docs(self, mock):
        command = 'make dirhtml'
        result = self.runner.invoke(console.build_docs)
        self.assertEquals(1, mock.call_count)
        self.assertEquals(mock.call_args.args[0], command.split(' '))
