# pylint: disable = missing-docstring, missing-return-doc, missing-return-type-doc
# pylint: disable = invalid-name
# pylint: disable = no-self-use
# pylint: disable = protected-access

import struct
from socket import timeout
from pathlib import Path
import pytest
from file_info import FileInfo


# v this could be a wildcard if pylint didn't complain
from ft_conn import FTProto, FTConn, FTSock, BrokenSocketError, UnexpectedValueError

class MockSock():
    def __init__(self):
        self.__timeout = None

    def gettimeout(self):
        return self.__timeout

    def settimeout(self, ntimeout):
        self.__timeout = ntimeout

class MockFTSock(FTSock):
    def __init__(self):
        super().__init__(MockSock())

        self.connected = False

        self.__crv = (True, "Server", "Success")

        self.__rbytes = b''

        self.__sbytes = b''

        self.break_on_send = False
        self.break_on_recv = False

    # MockSock ensures that the timeout stack business works
    # as intended.

    def append_bytes(self, br):
        self.__rbytes = self.__rbytes + br

    def check_bytes(self, br):
        if self.__sbytes.startswith(br):
            self.__sbytes = self.__sbytes[len(br):]
            return True

        print("Unexpected bytes:", br, self.__sbytes)

        return False

    def retrieve_bytes(self):
        b = self.__sbytes
        self.__sbytes = b''
        return b

    def ensure_esend(self):
        return len(self.__sbytes) == 0

    def ensure_erecv(self):
        return len(self.__rbytes) == 0

    def set_connect(self, s, m, st):
        self.__crv = (s, m, st)

    def connect(self, host, port):
        if self.__crv[1]:
            self.connected = True
        return self.__crv

    def recv_bytes(self, num):
        if not self.connected:
            # Imitate actual error
            raise OSError(107, 'Transport endpoint is not connected')

        if self.break_on_recv:
            raise BrokenSocketError()

        if len(self.__rbytes) >= num:
            b = self.__rbytes[:num]
            self.__rbytes = self.__rbytes[num:]
            return b
        else:
            raise timeout()

    def send_bytes(self, bstr):
        if not self.connected:
            # Imitate actual error
            raise OSError(107, 'Transport endpoint is not connected')

        if self.break_on_send:
            raise BrokenSocketError()

        self.__sbytes = self.__sbytes + bstr

def file_info_equals(a, b):
    pe = a.path == b.path
    he = a.hash == b.hash
    de = a.is_dir == b.is_dir
    te = a.mtime == b.mtime
    return pe and he and de and te

