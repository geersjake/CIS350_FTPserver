# pylint: disable = missing-docstring, missing-return-doc, missing-return-type-doc
# pylint: disable = invalid-name
# pylint: disable = no-self-use
# pylint: disable = protected-access

import pytest
from ft_conn.ft_sock import FTSock
from ft_conn.ft_error import BrokenSocketError
from .ft_mock import MockSock

class TestFTSock:
    def test_recv_b(self):
        s = FTSock(False, MockSock(True))
        s.sock.pshutdown = True

        with pytest.raises(BrokenSocketError):
            s.recv_bytes(1)

    def test_send_b(self):
        s = FTSock(False, MockSock(True))
        s.sock.pshutdown = True

        with pytest.raises(BrokenSocketError):
            s.send_bytes(b'l')
