from chef import Environment
from chef.exceptions import ChefAPIVersionError
from chef.tests import ChefTestCase, test_chef_api

class EnvironmentTestCase(ChefTestCase):
    def test_version_error_list(self):
        with test_chef_api(version='0.9.0'):
            with self.assertRaises(ChefAPIVersionError):
                Environment.list()

    def test_version_error_create(self):
        with test_chef_api(version='0.9.0'):
            with self.assertRaises(ChefAPIVersionError):
                Environment.create(self.random())

    def test_version_error_init(self):
        with test_chef_api(version='0.9.0'):
            with self.assertRaises(ChefAPIVersionError):
                Environment(self.random())