class TestFTConnLM:
    def __pi(self, num):
        return struct.pack('!i', num)

    def __pr(self, rstr):
        return struct.pack('!i{}s'.format(len(rstr)), len(rstr), rstr)

    def test_connect_fail(self):
        # Server
        c = FTConn(MockFTSock())
        c.fts.set_connect(False, "Server", "Failure")
        assert c.connect(0, 0) == "Failure"

        # Client
        c = FTConn(MockFTSock())
        c.fts.set_connect(False, "Client", "Failure")
        assert c.connect(0, 0) == "Failure"

    def test_connect_hs_s_s(self):
        # Testing string mismatch
        c = FTConn(MockFTSock())
        c.fts.append_bytes(b'lolwut??') # This can't be the actual string (8 char)
        c.fts.append_bytes(self.__pi(1))

        assert c.connect(0, 0) == "Handshake failed."

        # Should have sent out correct handshake anyway
        assert c.fts.check_bytes(b'??tuwlol')
        assert c.fts.check_bytes(self.__pi(1)) # This needs to be the correct version
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_connect_hs_s_v(self):
        # Testing version mismatch
        c = FTConn(MockFTSock())
        c.fts.append_bytes(b'FTProtoW') # This must be the actual string
        c.fts.append_bytes(self.__pi(0)) # This can't be the correct version

        assert c.connect(0, 0) == "Handshake failed."

        # Checking *sent* handshake
        assert c.fts.check_bytes(b'WotorPTF')
        assert c.fts.check_bytes(self.__pi(1)) # This needs to be the correct version
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_connect_hs_s_c(self):
        # Testing successful handshake
        c = FTConn(MockFTSock())
        c.fts.append_bytes(b'FTProtoW') # v these both need to be correct
        c.fts.append_bytes(self.__pi(1))

        assert c.connect(0, 0) == "Success"

        # Checking sent handshake
        assert c.fts.check_bytes(b'WotorPTF')
        assert c.fts.check_bytes(self.__pi(1)) # This needs to be the correct version
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()
        assert c.fts.connected

    def test_connect_hs_c_s(self):
        # Testing string mismatch
        c = FTConn(MockFTSock())

        c.fts.set_connect(True, "Client", "Success")

        # Because of the way we handshake, we need to set the
        # response before the socket sends the initiation
        c.fts.append_bytes(b'lolwut??') # Needs to be incorrect response
        c.fts.append_bytes(self.__pi(1))

        assert c.connect(0, 0) == "Handshake failed."

        # Check sent handhsake initiation
        assert c.fts.check_bytes(b'FTProtoW')
        assert c.fts.check_bytes(self.__pi(1))
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_connect_hs_c_v(self):
        # Testing version mismatch
        c = FTConn(MockFTSock())

        c.fts.set_connect(True, "Client", "Success")

        # Because of the way we handshake, we need to set the
        # response before the socket sends the initiation
        c.fts.append_bytes(b'WotorPTF') # Needs to be correct response
        c.fts.append_bytes(self.__pi(0)) # Needs to be incorrect

        assert c.connect(0, 0) == "Handshake failed."

        # Check sent handhsake initiation
        assert c.fts.check_bytes(b'FTProtoW')
        assert c.fts.check_bytes(self.__pi(1))
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_connect_hs_c_c(self):
        # Testing successful handshake
        c = FTConn(MockFTSock())

        c.fts.set_connect(True, "Client", "Success")

        # Because of the way we handshake, we need to set the
        # response before the socket sends the initiation
        c.fts.append_bytes(b'WotorPTF') # Needs to be correct response
        c.fts.append_bytes(self.__pi(1)) # Needs to be correct

        assert c.connect(0, 0) == "Success"

        # Check sent handhsake initiation
        assert c.fts.check_bytes(b'FTProtoW')
        assert c.fts.check_bytes(self.__pi(1))
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_cfr_none(self):
        # Testing check_for_request with no request
        c = FTConn(MockFTSock())
        c.fts.connected = True

        assert c.check_for_request() == (FTProto.REQ_NONE, None)
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_cfr_file(self):
        c = FTConn(MockFTSock())
        c.fts.connected = True

        c.fts.append_bytes(FTProto.REQ_FILE.value)

        c.fts.append_bytes(self.__pr(b'test.txt'))

        assert c.check_for_request() == (FTProto.REQ_FILE, 'test.txt')
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_cfr_list(self):
        c = FTConn(MockFTSock())
        c.fts.connected = True

        c.fts.append_bytes(FTProto.REQ_LIST.value)

        assert c.check_for_request() == (FTProto.REQ_LIST, None)
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_send_file(self):
        c = FTConn(MockFTSock())
        c.fts.connected = True

        tfc = b'Test file contents'

        c.send_file(tfc)

        assert c.fts.check_bytes(FTProto.RES_FILE.value)
        assert c.fts.check_bytes(self.__pr(tfc))
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_request_file_c(self):
        # Test correct receiving file
        c = FTConn(MockFTSock())
        c.fts.connected = True

        tfc = b'Test file contents'

        c.fts.append_bytes(FTProto.RES_FILE.value)
        c.fts.append_bytes(self.__pr(tfc))

        assert c.request_file('Test.txt') == tfc

        assert c.fts.check_bytes(FTProto.REQ_FILE.value)
        assert c.fts.check_bytes(self.__pr(b'Test.txt'))
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_request_file_i(self):
        # Test invalid response
        c = FTConn(MockFTSock())
        c.fts.connected = True

        c.fts.append_bytes(b'n') # wrong (invalid) response

        with pytest.raises(UnexpectedValueError) as err:
            c.request_file('Test.txt')

        assert err.value.state == str((FTProto.RES_FILE,))
        assert err.value.value == str(b'Invalid')
        assert c.fts.check_bytes(FTProto.REQ_FILE.value)
        assert c.fts.check_bytes(self.__pr(b'Test.txt'))
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()

    def test_request_file_n(self):
        # Test no response to request
        c = FTConn(MockFTSock())
        c.fts.connected = True

        with pytest.raises(UnexpectedValueError) as err:
            c.request_file('Test.txt')

        assert err.value.state == str((FTProto.RES_FILE,))
        assert err.value.value == str(b'None')
        assert c.fts.check_bytes(FTProto.REQ_FILE.value)
        assert c.fts.check_bytes(self.__pr(b'Test.txt'))
        assert c.fts.ensure_esend() and c.fts.ensure_erecv()


    def test_sr_file_list(self):
        # Generate fake file list
        fileList = []

        for i in range(20):
            fake_hash = str(i%10).encode() * (i % 32) + (b'0' * (32-i))
            f_id = i % 6 == 5
            item = FileInfo(path=Path().resolve(), file_hash = fake_hash, is_dir = f_id, mtime = i)
            fileList.append(item)

        # Test only the token exchange
        c = FTConn(MockFTSock())
        c.fts.connected = True

        c.send_file_list(fileList)

        assert c.fts.check_bytes(FTProto.RES_LIST.value)
        # Make sure it read all (nothing) but still sent stuff (the list)
        assert c.fts.ensure_erecv() and not c.fts.ensure_esend()


        # Test exchange by using two fake sockets (no requests)
        c1 = FTConn(MockFTSock())
        c1.fts.connected = True

        c2 = FTConn(MockFTSock())
        c2.fts.connected = True

        c1.send_file_list(fileList)
        c2.fts.append_bytes(c1.fts.retrieve_bytes())
        rfl = c2.request_file_list()

        assert c2.fts.check_bytes(FTProto.REQ_LIST.value)

        # Make sure the response is the same list
        assert len(rfl) == 20

        for i in range(20):
            assert file_info_equals(rfl[i], fileList[i])

        assert c1.fts.ensure_esend() and c1.fts.ensure_erecv()
        assert c2.fts.ensure_esend() and c2.fts.ensure_erecv()

    def test_ftsock_gen(self):
        # Testing the default contructor for FTConn
        c = FTConn()
        assert isinstance(c.fts, FTSock)
