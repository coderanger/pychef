import os

import mock
import unittest2

from chef.api import ChefAPI


class APITestCase(unittest2.TestCase):
    def load(self, path):
        path = os.path.join(os.path.dirname(__file__), 'configs', path)
        return ChefAPI.from_config_file(path)

    @mock.patch('chef.api.subprocess.Popen')
    def test_config_with_interpolated_settings(self, mock_subproc_popen):
        process_mock = mock.Mock()
        output = b'{"chef_server_url": "http:///chef:4000", "client_key": "../client.pem",' \
                 b'"node_name": "test_1"}'
        attrs = {
            'communicate.return_value': (output, 'error'),
            'returncode': 0}
        process_mock.configure_mock(**attrs)
        mock_subproc_popen.return_value = process_mock

        api = self.load('basic_with_interpolated_values.rb')
        self.assertEqual(api.client, 'test_1')

    def test_basic(self):
        api = self.load('basic.rb')
        self.assertEqual(api.url, 'http://chef:4000')
        self.assertEqual(api.client, 'test_1')

    def test_current_dir(self):
        api = self.load('current_dir.rb')
        path = os.path.join(os.path.dirname(__file__), 'configs', 'test_1')
        self.assertEqual(os.path.normpath(api.client), path)

    def test_env_variables(self):
        try:
            os.environ['_PYCHEF_TEST_'] = 'foobar'
            api = self.load('env_values.rb')
            self.assertEqual(api.client, 'foobar')
        finally:
            del os.environ['_PYCHEF_TEST_']

    def test_bad_key_raises(self):
        invalids = [None, '']
        for item in invalids:
            self.assertRaises(
                ValueError, ChefAPI, 'foobar', item, 'user')
