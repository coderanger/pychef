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
        self.assertItemsEqual(list(bag.keys()), ['item_1', 'item_2'])
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

    def test_direct_item(self):
        item = DataBagItem('test_1', 'item_1')
        self.assertEqual(item['test_attr'], 1)
        self.assertEqual(item['other'], 'foo')

    def test_direct_item_bag(self):
        bag = DataBag('test_1')
        item = DataBagItem(bag, 'item_1')
        self.assertEqual(item['test_attr'], 1)
        self.assertEqual(item['other'], 'foo')

    def test_create_bag(self):
        name = self.random()
        bag = DataBag.create(name)
        self.register(bag)
        self.assertIn(name, DataBag.list())

    def test_create_item(self):
        value = self.random()
        bag_name = self.random()
        bag = DataBag.create(bag_name)
        self.register(bag)
        item_name = self.random()
        item = DataBagItem.create(bag, item_name, foo=value)
        self.assertIn('foo', item)
        self.assertEqual(item['foo'], value)
        self.assertIn(item_name, bag)
        bag2 = DataBag(bag_name)
        self.assertIn(item_name, bag2)
        item2 = bag2[item_name]
        self.assertIn('foo', item)
        self.assertEqual(item['foo'], value)

    def test_set_item(self):
        value = self.random()
        value2 = self.random()
        bag_name = self.random()
        bag = DataBag.create(bag_name)
        self.register(bag)
        item_name = self.random()
        item = DataBagItem.create(bag, item_name, foo=value)
        item['foo'] = value2
        item.save()
        self.assertEqual(item['foo'], value2)
        item2 = DataBagItem(bag, item_name)
        self.assertEqual(item2['foo'], value2)
