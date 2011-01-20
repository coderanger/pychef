from chef import Role
from chef.exceptions import ChefError
from chef.tests import ChefTestCase

class RoleTestCase(ChefTestCase):
    def test_get(self):
        r = Role('test_1')
        self.assertEqual(r.description, 'Static test role 1')
        self.assertEqual(r.run_list, [])

    def test_create(self):
        name = self.random()
        r = Role.create(name, description='A test role', run_list=['recipe[foo]'])
        self.register(r)
        self.assertEqual(r.description, 'A test role')
        self.assertEqual(r.run_list, ['recipe[foo]'])
        self.assertFalse(getattr(r, '_populated', False))

        r2 = Role(name)
        self.assertEqual(r2.description, 'A test role')
        self.assertEqual(r2.run_list, ['recipe[foo]'])
    
    def test_delete(self):
        name = self.random()
        r = Role.create(name)
        r.delete()
        for role in Role.list():
            self.assertNotEqual(role.name, name)
        with self.assertRaises(ChefError):
            Role(name, lazy=False)
        