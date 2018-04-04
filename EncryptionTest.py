"""Encryption and decryption unit testing.
:Authors:
    Jake Geers
    Chris van Zomeren
    Noah Verdeyen
    Colton
:Date: 2018-04-01
:Version: 2.0
"""
import unittest

from encryption import PasswordError
from encryption import DataError
from encryption import Encryption


class TestPasswordMethods(unittest.TestCase):
    """Testing class to test all password related actions
    """
    def setUp(self):
        self.enc = Encryption("defaultD", "defaultP")
        self.passError = PasswordError

    def test_get(self):
        self.assertEqual(self.enc.password, "defaultP")

    def test_set(self):
        self.enc.password = "set1"
        self.assertEqual(self.enc.password, "set1")

    def test_password_error0(self):
        self.assertRaises(self.passError, Encryption, "temp", None)

    def test_password_error1(self):
        self.assertRaises(self.passError, Encryption, "temp", 123)

    def test_password_error2(self):
        arr = [3]
        self.assertRaises(self.passError, Encryption, "temp", arr)


class TestDataMethods(unittest.TestCase):
    """Testing class to test all data related actions
    """

    def setUp(self):
        self.enc = Encryption("defaultD", "defaultP")
        self.dataError = DataError

    def test_get(self):
        self.assertEqual(self.enc.data, "defaultD")

    def test_set(self):
        self.enc.data = "set2"
        self.assertEqual(self.enc.data, "set2")

    def test_data_error0(self):
        self.assertRaises(self.dataError, Encryption, None, "temp")

    def test_data_error1(self):
        self.assertRaises(self.dataError, Encryption, 1234, "temp")

    def test_data_error2(self):
        arr = [4]
        self.assertRaises(self.dataError, Encryption, arr, "temp")


class TestEncryptMethod(unittest.TestCase):
    """Testing class to test all encryption related actions
    """

    def setUp(self):
        self.enc = Encryption("defaultD", "defaultP")

    def test_encrypt0(self):
        self.enc.encrypt()
        d_data = self.enc.decrypt()
        self.assertEqual(self.enc.data, d_data)

    def test_encrypt1(self):
        self.enc.data = "HELLO RED BULL ALL DAY IPA"
        self.enc.password = "fee fi fo"
        hash1 = self.enc.encrypt()




class TestDecryptMethod(unittest.TestCase):
    """Testing class to test all encryption related actions
    """

    def setUp(self):
        self.enc = Encryption("defaultD", "defaultP")

    # def tearDown(self): # something here?

    def test_decrypt(self):
        self.enc.encrypt()
        d_data = self.enc.decrypt()
        self.assertEqual(self.enc.data, d_data)
