import os

import unittest2

from chef.rsa import Key, SSLError
from chef.tests import TEST_ROOT

class RSATestCase(unittest2.TestCase):
    def setUp(self):
        self.key = Key(os.path.join(TEST_ROOT, 'client.pem'))
        self.pubkey = Key(os.path.join(TEST_ROOT, 'client_pub.pem'))

    def test_private_export(self):
        raw = open(os.path.join(TEST_ROOT, 'client.pem'), 'rb').read()
        self.assertTrue(self.key.private_export().strip(), raw.strip())

    def test_public_export(self):
        raw = open(os.path.join(TEST_ROOT, 'client_pub.pem'), 'rb').read()
        self.assertTrue(self.key.public_export().strip(), raw.strip())

    def test_private_export_pubkey(self):
        with self.assertRaises(SSLError):
            self.pubkey.private_export()

    def test_public_export_pubkey(self):
        raw = open(os.path.join(TEST_ROOT, 'client_pub.pem'), 'rb').read()
        self.assertTrue(self.pubkey.public_export().strip(), raw.strip())
