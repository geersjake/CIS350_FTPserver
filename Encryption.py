"""Hashing - can be used to hash password to the server,
hashing the file names, or even the actions we send over the wire.

Jake Geers
2-25-2018

"""
import hashlib

password = 'adminguestpassword'
bytePassword = str.encode(password)  # md5 requires argument to be in byte code
md5 = hashlib.md5()  # could be any other sha or RSA md5

md5.update(bytePassword)  # Update the given report ID with all data from report
print(md5.digest())  # Return the digest value as a string of binary data.

sha256 = hashlib.sha256(bytePassword).hexdigest()
print(sha256)