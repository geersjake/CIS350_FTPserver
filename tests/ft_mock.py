# pylint: disable = missing-docstring, missing-return-doc, missing-return-type-doc
# pylint: disable = invalid-name
# pylint: disable = no-self-use
# pylint: disable = protected-access

from socket import timeout
from ft_conn import FTSock

class MockSock():
    def __init__(self, con=False):
        self.connected = con

        self.rbuf = b''
        self.sbuf = b''
        self.raise_on_end_recv = timeout()
        self.pshutdown = False

        self.raise_on_send = None

        self.__timeout = None

    def gettimeout(self):
        return self.__timeout

    def settimeout(self, ntimeout):
        self.__timeout = ntimeout

    def setsockopt(self, a, b, c):
        pass

    def recv(self, num):
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
        self.rbuf = self.rbuf + br

    def check_bytes(self, br):
        if self.sbuf.startswith(br):
            self.sbuf = self.sbuf[len(br):]
            return True

        return False

    def retrieve_bytes(self, clear=True):
        br = self.sbuf
        if clear:
            self.sbuf = b''
        return br

    def ensure_esend(self):
        return len(self.sbuf) == 0

    def ensure_erecv(self):
        return len(self.rbuf) == 0


class MockFTSock(FTSock):
    def __init__(self, con=False):
        super().__init__(False, MockSock(con))

        self.connected = False

        self.crv = (True, "Server", "Success")

    def connect(self, host, port):
        if self.crv[1]:
            self.sock.connected = True
        return self.crv
