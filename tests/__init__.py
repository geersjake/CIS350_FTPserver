# pylint: disable = missing-docstring

# Conglomeration of test classes. If all
# test classes are in the tests directory,
# and imported here, `pytest tests` will
# automatically run all of the automated
# tests.

from .test_ft_error import TestFTErrors
from .test_ft_conn import TestFTConn
from .test_ft_sock import TestFTSock
from .test_encryption import TestPasswordMethods, \
	TestDataMethods, TestEncryptMethod, \
	TestDecryptMethod, TestSecurity
from .test_file_info import TestLocalFileInfoBrowser
