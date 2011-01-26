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

    @skip('search sorting not working')
    def test_search_sort(self):
        s = Search('node', sort='test_sort_key')
        self.assertLess(s.index('test_1'), s.index('test_3'))

    @skip('search sorting not working')
    def test_search_sort_asc(self):
        s = Search('node', sort='test_sort_key asc')
        self.assertLess(s.index('test_1'), s.index('test_3'))

    @skip('search sorting not working')
    def test_search_sort_desc(self):
        s = Search('node', sort='test_sort_key desc')
        self.assertGreater(s.index('test_1'), s.index('test_3'))

    def test_rows(self):
        s = Search('node', rows=1)
        self.assertEqual(len(s), 1)
        self.assertGreaterEqual(s.total, 3)

    def test_start(self):
        s = Search('node', start=1)
        self.assertEqual(len(s), s.total-1)
        self.assertGreaterEqual(s.total, 3)

    def test_slice(self):
        s = Search('node')[1:2]
        self.assertEqual(len(s), 1)
        self.assertGreaterEqual(s.total, 3)

        s2 = s[1:2]
        self.assertEqual(len(s2), 1)
        self.assertGreaterEqual(s2.total, 3)
        self.assertNotEqual(s[0]['name'], s2[0]['name'])

        s3 = Search('node')[2:3]
        self.assertEqual(len(s3), 1)
        self.assertGreaterEqual(s3.total, 3)
        self.assertEqual(s2[0]['name'], s3[0]['name'])

    def test_object(self):
        s = Search('node', 'name:test_1')
        self.assertEqual(len(s), 1)
        node = s[0].object
        self.assertEqual(node.name, 'test_1')
        self.assertEqual(node.run_list, ['role[test_1]'])
