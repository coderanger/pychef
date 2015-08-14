import six.moves
import os
import random
from functools import wraps

import mock
from unittest2 import TestCase, skipUnless

from chef.api import ChefAPI
from chef.exceptions import ChefError
from chef.search import Search

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))

def skipSlowTest():
    return skipUnless(os.environ.get('PYCHEF_SLOW_TESTS'), 'slow tests skipped, set $PYCHEF_SLOW_TESTS=1 to enable')

class mockSearch(object):
    def __init__(self, search_data):
        self.search_data = search_data

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(inner_self):
            return mock.patch('chef.search.Search', side_effect=self._search_inst)(fn)(inner_self)
        return wrapper

    def _search_inst(self, index, q='*:*', *args, **kwargs):
        data = self.search_data[index, q]
        if not isinstance(data, dict):
            data = {'total': len(data), 'rows': data}
        search = Search(index, q, *args, **kwargs)
        search._data = data
        return search


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
            except ChefError as e:
                print(e)
                # Continue running

    def register(self, obj):
        self.objects.append(obj)

    def random(self, length=8, alphabet='0123456789abcdef'):
        return ''.join(random.choice(alphabet) for _ in six.moves.range(length))
