# pylint: disable = missing-docstring, missing-return-doc, missing-return-type-doc
# pylint: disable = invalid-name
# pylint: disable = no-self-use
# pylint: disable = protected-access

import struct
from pathlib import Path

import pytest
from file_info import FileInfo

# v this could be a wildcard if pylint didn't complain
from ft_conn import FTProto, FTConn, FTSock, UnexpectedValueError

from .ft_mock import MockFTSock



correct_handshake = b'FTProtoW'
correct_hs_resp = correct_handshake[::-1]

wrong_handshake = b'lolwut??'   # Wrong handshake
wrong_hs_resp = b'response'     # Wrong response to correct handshake
wrong_hs_c_resp = b'??tuwlol'   # Correct response to wrong handshake

correct_version =  1
wrong_version = 0

test_file_name = 'test.txt'
test_file_contents = b'Hello, World!'



def file_info_equals(a, b):
    pe = a.path == b.path
    he = a.hash == b.hash
    de = a.is_dir == b.is_dir
    te = a.mtime == b.mtime
    return pe and he and de and te

def pi(num):
    return struct.pack('!i', num)

def pr(rstr):
    return struct.pack('!i{}s'.format(len(rstr)), len(rstr), rstr)


class TestFTConn:
    def test_connect_fail(self):
        # Server
        c = FTConn(MockFTSock())
        c.fts.crv = (False, "Server", "Failure")
        assert c.connect(0, 0) == "Failure"

        # Client
        c = FTConn(MockFTSock())
        c.fts.crv = (False, "Client", "Failure")
        assert c.connect(0, 0) == "Failure"

    def test_connect_hs_s_s(self):
        # Testing string mismatch
        c = FTConn(MockFTSock())
        c.fts.sock.append_bytes(wrong_handshake)
        c.fts.sock.append_bytes(pi(correct_version))

        assert c.connect(0, 0) == "Handshake failed"

        # Should have sent out correct handshake anyway
        assert c.fts.sock.check_bytes(wrong_hs_c_resp)
        assert c.fts.sock.check_bytes(pi(correct_version))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_connect_hs_s_v(self):
        # Testing version mismatch
        c = FTConn(MockFTSock())
        c.fts.sock.append_bytes(correct_handshake)
        c.fts.sock.append_bytes(pi(wrong_version))

        assert c.connect(0, 0) == "Handshake failed"

        # Checking *sent* handshake
        assert c.fts.sock.check_bytes(correct_hs_resp)
        assert c.fts.sock.check_bytes(pi(correct_version))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_connect_hs_s_c(self):
        # Testing successful handshake
        c = FTConn(MockFTSock())
        c.fts.sock.append_bytes(correct_handshake)
        c.fts.sock.append_bytes(pi(correct_version))

        assert c.connect(0, 0) == "Success"

        # Checking sent handshake
        assert c.fts.sock.check_bytes(correct_hs_resp)
        assert c.fts.sock.check_bytes(pi(correct_version))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()
        assert c.fts.sock.connected

    def test_connect_hs_c_s(self):
        # Testing string mismatch
        c = FTConn(MockFTSock())

        c.fts.crv = (True, "Client", "Success")

        # Because of the way we handshake, we need to set the
        # response before the socket sends the initiation
        c.fts.sock.append_bytes(wrong_handshake)
        c.fts.sock.append_bytes(pi(correct_version))

        assert c.connect(0, 0) == "Handshake failed"

        # Check sent handhsake initiation
        assert c.fts.sock.check_bytes(correct_handshake)
        assert c.fts.sock.check_bytes(pi(correct_version))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_connect_hs_c_v(self):
        # Testing version mismatch
        c = FTConn(MockFTSock())

        c.fts.crv = (True, "Client", "Success")

        # Because of the way we handshake, we need to set the
        # response before the socket sends the initiation
        c.fts.sock.append_bytes(correct_hs_resp)
        c.fts.sock.append_bytes(pi(wrong_version))

        assert c.connect(0, 0) == "Handshake failed"

        # Check sent handhsake initiation
        assert c.fts.sock.check_bytes(correct_handshake)
        assert c.fts.sock.check_bytes(pi(correct_version))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_connect_hs_c_c(self):
        # Testing successful handshake
        c = FTConn(MockFTSock())

        c.fts.crv = (True, "Client", "Success")

        # Because of the way we handshake, we need to set the
        # response before the socket sends the initiation
        c.fts.sock.append_bytes(correct_hs_resp)
        c.fts.sock.append_bytes(pi(correct_version))

        assert c.connect(0, 0) == "Success"

        # Check sent handhsake initiation
        assert c.fts.sock.check_bytes(correct_handshake)
        assert c.fts.sock.check_bytes(pi(correct_version))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_cfr_none(self):
        # Testing check_for_request with no request
        c = FTConn(MockFTSock(True))

        assert c.check_for_request() == (FTProto.REQ_NONE, None)
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_cfr_file(self):
        c = FTConn(MockFTSock(True))

        c.fts.sock.append_bytes(FTProto.REQ_FILE.value)

        c.fts.sock.append_bytes(pr(test_file_name.encode()))

        assert c.check_for_request() == (FTProto.REQ_FILE, test_file_name)
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_cfr_list(self):
        c = FTConn(MockFTSock(True))

        c.fts.sock.append_bytes(FTProto.REQ_LIST.value)

        assert c.check_for_request() == (FTProto.REQ_LIST, None)
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_send_file(self):
        c = FTConn(MockFTSock(True))

        c.send_file(test_file_contents)

        assert c.fts.sock.check_bytes(FTProto.RES_FILE.value)
        assert c.fts.sock.check_bytes(pr(test_file_contents))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_request_file_c(self):
        # Test correct receiving file
        c = FTConn(MockFTSock(True))

        c.fts.sock.append_bytes(FTProto.RES_FILE.value)
        c.fts.sock.append_bytes(pr(test_file_contents))

        assert c.request_file(test_file_name) == test_file_contents

        assert c.fts.sock.check_bytes(FTProto.REQ_FILE.value)
        assert c.fts.sock.check_bytes(pr(test_file_name.encode()))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_request_file_i(self):
        # Test invalid response
        c = FTConn(MockFTSock(True))

        c.fts.sock.append_bytes(FTProto.TINVALID.value) # wrong (invalid) response

        with pytest.raises(UnexpectedValueError) as err:
            c.request_file(test_file_name)

        assert err.value.state == str((FTProto.RES_FILE,))
        assert err.value.value == str(FTProto.TINVALID.value)
        assert c.fts.sock.check_bytes(FTProto.REQ_FILE.value)
        assert c.fts.sock.check_bytes(pr(test_file_name.encode()))
        assert c.fts.sock.ensure_esend()

    def test_request_file_n(self):
        # Test no response to request
        c = FTConn(MockFTSock(True))

        with pytest.raises(UnexpectedValueError) as err:
            c.request_file(test_file_name)

        assert err.value.state == str((FTProto.RES_FILE,))
        assert err.value.value == str(FTProto.REQ_NONE.value)
        assert c.fts.sock.check_bytes(FTProto.REQ_FILE.value)
        assert c.fts.sock.check_bytes(pr(test_file_name.encode()))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()


    def test_sr_file_list(self):
        # Generate fake file list
        fileList = []

        for i in range(20):
            fake_hash = str(i%10).encode() * (i % 32) + (b'0' * (32-i))
            f_id = i % 6 == 5
            item = FileInfo(path=Path().resolve(), file_hash = fake_hash, is_dir = f_id, mtime = i)
            fileList.append(item)

        # Test only the token exchange
        c = FTConn(MockFTSock(True))

        c.send_file_list(fileList)

        assert c.fts.sock.check_bytes(FTProto.RES_LIST.value)
        # Make sure it read all (nothing) but still sent stuff (the list)
        assert c.fts.sock.ensure_erecv() and not c.fts.sock.ensure_esend()


        # Test exchange by using two fake sockets (no requests)
        c1 = FTConn(MockFTSock(True))

        c2 = FTConn(MockFTSock(True))

        c1.send_file_list(fileList)
        c2.fts.sock.append_bytes(c1.fts.sock.retrieve_bytes())
        rfl = c2.request_file_list()

        assert c2.fts.sock.check_bytes(FTProto.REQ_LIST.value)

        # Make sure the response is the same list
        assert len(rfl) == 20

        for i in range(20):
            assert file_info_equals(rfl[i], fileList[i])

        assert c1.fts.sock.ensure_esend() and c1.fts.sock.ensure_erecv()
        assert c2.fts.sock.ensure_esend() and c2.fts.sock.ensure_erecv()

    def test_ftsock_gen(self):
        # Testing the default contructor for FTConn
        c = FTConn()
        assert isinstance(c.fts, FTSock)
