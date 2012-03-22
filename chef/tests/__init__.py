import os
import random

from unittest2 import TestCase, skipUnless

from chef.api import ChefAPI
from chef.exceptions import ChefError

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))

def skipSlowTest():
    return skipUnless(os.environ.get('PYCHEF_SLOW_TESTS'), 'slow tests skipped, set $PYCHEF_SLOW_TESTS=1 to enable')


def test_chef_api(**kwargs):
    return ChefAPI('https://api.opscode.com/organizations/pycheftest', os.path.join(TEST_ROOT, 'client.pem'), 'unittests', **kwargs)


class ChefTestCase(TestCase):
    """Base class for Chef unittests."""

    def setUp(self):
        super(ChefTestCase, self).setUp()
        self.api = test_chef_api()
        self.api.set_default()
        self.objects = []

    def tearDown(self):
        for obj in self.objects:
            try:
                obj.delete()
            except ChefError, e:
                print e
                # Continue running

    def register(self, obj):
        self.objects.append(obj)

    def random(self, length=8, alphabet='0123456789abcdef'):
        return ''.join(random.choice(alphabet) for _ in xrange(length))
