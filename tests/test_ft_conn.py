# pylint: disable = missing-docstring, missing-return-doc, missing-return-type-doc
# pylint: disable = invalid-name
# pylint: disable = no-self-use
# pylint: disable = protected-access

import struct
from pathlib import Path

import pytest
from file_info import FileInfo

from ft_conn import FTProto, FTConn
from ft_conn.ft_sock import FTSock
from ft_conn.ft_error import UnexpectedValueError

from .ft_mock import MockFTSock

# We need some data to test with:

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
    # There is no equality function for FileInfo, so we make a quick one
    pe = a.path == b.path
    he = a.hash == b.hash
    de = a.is_dir == b.is_dir
    te = a.mtime == b.mtime
    return pe and he and de and te

def pi(num):
    # Packs an integer (like the protocol does)
    return struct.pack('!i', num)

def pr(rstr):
    # Packs a raw string (like the protocol does)
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

    def tst_connect_hs_s_v(self):
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

        # Check sent handshake initiation
        assert c.fts.sock.check_bytes(correct_handshake)
        assert c.fts.sock.check_bytes(pi(correct_version))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def tst_connect_hs_c_v(self):
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

        # Check sent handshake initiation
        assert c.fts.sock.check_bytes(correct_handshake)
        assert c.fts.sock.check_bytes(pi(correct_version))
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_recv_req_l(self):
        # Testing receive list request
        c = FTConn(MockFTSock(True))

        c.fts.sock.append_bytes(FTProto.REQ_LIST)

        assert c.receive_data() == (FTProto.REQ_LIST, None)
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_recv_req_f(self):
        # Testing receive file request
        c = FTConn(MockFTSock(True))

        c.fts.sock.append_bytes(FTProto.REQ_FILE)
        c.fts.sock.append_bytes(pr(test_file_name.encode()))

        assert c.receive_data() == (FTProto.REQ_FILE, test_file_name)
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_send_req_l(self):
        # Testing sending a list request
        c = FTConn(MockFTSock(True))

        c.request_file_list()

        assert c.fts.sock.check_bytes(FTProto.REQ_LIST)
        assert c.fts.sock.ensure_esend() and c.fts.sock.ensure_erecv()

    def test_send_res_l(self):
        # Testing sending a file response
        c = FTConn(MockFTSock(True))

        c.send_file(test_file_name.encode(), test_file_contents)

        assert c.fts.sock.check_bytes(FTProto.RES_FILE)
        assert c.fts.sock.check_bytes(pr(test_file_name.encode()))
        assert c.fts.sock.check_bytes(pr(test_file_contents))
        assert c.fts.sock.ensure_erecv() and c.fts.sock.ensure_esend()

    def test_send_req_f(self):
        # Testing sending a file request
        c = FTConn(MockFTSock(True))

        c.request_file(test_file_name.encode())

        assert c.fts.sock.check_bytes(FTProto.REQ_FILE)
        assert c.fts.sock.check_bytes(pr(test_file_name.encode()))
        assert c.fts.sock.ensure_erecv() and c.fts.sock.ensure_esend()

    def test_recv_res_f(self):
        # Testing receiving a file response
        c = FTConn(MockFTSock(True))

        c.fts.sock.append_bytes(FTProto.RES_FILE)
        c.fts.sock.append_bytes(pr(test_file_name.encode()))
        c.fts.sock.append_bytes(pr(test_file_contents))

        assert c.receive_data() == (FTProto.RES_FILE, (test_file_name.encode(), test_file_contents))
        assert c.fts.sock.ensure_erecv() and c.fts.sock.ensure_esend()