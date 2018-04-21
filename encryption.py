"""Encryption and decryption handling for all data sent/received.
:Authors:
    Jake Geers
    Chris van Zomeren
    Noah Verdeyen
    Colton
:Date: 2018-04-01
:Version: 2.0
"""
import rncryptor  # https://github.com/RNCryptor/RNCryptor-python


class PasswordError(Exception):
    """Raised when password is improper or invalid"""


class DataError(Exception):
    """Raised when data is improper or invalid"""


class Encryption:
    """Class that implements cryptographic Password Based Key
    Derivation Function 2 as used in RNCryptor. Function utilizes
    a key to encrypt data + salt.The key is then used for decryption.
    """

    # TODO: where to say function raises my exceptions?
    def __init__(self, data, password):
        """Initialize an instance of Encryption
        :param data: The data to encrypt or decrypt
        :type data: bytes
        :param password: The password key to encrypt or decrypt data
        :type password: str
        """
        if not isinstance(data, bytes):
            raise DataError("Error: Data param must be bytes")

        if not isinstance(password, str):
            raise PasswordError("Error: Password must be string")

        self._data = data
        self._password = password

    def encrypt(self):
        """Encrypt the data using PBKDF2 + salt function.
        :return: The encrypted data
        :rtype: bytes
        """
        cryptor = rncryptor.RNCryptor()
        encrypted_data = cryptor.encrypt(self.data, self.password)
        self.data = encrypted_data

        return self.data

    def decrypt(self):
        """Decrypt the hashed data using password
        :return: The decrypted data
        :rtype: bytes
        """
        cryptor = rncryptor.RNCryptor()
        decrypted_data = cryptor.decrypt(self.data, self.password).encode()
        self.data = decrypted_data

        return self.data

    @property
    def data(self):
        """Getter"""
        return self._data

    @data.setter
    def data(self, new_data):
        """Setter"""
        self._data = new_data

    @property
    def password(self):
        """Getter"""
        return self._password

    @password.setter
    def password(self, new_pass):
        """Setter"""
        self._password = new_pass


