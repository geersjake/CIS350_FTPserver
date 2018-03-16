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
        self.data = encrypted_data
        return self.data

    def decrypt(self):
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


msg = "hello"
passkey = "jimmy"
enc = Encryption(msg, passkey)
e_data = enc.encrypt()
print(e_data)
d_data = enc.decrypt()
print(d_data)
