import os

import unittest2

from chef.api import ChefAPI

class APITestCase(unittest2.TestCase):
    def load(self, path):
        path = os.path.join(os.path.dirname(__file__), 'configs', path)
        return ChefAPI.from_config_file(path)

    def test_basic(self):
        api = self.load('basic.rb')
        self.assertEqual(api.url, 'http://chef:4000')
        self.assertEqual(api.client, 'test_1')

    def test_current_dir(self):
        api = self.load('current_dir.rb')
        path = os.path.join(os.path.dirname(__file__), 'configs', 'test_1')
        self.assertEqual(api.client, path)

    def test_env_variables(self):
        username = os.environ.get('LOGNAME')
        if username is None:
            self.fail('could not read $LOGNAME from environment')
        api = self.load('env_values.rb')
        self.assertEqual(api.client, username)
