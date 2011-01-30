from chef import DataBag, DataBagItem, Search
from chef.exceptions import ChefError
from chef.tests import ChefTestCase

class DataBagTestCase(ChefTestCase):
    def test_list(self):
        bags = DataBag.list()
        self.assertIn('test_1', bags)
        self.assertIsInstance(bags['test_1'], DataBag)

    def test_keys(self):
        bag = DataBag('test_1')
        self.assertItemsEqual(bag.keys(), ['item_1', 'item_2'])
        self.assertItemsEqual(iter(bag), ['item_1', 'item_2'])

    def test_item(self):
        bag = DataBag('test_1')
        item = bag['item_1']
        self.assertEqual(item['test_attr'], 1)
        self.assertEqual(item['other'], 'foo')

    def test_search_item(self):
        self.assertIn('test_1', Search.list())
        q = Search('test_1')
        self.assertIn('item_1', q)
        self.assertIn('item_2', q)
        self.assertEqual(q['item_1']['raw_data']['test_attr'], 1)
        item = q['item_1'].object
        self.assertIsInstance(item, DataBagItem)
        self.assertEqual(item['test_attr'], 1)
