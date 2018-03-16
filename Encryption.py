import rncryptor  # https://github.com/RNCryptor/RNCryptor-python


class Encryption:
    """
    Main class to handel byte encrypting as well as decrypting using RSA.
    Class creates two keys:
        Public Key - key sent over wire
        Private Key - key kept
    """

    def __init__(self, data, password):
        self._data = data
        self._password = password

    def encrypt(self):
        cryptor = rncryptor.RNCryptor()
        encrypted_data = cryptor.encrypt(self.data, self.password)
        return encrypted_data

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


msg = "hello"
passkey = "jimmy"
enc = Encryption(msg, passkey)
print(enc.encrypt())
