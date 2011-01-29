from unittest2 import TestCase, skip

from chef import Node
from chef.exceptions import ChefError
from chef.node import NodeAttributes
from chef.tests import ChefTestCase

class NodeAttributeTestCase(TestCase):
    def test_getitem(self):
        attrs = NodeAttributes([{'a': 1}])
        self.assertEqual(attrs['a'], 1)
    
    def test_setitem(self):
        data = {'a': 1}
        attrs = NodeAttributes([data], write=data)
        attrs['a'] = 2
        self.assertEqual(attrs['a'], 2)
        self.assertEqual(data['a'], 2)

    def test_getitem_nested(self):
         attrs = NodeAttributes([{'a': {'b': 1}}])
         self.assertEqual(attrs['a']['b'], 1)
    
    def test_set_nested(self):
        data = {'a': {'b': 1}}
        attrs = NodeAttributes([data], write=data)
        attrs['a']['b'] = 2
        self.assertEqual(attrs['a']['b'], 2)
        self.assertEqual(data['a']['b'], 2)
    
    def test_search_path(self):
        attrs = NodeAttributes([{'a': 1}, {'a': 2}])
        self.assertEqual(attrs['a'], 1)
    
    def test_search_path_nested(self):
        data1 = {'a': {'b': 1}}
        data2 = {'a': {'b': 2}}
        attrs = NodeAttributes([data1, data2])
        self.assertEqual(attrs['a']['b'], 1)
    
    def test_read_only(self):
        attrs = NodeAttributes([{'a': 1}])
        with self.assertRaises(ChefError):
            attrs['a'] = 2

    def test_get(self):
        attrs = NodeAttributes([{'a': 1}])
        self.assertEqual(attrs.get('a'), 1)

    def test_get_default(self):
        attrs = NodeAttributes([{'a': 1}])
        self.assertEqual(attrs.get('b'), None)

    def test_getitem_keyerror(self):
        attrs = NodeAttributes([{'a': 1}])
        with self.assertRaises(KeyError):
            attrs['b']

    def test_iter(self):
        attrs = NodeAttributes([{'a': 1, 'b': 2}])
        self.assertEqual(set(attrs), set(['a', 'b']))

    def test_iter2(self):
        attrs = NodeAttributes([{'a': {'b': 1, 'c': 2}}])
        self.assertEqual(set(attrs['a']), set(['b', 'c']))

    def test_len(self):
        attrs = NodeAttributes([{'a': 1, 'b': 2}])
        self.assertEqual(len(attrs), 2)

    def test_len2(self):
        attrs = NodeAttributes([{'a': {'b': 1, 'c': 2}}])
        self.assertEqual(len(attrs), 1)
        self.assertEqual(len(attrs['a']), 2)

    def test_get_dotted(self):
        attrs = NodeAttributes([{'a': {'b': 1}}])
        self.assertEqual(attrs.get_dotted('a.b'), 1)

    def test_get_dotted_keyerror(self):
        attrs = NodeAttributes([{'a': {'b': 1}}])
        with self.assertRaises(KeyError):
            attrs.get_dotted('a.b.c')

    def test_set_dotted(self):
        data = {'a': {'b': 1}}
        attrs = NodeAttributes([data], write=data)
        attrs.set_dotted('a.b', 2)
        self.assertEqual(attrs['a']['b'], 2)
        self.assertEqual(attrs.get_dotted('a.b'), 2)
        self.assertEqual(data['a']['b'], 2)

    def test_set_dotted2(self):
        data = {'a': {'b': 1}}
        attrs = NodeAttributes([data], write=data)
        attrs.set_dotted('a.c.d', 2)
        self.assertEqual(attrs['a']['c']['d'], 2)
        self.assertEqual(attrs.get_dotted('a.c.d'), 2)
        self.assertEqual(data['a']['c']['d'], 2)


class NodeTestCase(ChefTestCase):
    def setUp(self):
        super(NodeTestCase, self).setUp()
        self.node = Node('test_1')

    def test_default_attr(self):
        self.assertEqual(self.node.default['test_attr'], 'default')

    def test_normal_attr(self):
        self.assertEqual(self.node.normal['test_attr'], 'normal')

    def test_override_attr(self):
        self.assertEqual(self.node.override['test_attr'], 'override')

    def test_composite_attr(self):
        self.assertEqual(self.node.attributes['test_attr'], 'override')

    def test_getitem(self):
        self.assertEqual(self.node['test_attr'], 'override')

    def test_create(self):
        name = self.random()
        node = Node.create(name, run_list=['recipe[foo]'])
        self.register(node)
        self.assertEqual(node.run_list, ['recipe[foo]'])

        node2 = Node(name)
        self.assertTrue(node2.exists)
        self.assertEqual(node2.run_list, ['recipe[foo]'])

    def test_create_crosslink(self):
        node = Node.create(self.random())
        self.register(node)
        node.normal['foo'] = 'bar'
        self.assertEqual(node['foo'], 'bar')
        node.attributes['foo'] = 'baz'
        self.assertEqual(node.normal['foo'], 'baz')
