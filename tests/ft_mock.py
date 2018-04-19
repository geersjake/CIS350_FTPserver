# pylint: disable = missing-docstring, missing-return-doc, missing-return-type-doc
# pylint: disable = invalid-name
# pylint: disable = no-self-use
# pylint: disable = protected-access

# This file contains mock network devices to allow FTSock and FTConn to be tested
# locally (and without network connections).

from socket import timeout
from ft_conn.ft_sock import FTSock

class MockSock():
    def __init__(self, con=False):
        # Whether the socket is "connected" after init
        self.connected = con

        # Receive buffer (receives come from here)
        self.rbuf = b''

        # Send buffer (sends go here)
        self.sbuf = b''

        # Error to raise if we read from an empty buffer (usually timeout or
        # ft_conn.ft_error.BrokenSocketError)
        self.raise_on_end_recv = timeout()

        # Whether to simulate the other peer having closed their socket
        self.pshutdown = False

        # What error to raise when we try to send (None = don't raise anything and just send)
        self.raise_on_send = None

        # Does nothing but the code sets/gets this
        self.__timeout = None

    def gettimeout(self):
        return self.__timeout

    def settimeout(self, ntimeout):
        self.__timeout = ntimeout

    def setsockopt(self, a, b, c):
        # Does nothing but the code does call this (for setting test options)
        pass

    def recv(self, num):
        # Simulates socket.recv but gets data from the recv buffer

        if not self.connected:
            # Imitate actual error
            raise OSError(107, 'Transport endpoint is not connected')

        if self.pshutdown:
            return b''

        if num > len(self.rbuf) and self.raise_on_end_recv is not None:
            raise self.raise_on_end_recv

        br = self.rbuf[:num]
        self.rbuf = self.rbuf[num:]
        return br

    def send(self, br):
        # Simulates socket.send but sends data to the send buffer

        if not self.connected:
            # Imitate actual error
            raise OSError(107, 'Transport endpoint is not connected')

        if self.pshutdown:
            return 0

        if self.raise_on_send is not None:
                                            # pylint complains that we raise None,
                                            # even though we check to make sure we don't
            raise self.raise_on_send        # pylint: disable = raising-bad-type

        self.sbuf = self.sbuf + br

        return len(br)

    # END SOCKET EMULATION #

    # BEGIN TEST HELPERS #

    def append_bytes(self, br):
        # Add bytes for the socket to receive
        self.rbuf = self.rbuf + br

    def check_bytes(self, br):
        # Check that the socket sent the proper bytes
        if self.sbuf.startswith(br):
            self.sbuf = self.sbuf[len(br):]
            return True

        print(br, self.sbuf)

        return False

    def retrieve_bytes(self, clear=True):
        # Takes the whole send buffer (used for faking connections)
        br = self.sbuf
        if clear:
            self.sbuf = b''
        return br

    def ensure_esend(self):
        # Make sure the socket *only* sent what we checked
        return len(self.sbuf) == 0

    def ensure_erecv(self):
        # Make sure the socket read everything we put in the recv buffer
        return len(self.rbuf) == 0


class MockFTSock(FTSock):
    # MockSock does all of the hard stuff here, we just need to fake the connection
    def __init__(self, con=False):
        super().__init__(MockSock(con))

        # What connect returns (if the bool is True, the socket gets "connected")
        self.crv = (True, "Server", "Success")

    def connect(self, host, port):
        if self.crv[1]:
            self.sock.connected = True
        return self.crv