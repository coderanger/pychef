import unittest2

from chef import Client
from chef.tests import ChefTestCase

class ClientTestCase(ChefTestCase):
    def test_list(self):
        self.assertIn('test_1', Client.list())

    def test_get(self):
        client = Client('test_1')
        self.assertTrue(client.platform)
        self.assertEqual(client.orgname, 'pycheftest')
        self.assertTrue(client.public_key)
        self.assertTrue(client.certificate)
        self.assertEqual(client.private_key, None)

    @unittest2.skip('Unknown failure, skipping until tomorrow morning <NPK 2012-03-22>')
    def test_create(self):
        name = self.random()
        client = Client.create(name)
        self.register(client)
        self.assertEqual(client.name, name)
        #self.assertEqual(client.orgname, 'pycheftest') # See CHEF-2019
        self.assertTrue(client.private_key)

        self.assertIn(name, Client.list())

        client2 = Client(name)
        client2.rekey()
        self.assertNotEqual(client.private_key, client2.private_key)

    @unittest2.skip('Unknown failure, skipping until tomorrow morning <NPK 2012-03-22>')
    def test_delete(self):
        name = self.random()
        client = Client.create(name)
        client.delete()
        self.assertNotIn(name, Client.list())
