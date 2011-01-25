from unittest2 import skip

from chef import Search
from chef.exceptions import ChefError
from chef.tests import ChefTestCase

class SearchTestCase(ChefTestCase):
    def test_search_all(self):
        s = Search('node')
        self.assertGreaterEqual(len(s), 3)
        self.assertIn('test_1', s)
        self.assertIn('test_2', s)
        self.assertIn('test_3', s)

    def test_search_query(self):
        s = Search('node', 'role:test_1')
        self.assertGreaterEqual(len(s), 2)
        self.assertIn('test_1', s)
        self.assertNotIn('test_2', s)
        self.assertIn('test_3', s)

    def test_list(self):
        searches = Search.list()
        self.assertIn('node', searches)
        self.assertIn('role', searches)

    def test_search_set_query(self):
        s = Search('node').query('role:test_1')
        self.assertGreaterEqual(len(s), 2)
        self.assertIn('test_1', s)
        self.assertNotIn('test_2', s)
        self.assertIn('test_3', s)

    def test_search_call(self):
        s = Search('node')('role:test_1')
        self.assertGreaterEqual(len(s), 2)
        self.assertIn('test_1', s)
        self.assertNotIn('test_2', s)
        self.assertIn('test_3', s)

    @skip('sorting is being weird')
    def test_search_sort(self):
        s = Search('node', sort='name')
        self.assertLess(s.index('test_1'), s.index('test_3'))

    @skip('sorting is being weird')
    def test_search_sort_asc(self):
        s = Search('node', sort='X_CHEF_id_CHEF_X asc')
        self.assertLess(s.index('test_1'), s.index('test_3'))

    @skip('sorting is being weird')
    def test_search_sort_desc(self):
        s = Search('node', 'name:*', sort='name desc')
        self.assertGreater(s.index('test_1'), s.index('test_3'))
