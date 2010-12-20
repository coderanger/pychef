import os

from unittest2 import TestCase

from chef.api import ChefAPI

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))

def test_chef_api():
    return ChefAPI('https://api.opscode.com/organizations/pycheftest', os.path.join(TEST_ROOT, 'client.pem'), 'unittests')


class ChefTestCase(TestCase):
    """Base class for Chef unittests."""
    
    def setUp(self):
        super(ChefTestCase, self).setUp()
        self.api = test_chef_api
        self.api.set_default()
