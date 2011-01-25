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

    def test_search_role(self):
        s = Search('node', 'role:test_1')
        self.assertGreaterEqual(len(s), 2)
        self.assertIn('test_1', s)
        self.assertNotIn('test_2', s)
        self.assertIn('test_3', s)

    def test_list(self):
        searches = Search.list()
        self.assertIn('node', searches)
        self.assertIn('role', searches)

