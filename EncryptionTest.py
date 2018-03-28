import unittest

from Encryption import EncryptError
from Encryption import Encryption


class TestPasswordMethods(unittest.TestCase):
    def setUp(self):
        self.enc = Encryption("defaultD", "defaultP")
        self.passError = EncryptError  # best way to test exception?

    # def tearDown(self): #  something here?

    def test_get(self):
        self.assertEqual(self.enc.password, "defaultP")

    def test_set(self):
        self.enc.password = "set1"
        self.assertEqual(self.enc.password, "set1")
