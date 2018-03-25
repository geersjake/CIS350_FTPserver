"""Encryption and decryption handling for all data sent/received.
:Authors:
    Jake Geers
    Chris van Zomeren
    Noah Verdeyen
    Colton

:Date: 2018-03-07

:Version: 1.5
"""
import rncryptor  # https://github.com/RNCryptor/RNCryptor-python


class EncryptError(Exception):
    """Raised when anything goes wrong with encryption process"""


class DecryptError(Exception):
    """Raised when anything goes wrong with decryption process"""


class Encryption:
    """Class that implements cryptographic Password Based Key
    Derivation Function 2 as used in RNCryptor. Function utilizes
    a key to encrypt data + salt.The key is then used for decryption.
    """

    def __init__(self, data, password):
        """Initialize an instance of Encryption
        :param data: The data to encrypt or decrypt
        :type data: str

        :param password: The password key to encrypt or decrypt data
        :type password: str
        """
        self._data = data
        self._password = password

    def encrypt(self):
        """Encrypt the data using PBKDF2 + salt function.

        :return: The encrypted data
        :rtype: hash
        """
        if not isinstance(self.data, str) or not isinstance(self.password, str):
            raise EncryptError("Error: Encrypt param must be string")  # TODO: handle

        cryptor = rncryptor.RNCryptor()
        encrypted_data = cryptor.encrypt(self.data, self.password)
        self.data = encrypted_data

        return self.data

    def decrypt(self):
        """Decrypt the hashed data using password

        :return: The decrypted data
        :rtype: str
        """
        if not isinstance(self.password, str):
            raise DecryptError("Error: Decrypt password must be string")  # TODO: handle

        cryptor = rncryptor.RNCryptor()
        decrypted_data = cryptor.decrypt(self.data, self._password)
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


############ temp testing #################


msg = ""
passkey = ""
enc = Encryption(msg, passkey)
e_data = enc.encrypt()
print(e_data)
d_data = enc.decrypt()
print(d_data)
